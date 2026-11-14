from google import genai
from slugroute.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

if not GEMINI_API_KEY:
  raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=GEMINI_API_KEY)
available = [
  m.name.replace("models/", "")
  for m in client.models.list()
  if "generateContent" in (m.supported_actions or [])
]

print("--- Available Models Supporting generateContent ---")
for model in sorted(available):
  print(f"- {model}")

print("\n--- Model Configuration Check ---")
print(f"Configured: '{GEMINI_MODEL_NAME}'")
if GEMINI_MODEL_NAME in available:
  print("Status: READY (Model is available)")
else:
  print(f"Status: WARNING (Model '{GEMINI_MODEL_NAME}' not found in available list)")
