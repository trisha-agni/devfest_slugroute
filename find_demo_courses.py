import re
from slugroute.graph.engine import AcademicGraphEngine

engine = AcademicGraphEngine()
candidates = []


def course_num(c: str) -> int:
  m = re.search(r"\d+", c)
  return int(m.group()) if m else 0


for node in engine.G.nodes():
  if not node.startswith("CSE ") or course_num(node) >= 200:
    continue

  canonical_nodes = engine._resolve_minimal_prereqs(node, set(), major="CS_BS")
  can_count = len(canonical_nodes)

  # Target sweet spot: 3 to 7 nodes in the canonical CS track
  if 3 <= can_count <= 7:
    raw_sub = engine.get_prerequisite_subgraph(node)
    data = engine.get_course_data(node) or {}
    candidates.append({
      "code": node,
      "title": data.get("title", ""),
      "canonical_nodes": can_count,
      "raw_nodes": raw_sub.number_of_nodes(),
      "path": sorted(list(canonical_nodes)),
    })

candidates.sort(key=lambda x: (x["canonical_nodes"], x["raw_nodes"]))

print(f"{'Code':<10} | {'Nodes':<5} | {'Title':<35} | Prerequisite Chain")
print("-" * 85)
for c in candidates[:15]:
  print(f"{c['code']:<10} | {c['canonical_nodes']:<5} | {c['title'][:35]:<35} | {', '.join(c['path'])}")  # noqa
