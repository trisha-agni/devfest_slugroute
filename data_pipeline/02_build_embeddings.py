# external imports
from sentence_transformers import SentenceTransformer
import json
import torch
import torch.nn.functional as F
# internal imports
from slugroute.config import (
  COURSE_DATA_FILE,
  COURSE_DATA_ENCODING,
  EMBEDDING_MODEL_NAME,
  INDEX_FILE,
)

BATCH_SZ = 64


def course_to_text(c: dict) -> str:
  ge_part = f" | GE: {c['gen_ed']}" if c.get("gen_ed") else ""
  credits_part = f" ({c['credits']} credits)" if c.get("credits") else ""
  prereq_part = f"\nPrerequisites: {c['prereq_raw']}" if c.get("prereq_raw") else ""

  return (
    f"Course: {c['code']} - {c['title']}{credits_part}{ge_part}\n"
    f"Description: {c.get('desc', '')}{prereq_part}"
  ).strip()


def run_pipeline():
  if not COURSE_DATA_FILE.exists():
    raise FileNotFoundError(f"missing input: {COURSE_DATA_FILE}. run scraper first.")

  print(f"loading raw courses from {COURSE_DATA_FILE}...")
  courses = []
  with open(COURSE_DATA_FILE, "r", encoding=COURSE_DATA_ENCODING) as f:
    for line in f:
      if line.strip():
        courses.append(json.loads(line))

  print(f"preparing texts for {len(courses)} courses...")
  texts = [course_to_text(c) for c in courses]
  codes = [c["code"] for c in courses]

  # hardware acceleration: CUDA > MPS (Apple Silicon) > CPU
  device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
  )
  print(f"loading '{EMBEDDING_MODEL_NAME}' on {device.upper()}...")
  model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

  print("computing embeddings in batches...")
  embeddings_np = model.encode(
    texts,
    batch_size=BATCH_SZ,
    show_progress_bar=True,
    convert_to_numpy=True,
  )

  # convert to PyTorch and L2-normalize for blazing fast cosine similarity (dot-product)
  embeddings_tensor = torch.tensor(embeddings_np, dtype=torch.float32)
  normalized_embeddings = F.normalize(embeddings_tensor, p=2, dim=1)

  payload = {
    "codes": codes,
    "courses": courses,
    "texts": texts,
    "embeddings": normalized_embeddings,
    "model_name": EMBEDDING_MODEL_NAME,
  }

  print(f"saving indexed vector store to {INDEX_FILE}...")
  torch.save(payload, INDEX_FILE)
  print(f"done! index size: {INDEX_FILE.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
  run_pipeline()
