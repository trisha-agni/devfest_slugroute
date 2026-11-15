# external imports
from networkx.readwrite import json_graph
from pathlib import Path
from typing import Any
import json
import networkx as nx
import re
# internal imports
from slugroute.config import GRAPH_FILE


class AcademicGraphEngine:

  # ---------------------------------------------------------
  # Part 1: Loading & Inspection
  # ---------------------------------------------------------
  def __init__(self, graph_path: Path | None = None):
    path = graph_path or GRAPH_FILE
    if not path.exists():
      raise FileNotFoundError(f"prerequisite graph not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
      data = json.load(f)

    self.G: nx.DiGraph = json_graph.node_link_graph(data)
    # Quick case-insensitive lookup: "cse 101" -> "CSE 101"
    self._code_map = {node.upper(): node for node in self.G.nodes()}

  def resolve_code(self, course_code: str) -> str | None:
    """Normalize input string to exact catalog course code."""
    if not isinstance(course_code, str):
      return None
    normalized = " ".join(course_code.strip().upper().split())
    return self._code_map.get(normalized)

  def get_course_data(self, course_code: str) -> dict[str, Any] | None:
    code = self.resolve_code(course_code)
    return dict(self.G.nodes[code]) if code else None

  def get_course_url(self, course_code: str) -> str | None:
    data = self.get_course_data(course_code)
    return data.get("url") if data else None

  def linkify_courses(self, text: str) -> str:
    """Converts catalog course codes into official clickable catalog links."""
    if not text:
      return text

    # Split by fenced code blocks (``` ... ```) to avoid altering literal code
    parts = re.split(r"(```[\s\S]*?```)", text)
    pattern = re.compile(
      r"(\[.*?\]\(.*?\)|\`([A-Z]{2,5}(?:\s+[A-Z]{2,4})?\s+\d+[A-Z]?)\`|"
      r"\b([A-Z]{2,5}(?:\s+[A-Z]{2,4})?\s+\d+[A-Z]?)\b)"
    )

    def replacer(match: re.Match) -> str:
      full = match.group(0)
      if full.startswith("[") and "](" in full:
        return full
      code = match.group(2) or match.group(3)
      url = self.get_course_url(code)
      if url:
        if match.group(2):
          return f"[`{code}`]({url})"
        return f"[{code}]({url})"
      return full

    for i in range(0, len(parts), 2):
      parts[i] = pattern.sub(replacer, parts[i])

    return "".join(parts)

  # ---------------------------------------------------------
  # Part 2: Prerequisite Validator (CNF Logic)
  # ---------------------------------------------------------
  @staticmethod
  def _get_tracks(node: dict[str, Any]) -> list[list[list[str]]]:
    """Extracts prerequisites and guarantees 3-level DNF:
    list[Track -> list[Group -> list[str]]]."""
    raw = node.get("prereq_tracks") or node.get("prereq_groups")
    if not raw or not isinstance(raw, list):
      return []

    def is_group(x: Any) -> bool:
      return isinstance(x, list) and all(isinstance(c, str) for c in x)

    def is_track(x: Any) -> bool:
      return isinstance(x, list) and all(is_group(g) for g in x)

    data = raw
    # Peel off accidental extra wrappers
    while isinstance(data, list) and len(data) > 0 and not is_track(data):
      if all(is_track(t) for t in data):
        return data
      data = data[0]

    if is_track(data):
      return [data]
    return []

  def check_eligibility(
    self,
    course_code: str,
    completed_courses: set[str],
  ) -> tuple[bool, list[list[str]]]:
    """Check if course prerequisites are satisfied across any valid track."""
    code = self.resolve_code(course_code)
    if not code:
      return False, []

    completed = {
      self.resolve_code(c)
      for c in completed_courses
      if self.resolve_code(c)
    }

    tracks = self._get_tracks(self.G.nodes[code])
    if not tracks:
      return True, []

    best_missing = None

    for track in tracks:
      missing_in_track = []
      for group in track:
        if not any(self.resolve_code(alt) in completed for alt in group):
          missing_in_track.append(group)

      if len(missing_in_track) == 0:
        return True, []

      if best_missing is None or len(missing_in_track) < len(best_missing):
        best_missing = missing_in_track

    return False, best_missing or []

  # ---------------------------------------------------------
  # Part 3: Subgraph Extractor (For Interactive UI Graph)
  # ---------------------------------------------------------
  def get_prerequisite_subgraph(self, target_code: str) -> nx.DiGraph:
    """Returns the ancestor graph (all direct & indirect prereqs) for UI visualizer."""
    code = self.resolve_code(target_code)
    if not code:
      return nx.DiGraph()

    ancestors = nx.ancestors(self.G, code)
    nodes = ancestors | {code}
    return self.G.subgraph(nodes).copy()

  def get_unlocked_courses(self, completed_courses: set[str]) -> list[str]:
    """Finds all catalog courses that the student is now newly eligible to take."""
    completed = {self.resolve_code(c) for c in completed_courses if self.resolve_code(c)}
    unlocked = []

    for node in self.G.nodes():
      if node in completed:
        continue
      eligible, _ = self.check_eligibility(node, completed)
      if eligible:
        unlocked.append(node)

    return sorted(unlocked)

  # ---------------------------------------------------------
  # Part 4: Major Profiles & Quarter Sequencer
  # ---------------------------------------------------------

  # Preferences for breaking "OR" ties based on declared major
  MAJOR_PROFILES: dict[str, dict[str, Any]] = {
    "CS_BS": {
      "preferred_depts": ["CSE", "MATH", "AM"],
      "ranks": {
        "MATH 19A": 1, "MATH 19B": 1, "MATH 21": 1, "AM 10": 1,
        "CSE 20": 1, "CSE 30": 1, "CSE 12": 1, "CSE 13S": 1, "CSE 16": 1,
        "CSE 13E": 3, "ECE 13": 3,
        "MATH 11A": 8, "MATH 11B": 8, "BME 160": 8, "CSE 5J": 8,
      },
      "entry_courses": {"MATH 19A", "MATH 20A", "CSE 20"},
    },
    "BME_BS": {
      "preferred_depts": ["BME", "BIOL", "CHEM", "MATH"],
      "ranks": {
        "BME 160": 1, "BIOL 20A": 1, "CHEM 1A": 1,
        "MATH 11A": 1, "MATH 11B": 1,
        "MATH 19A": 3, "MATH 19B": 3,
        "CSE 12": 8, "CSE 13S": 8,
      },
      "entry_courses": {"CHEM 1A", "MATH 11A", "BIOL 20A", "CSE 20"},
    },
  }

  def _resolve_minimal_prereqs(
    self,
    target: str,
    completed: set[str],
    major: str = "CS_BS",
  ) -> set[str]:
    """Picks one optimal path across multi-track DNF prerequisites."""
    profile = self.MAJOR_PROFILES.get(major, self.MAJOR_PROFILES["CS_BS"])
    preferred_depts = set(profile["preferred_depts"])
    ranks = profile["ranks"]
    entry_courses = profile["entry_courses"]

    required = set()
    to_visit = [target]
    visited = set()

    def score_course(code: str) -> int:
      if code in completed:
        return 0
      if code in ranks:
        return ranks[code]
      dept = code.split()[0]
      if dept in preferred_depts:
        return 5
      return 10

    def score_track(tr: list[list[str]]) -> int:
      return sum(min(score_course(alt) for alt in grp) for grp in tr)

    while to_visit:
      curr = to_visit.pop(0)
      if curr in visited or curr in completed:
        continue
      visited.add(curr)
      required.add(curr)

      # Stop at college entry-level courses (placement assumed)
      if curr in entry_courses:
        continue

      tracks = self._get_tracks(self.G.nodes[curr])
      if not tracks:
        continue

      # Pick the track with lowest total score for the declared major
      best_track = sorted(tracks, key=score_track)[0]

      for group in best_track:
        # Skip group if already satisfied by completed or scheduled courses
        if any(alt in completed or alt in required for alt in group):
          continue
        best_alt = sorted(group, key=score_course)[0]
        to_visit.append(best_alt)

    return required

  def generate_quarter_plan(
    self,
    target_courses: list[str],
    completed_courses: set[str] | None = None,
    major: str = "CS_BS",
    max_credits_per_qtr: int = 19,
  ) -> list[dict[str, Any]]:
    """Builds a quarter-by-quarter schedule customized to student's major."""
    profile = self.MAJOR_PROFILES.get(major, self.MAJOR_PROFILES["CS_BS"])
    entry_courses = profile["entry_courses"]

    completed = {
      self.resolve_code(c)
      for c in (completed_courses or set())
      if self.resolve_code(c)
    }

    # 1. Resolve prerequisites tailored to the major
    needed_nodes = set()
    for t in target_courses:
      resolved = self.resolve_code(t)
      if resolved and resolved not in completed:
        needed_nodes.update(
          self._resolve_minimal_prereqs(resolved, completed, major=major)
        )

    needed_nodes -= completed
    if not needed_nodes:
      return []

    subgraph = self.G.subgraph(needed_nodes)
    order = list(nx.topological_sort(subgraph))

    # 2. Greedily schedule into quarters
    quarters: list[dict[str, Any]] = []
    scheduled = set(completed)
    remaining = list(order)

    while remaining:
      current_quarter_courses = []
      current_credits = 0

      for course in list(remaining):
        course_credits = self.G.nodes[course].get("credits") or 5
        # Entry courses (like MATH 19A / CSE 20) are immediately eligible
        if course in entry_courses:
          eligible = True
        else:
          eligible, _ = self.check_eligibility(course, scheduled)

        if eligible:
          if current_credits + course_credits <= max_credits_per_qtr:
            current_quarter_courses.append(course)
            current_credits += course_credits
            remaining.remove(course)

      if not current_quarter_courses:
        course = remaining.pop(0)
        current_quarter_courses.append(course)
        current_credits += self.G.nodes[course].get("credits") or 5

      scheduled.update(current_quarter_courses)
      quarters.append({
        "quarter": len(quarters) + 1,
        "courses": current_quarter_courses,
        "total_credits": current_credits,
      })

    return quarters
