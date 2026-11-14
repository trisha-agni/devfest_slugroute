from slugroute.agent.tools import (
  check_prerequisites,
  generate_roadmap,
  inspect_course,
  search_courses,
)

print("--- 1. Search Tool ---")
print(search_courses("reinforcement learning", top_k=2))

print("\n--- 2. Prereq Check Tool ---")
print(check_prerequisites("CSE 101", ["CSE 20", "MATH 19A"]))

print("\n--- 3. Roadmap Tool ---")
print(generate_roadmap(["CSE 101"], completed_courses=["CSE 20", "MATH 19A"]))

print("\n--- 4. Inspect Tool ---")
print(inspect_course("CSE 101"))
