import sys
import networkx as nx
from slugroute.graph.engine import AcademicGraphEngine

engine = AcademicGraphEngine()
failures = 0


def run_test(name: str, passed: bool, details: str = ""):
  global failures
  if passed:
    print(f"✅ [PASS] {name}")
  else:
    print(f"❌ [FAIL] {name}\n   Details: {details}")
    failures += 1


print("========================================")
print(" Academic Graph Regression Test Suite   ")
print("========================================")

# 1. Strict DAG Check (Must never contain cycles)
is_dag = nx.is_directed_acyclic_graph(engine.G)
run_test("Graph is strictly acyclic (DAG)", is_dag)

# 2. CSE 101 CNF Evaluation
can_take, missing = engine.check_eligibility(
  "CSE 101", {"CSE 12", "CSE 13S", "CSE 16", "CSE 30", "MATH 19B"}
)
run_test(
  "CSE 101 satisfies with canonical CS lower-divs",
  can_take,
  f"Missing groups: {missing}",
)

# 3. CSE 111 Alternative Track Check (DNF Bug Test)
# CSE 111 should be satisfied with ONLY CSE 101 (or CSE 13S + CMPM 35)
can_take_111, missing_111 = engine.check_eligibility("CSE 111", {"CSE 101"})
run_test(
  "CSE 111 satisfies with CSE 101 alone (DNF track split)",
  can_take_111,
  f"Engine still demanding other tracks: {missing_111}",
)

# 4. CSE 130 Prerequisites
can_take_130, missing_130 = engine.check_eligibility(
  "CSE 130", {"CSE 101", "CSE 12"}
)
run_test(
  "CSE 130 satisfies with CSE 101",
  can_take_130,
  f"Missing groups: {missing_130}",
)

# 5. Roadmap Length Sanity Check
plan_111 = engine.generate_quarter_plan(["CSE 111"], major="CS_BS")
qtr_count = len(plan_111)
run_test(
  "Roadmap to CSE 111 is realistic (<= 8 quarters from scratch)",
  0 < qtr_count <= 8,
  f"Generated {qtr_count} quarters (potential OR-loop bloat)",
)

print("========================================")
if failures == 0:
  print("All graph integrity tests PASSED! ✨")
  sys.exit(0)
else:
  print(f"Total failures: {failures}. Review graph extraction logic.")
  sys.exit(1)
