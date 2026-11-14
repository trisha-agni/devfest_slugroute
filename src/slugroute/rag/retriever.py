# external imports
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import Any
import torch
import torch.nn.functional as F
# internal imports
from slugroute.config import INDEX_FILE, TOP_K_RETRIEVAL


class CourseRetriever:

  def __init__(
    self,
    index_path: Path | None = None,
    device: str | None = None,
  ):
    path = index_path or INDEX_FILE
    if not path.exists():
      raise FileNotFoundError(f"Vector index not found at {path}")

    # Auto-detect fastest device: CUDA > MPS > CPU
    self.device = device or (
      "cuda"
      if torch.cuda.is_available()
      else "mps"
      if torch.backends.mps.is_available()
      else "cpu"
    )

    # 1. Load precomputed index artifact
    data = torch.load(path, map_location=self.device, weights_only=False)
    self.courses: list[dict[str, Any]] = data["courses"]
    self.codes: list[str] = data["codes"]
    self.embeddings: torch.Tensor = data["embeddings"].to(self.device)
    self.model_name: str = data.get("model_name", "all-MiniLM-L6-v2")

    # Fast O(1) lookup map
    self.course_map: dict[str, dict[str, Any]] = {
      c["code"].upper(): c for c in self.courses
    }

    # 2. Load embedder for search queries
    self.model = SentenceTransformer(self.model_name, device=self.device)

  def get_course(self, course_code: str) -> dict[str, Any] | None:
    """O(1) exact metadata lookup by course code."""
    normalized = " ".join(course_code.strip().upper().split())
    return self.course_map.get(normalized)

  def search(
    self,
    query: str,
    top_k: int = TOP_K_RETRIEVAL,
    subject: str | None = None,
    gen_ed: str | None = None,
  ) -> list[dict[str, Any]]:
    """Sub-millisecond cosine similarity search over UCSC catalog."""
    # Encode and L2-normalize query vector
    query_emb_np = self.model.encode(query, convert_to_numpy=True)
    query_tensor = torch.tensor(
      query_emb_np, dtype=torch.float32, device=self.device
    )
    query_tensor = F.normalize(query_tensor, p=2, dim=0)

    # Cosine similarity via dot-product: (N, D) @ (D,) -> (N,)
    scores = torch.mv(self.embeddings, query_tensor)

    # Optional pre-filtering by Subject or GE code
    if subject or gen_ed:
      mask = torch.ones(len(self.courses), dtype=torch.bool, device=self.device)
      for i, c in enumerate(self.courses):
        c_sub = (c.get("subject") or "").upper()
        c_ge = (c.get("gen_ed") or "").upper()
        if subject and c_sub != subject.upper():
          mask[i] = False
        if gen_ed and c_ge != gen_ed.upper():
          mask[i] = False
      scores[~mask] = -1.0

    top_scores, top_indices = torch.topk(scores, k=min(top_k, len(self.courses)))

    results = []
    for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
      if score < 0.0:  # Filtered out
        continue
      course_info = dict(self.courses[idx])
      course_info["similarity_score"] = round(float(score), 4)
      results.append(course_info)

    return results
