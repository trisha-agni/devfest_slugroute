# external imports
import json
# internal imports
from slugroute.graph.engine import AcademicGraphEngine
from slugroute.rag.retriever import CourseRetriever

# Initialize singletons to avoid repeated disk reads
_retriever: CourseRetriever | None = None
_engine: AcademicGraphEngine | None = None


def get_retriever() -> CourseRetriever:
  global _retriever
  if _retriever is None:
    _retriever = CourseRetriever()
  return _retriever


def get_engine() -> AcademicGraphEngine:
  global _engine
  if _engine is None:
    _engine = AcademicGraphEngine()
  return _engine


# -------------------------------------------------------------------
# Agent Tools (Docstrings and type annotations guide Gemini calling)
# -------------------------------------------------------------------


def search_courses(
  query: str,
  subject: str = "",
  gen_ed: str = "",
  top_k: int = 5,
) -> str:
  """Find UCSC courses semantically matching a topic, subject, or GE code.

  Args:
    query: Natural language topic (e.g. 'deep learning', 'ethics in tech').
    subject: Optional department code filter (e.g. 'CSE', 'MATH', 'AM').
    gen_ed: Optional General Education category (e.g. 'PE-H', 'MF', 'SI').
    top_k: Maximum number of courses to return.
  """
  print(f"🔧 [Agent Tool] Calling search_courses(query='{query}')...")
  r = get_retriever()
  matches = r.search(query=query, top_k=top_k, subject=subject, gen_ed=gen_ed)
  if not matches:
    return "No matching courses found."

  formatted = []
  for m in matches:
    formatted.append(
      f"Course: {m['code']} - {m['title']} ({m['credits']} cr, GE: {m.get('gen_ed')})\n"
      f"Score: {m['similarity_score']}\n"
      f"Desc: {m.get('desc', '')[:180]}...\n"
      f"Prereqs: {m.get('prereq_raw', 'None')}"
    )
  return "\n\n".join(formatted)


def check_prerequisites(
  course_code: str,
  completed_courses: list[str],
) -> str:
  """Determines if a student is eligible to take a specific UCSC course.

  Args:
    course_code: The course identifier (e.g. 'CSE 101').
    completed_courses: List of courses already completed (e.g. ['CSE 20', 'MATH 19A']).
  """
  print(f"🔧 [Agent Tool] Calling check_prerequisites({course_code})...")
  e = get_engine()
  resolved = e.resolve_code(course_code)
  if not resolved:
    return f"Course '{course_code}' not found in the UCSC catalog."

  can_take, missing = e.check_eligibility(resolved, set(completed_courses))
  if can_take:
    return f"ELIGIBLE: All prerequisites satisfied for {resolved}."

  # Format CNF missing requirements cleanly for the agent
  missing_clauses = []
  for group in missing:
    missing_clauses.append(" OR ".join(group))
  missing_str = " AND ".join([f"({c})" for c in missing_clauses])

  return (
    f"INELIGIBLE: Missing prerequisite requirement(s) for {resolved}: {missing_str}"
  )


def generate_roadmap(
  target_courses: list[str],
  completed_courses: list[str] = [],
  major: str = "CS_BS",
  max_credits_per_qtr: int = 19,
) -> str:
  """Generates a quarter-by-quarter schedule to reach target courses.

  Args:
    target_courses: Target courses to reach (e.g. ['CSE 102', 'CSE 130']).
    completed_courses: Courses already completed (e.g. ['CSE 20', 'MATH 19A']).
    major: Student declared major ('CS_BS' or 'BME_BS').
    max_credits_per_qtr: Max credit limit per quarter (default 19).
  """
  print(f"🔧 [Agent Tool] Calling generate_roadmap({target_courses})...")
  e = get_engine()
  plan = e.generate_quarter_plan(
    target_courses=target_courses,
    completed_courses=set(completed_courses or []),
    major=major,
    max_credits_per_qtr=max_credits_per_qtr,
  )
  if not plan:
    return "Target courses are either already completed or invalid."

  return json.dumps(plan, indent=2)


def inspect_course(course_code: str) -> str:
  """Fetches authoritative catalog details and prerequisites for a single course.

  Args:
    course_code: The course identifier (e.g. 'CSE 101').
  """
  print(f"🔧 [Agent Tool] Calling inspect_course({course_code})...")
  r = get_retriever()
  course = r.get_course(course_code)
  if not course:
    return f"Course '{course_code}' not found in catalog."

  return (
    f"Code: {course['code']}\n"
    f"Title: {course['title']}\n"
    f"Credits: {course['credits']}\n"
    f"GE: {course.get('gen_ed')}\n"
    f"Prerequisites: {course.get('prereq_raw', 'None')}\n"
    f"Description: {course.get('desc', '')}\n"
    f"Catalog URL: {course.get('url', '')}"
  )
