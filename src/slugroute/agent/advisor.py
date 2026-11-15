# external imports
from google import genai
from google.genai import types
from typing import Any
import json
import time
# internal imports
from slugroute.agent.tools import (
  check_prerequisites,
  generate_roadmap,
  get_engine,
  get_retriever,
  inspect_course,
  search_courses,
)
from slugroute.config import (
  FALLBACK_MODELS,
  GEMINI_API_KEY,
  GEMINI_MODEL_NAME,
)

SYSTEM_INSTRUCTION = """
You are SlugRoute, an expert AI Academic Advisor for UCSC students.
Your mission is to provide authoritative, hallucination-free academic planning.

Key Rules:
1. Grounding: Never invent prerequisites or course sequences. Always verify via tools:
   - Use `search_courses` to discover relevant courses.
   - Use `inspect_course` to verify details, descriptions, and credits.
   - Use `check_prerequisites` before declaring if a student can take a class.
   - Use `generate_roadmap` to build multi-quarter graduation pathways.
2. Tool Efficiency: `search_courses` already provides credits, descriptions, and
   prerequisites. Only inspect or check prerequisites for the top 2-3 most relevant
   courses you intend to recommend, rather than every candidate course found.
3. Tone & Persona: Supportive, structured, and realistic about student workloads.
4. Quarter Planning: When presenting schedules, state quarter numbers, total credits,
   and remind students that 15–19 credits is a standard full-time load.
""".strip()


class SlugAdvisor:

  def __init__(self, model_name: str | None = None):
    if not GEMINI_API_KEY:
      raise ValueError("GEMINI_API_KEY not found. Set it in your .env file.")

    self.model_name = model_name or GEMINI_MODEL_NAME
    self.client = genai.Client(
      api_key=GEMINI_API_KEY,
      http_options=types.HttpOptions(timeout=25000),
    )
    self.tools = [
      search_courses,
      check_prerequisites,
      generate_roadmap,
      inspect_course,
    ]
    self._chat_session: Any = None
    self.reset()

  def reset(self, history: list[Any] | None = None):
    """Start or restore a chat session."""
    self._chat_session = self.client.chats.create(
      model=self.model_name,
      config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=self.tools,
        temperature=0.2,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
          maximum_remote_calls=20,
        ),
      ),
      history=history or [],
    )

  def _local_fallback(self, query: str) -> str:
    """Deterministic offline answer if all cloud models are unavailable."""
    engine = get_engine()
    retriever = get_retriever()

    # If user mentions specific course, check it directly
    words = query.upper().replace(",", " ").split()
    found_code = None
    for i in range(len(words) - 1):
      cand = f"{words[i]} {words[i+1]}"
      if engine.resolve_code(cand):
        found_code = engine.resolve_code(cand)
        break

    if found_code:
      course = retriever.get_course(found_code)
      plan = engine.generate_quarter_plan([found_code])
      return (
        f"*(Offline Engine Fallback)*\n\n"
        f"**Course:** {found_code} - {course.get('title', '')} ({course.get('credits')} cr)\n"  # noqa
        f"**Prerequisites:** {course.get('prereq_raw', 'None')}\n\n"
        f"**Computed Roadmap:**\n```json\n{json.dumps(plan, indent=2)}\n```"
      )

    # General search fallback
    results = retriever.search(query, top_k=3)
    res_str = "\n".join([f"- **{c['code']}**: {c['title']} ({c['credits']} cr)" for c in results])  # noqa
    return (
      f"*(Offline Engine Fallback)*\n\n"
      f"Cloud AI is busy. Here are relevant catalog matches from the local index:\n\n{res_str}"  # noqa
    )

  def chat(self, user_message: str) -> str:
    """Send message to Gemini agent with automatic fallback and history preservation."""
    candidates = [self.model_name] + [
      m for m in FALLBACK_MODELS if m != self.model_name
    ]

    for model in candidates:
      try:
        if self.model_name != model:
          # Carry forward existing conversation history to the fallback model
          history = self._chat_session.get_history() if self._chat_session else []
          self.model_name = model
          self.reset(history=history)

        response = self._chat_session.send_message(user_message)

        # 1. Direct text return
        if response.text and response.text.strip():
          return response.text.strip()

        # 2. If AFC stopped with open tool calls or empty text, request synthesis
        if response.function_calls or not response.text:
          followup = self._chat_session.send_message(
            "Please summarize your recommendations and answer the question "
            "based on the tool results gathered so far."
          )
          if followup.text and followup.text.strip():
            return followup.text.strip()

        # 3. Check for any raw text parts (e.g., from reasoning/thought parts)
        if (
          response.candidates
          and response.candidates[0].content
          and response.candidates[0].content.parts
        ):
          raw_texts = [
            p.text
            for p in response.candidates[0].content.parts
            if getattr(p, "text", None) and p.text.strip()
          ]
          if raw_texts:
            return "\n\n".join(raw_texts).strip()

        print(f"⚠️ {model} returned empty response. Trying fallback...")
        continue
      except Exception as e:
        err = str(e).upper()
        if "429" in err or "503" in err or "RESOURCE_EXHAUSTED" in err:
          print(f"⚠️ {model} throttled ({e}), trying fallback in 2s...")
          time.sleep(2)
          continue
        print(f"⚠️ {model} error: {e}")
        continue

    # Final safety net: zero crash, return local deterministic output
    return self._local_fallback(user_message)
