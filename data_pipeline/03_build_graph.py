# external imports
from networkx.readwrite import json_graph
import json
import re
import networkx as nx
# internal imports
from slugroute.config import (
  COURSE_DATA_FILE,
  COURSE_DATA_ENCODING,
  GRAPH_FILE,
)

COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,5}(?:\s+[A-Z]{2,4})?\s+\d+[A-Z]?)\b")
STRIP_PREFIX_RE = re.compile(
  r"^(?:Prerequisite\(s\):|Prerequisites?:)\s*",
  re.IGNORECASE,
)
EXCLUSION_RE = re.compile(
  r"\b(cannot enroll|may not enroll|should not take|not open to|cannot receive credit)\b",  # noqa
  re.IGNORECASE,
)


def _parse_cnf_clause(clause_text: str, valid_codes: set[str]) -> list[list[str]]:
  """Parse a single track string into CNF requirement groups."""
  clauses = re.split(r"[;\.]", clause_text)
  groups: list[list[str]] = []

  for clause in clauses:
    # Skip anti-prerequisite exclusion sentences
    if EXCLUSION_RE.search(clause):
      continue
    sub_clauses = re.split(r"\band\b", clause, flags=re.IGNORECASE)
    for sub in sub_clauses:
      found = COURSE_CODE_RE.findall(sub)
      matched = [" ".join(c.split()) for c in found if c in valid_codes]
      if matched:
        unique_group = list(dict.fromkeys(matched))
        if unique_group not in groups:
          groups.append(unique_group)
  return groups


def extract_prereq_tracks(
  raw_text: str,
  valid_codes: set[str],
) -> list[list[list[str]]]:
  """Parse text into DNF of CNFs: [Track1, Track2, ...]

  Each Track is a CNF: [[Alt1, Alt2], [Req2]]
  """
  if not raw_text:
    return []

  # Only inspect text AFTER 'Prerequisite(s):' to ignore leading exclusions
  prereq_match = re.search(
    r"(?:Prerequisite\(s\):|Prerequisites?:)\s*(.*)",
    raw_text,
    re.IGNORECASE,
  )
  if prereq_match:
    text = prereq_match.group(1).strip()
  else:
    text = raw_text.strip()
  cutoff = re.search(
    r"\b(Enrollment is restricted|Students cannot receive|Open to)\b",
    text,
    re.IGNORECASE,
  )
  if cutoff:
    text = text[: cutoff.start()].strip()

  # Semicolon followed by 'or' indicates independent alternative tracks (DNF)
  track_strings = re.split(r";\s*or\b", text, flags=re.IGNORECASE)
  tracks: list[list[list[str]]] = []

  for t_str in track_strings:
    cnf = _parse_cnf_clause(t_str, valid_codes)
    if cnf:
      tracks.append(cnf)

  return tracks


def run_pipeline():
  if not COURSE_DATA_FILE.exists():
    raise FileNotFoundError(f"Missing input: {COURSE_DATA_FILE}")

  print(f"loading courses from {COURSE_DATA_FILE}...")
  courses = []
  with open(COURSE_DATA_FILE, "r", encoding=COURSE_DATA_ENCODING) as f:
    for line in f:
      if line.strip():
        courses.append(json.loads(line))

  valid_codes = {c["code"] for c in courses}
  course_map = {c["code"]: c for c in courses}
  print(f"catalog contains {len(valid_codes)} verified course codes.")

  G = nx.DiGraph()

  # 1. add all courses as graph nodes
  for c in courses:
    G.add_node(
      c["code"],
      title=c.get("title", ""),
      subject=c.get("subject", ""),
      number=c.get("number", ""),
      credits=c.get("credits"),
      gen_ed=c.get("gen_ed"),
      url=c.get("url", ""),
    )

  # 2. parse prerequisite edges (edge direction: Prerequisite -> Target Course)
  total_with_prereqs = 0
  for code, c in course_map.items():
    raw = c.get("prereq_raw", "")
    tracks = extract_prereq_tracks(raw, valid_codes)

    # store multi-track representation
    G.nodes[code]["prereq_groups"] = tracks

    if tracks:
      total_with_prereqs += 1
      for track in tracks:
        for group in track:
          for prereq in group:
            if prereq != code:
              G.add_edge(prereq, code)

  print("\n--- graph statistics ---")
  print(f"total nodes: {G.number_of_nodes()}")
  print(f"total directed dependency edges: {G.number_of_edges()}")
  print(f"courses with structured prerequisites: {total_with_prereqs}")

  # check for cyclic dependencies in catalog
  cycles = list(nx.recursive_simple_cycles(G)) \
    if hasattr(nx, "recursive_simple_cycles") else []
  if cycles:
    print(f"warning: found {len(cycles)} circular dependencies in raw data (e.g. labs).")

  def course_level(code: str) -> int:
    m = re.search(r"\d+", code)
    return int(m.group()) if m else 0

  # break 2-node cycles (co-requisites like CSE 100 <-> CSE 100L)
  two_cycles = [
    (u, v) for u, v in G.edges() if G.has_edge(v, u) and u != v
  ]
  for u, v in two_cycles:
    if G.has_edge(u, v) and G.has_edge(v, u):
      lvl_u, lvl_v = course_level(u), course_level(v)
      # If u is lower level than v, keep u -> v and delete v -> u
      if lvl_u < lvl_v:
        G.remove_edge(v, u)
      elif lvl_v < lvl_u:
        G.remove_edge(u, v)
      else:
        # Same level (e.g. CSE 100 lecture vs CSE 100L lab): keep lecture -> lab
        if "L" in u and "L" not in v:
          G.remove_edge(u, v)
        else:
          G.remove_edge(v, u)

  # check remaining cycles (if any)
  try:
    cycles = list(nx.simple_cycles(G))
    if cycles:
      print(f"breaking {len(cycles)} remaining complex cycles...")
      for cycle in cycles:
        if G.has_edge(cycle[-1], cycle[0]):
          G.remove_edge(cycle[-1], cycle[0])
  except Exception:
    pass

  print(f"is strict DAG: {nx.is_directed_acyclic_graph(G)}")

  # 3. export to JSON (node-link format)
  graph_data = json_graph.node_link_data(G)
  with open(GRAPH_FILE, "w", encoding=COURSE_DATA_ENCODING) as f:
    json.dump(graph_data, f, ensure_ascii=False, indent=2)

  print(f"saved networkX prerequisite graph to {GRAPH_FILE}")


if __name__ == "__main__":
  run_pipeline()
