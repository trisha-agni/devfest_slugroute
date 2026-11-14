from slugroute.rag.retriever import CourseRetriever

retriever = CourseRetriever()

print("--- 1. Semantic Search: 'machine learning and neural networks' ---")
results = retriever.search("machine learning and neural networks", top_k=3)
for c in results:
  print(f"[{c['similarity_score']}] {c['code']} - {c['title']}")

print("\n--- 2. Filtered Search: 'ethics' with GE='PE-H' ---")
filtered = retriever.search("ethics and technology", top_k=2, gen_ed="PE-H")
for c in filtered:
  print(f"[{c['similarity_score']}] {c['code']} - {c['title']} (GE: {c['gen_ed']})")

print("\n--- 3. Exact Course Lookup: 'CSE 101' ---")
course = retriever.get_course("cse 101")
if course:
  print(f"{course['code']}: {course['title']} ({course['credits']} cr)")
  print(f"Raw Prereqs: {course['prereq_raw']}")
