from slugroute.graph.engine import AcademicGraphEngine

engine = AcademicGraphEngine()

print("--- CS Major Roadmap to CSE 102 ---")
for q in engine.generate_quarter_plan(["CSE 102"], major="CS_BS"):
  print(f"Quarter {q['quarter']} ({q['total_credits']} cr): {q['courses']}")
