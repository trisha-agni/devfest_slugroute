import time
from google import genai
from google.genai import types
from slugroute.config import GEMINI_API_KEY

print("1. Initializing client with 10s network timeout...")
client = genai.Client(
  api_key=GEMINI_API_KEY,
  http_options=types.HttpOptions(timeout=10000),  # 10s in milliseconds
)

# Test models from your active list
models_to_test = [
  "gemini-3.5-flash",
  "gemini-3.7-flash",
  "gemini-2.5-flash-lite",
  "gemini-3.8-flash",
]

for model in models_to_test:
  print(f"\nTesting '{model}' (basic text without tools)...")
  t0 = time.time()
  try:
    resp = client.models.generate_content(
      model=model,
      contents="Reply with 'OK'",
    )
    print(f"-> SUCCESS in {time.time() - t0:.2f}s: {resp.text.strip()}")
  except Exception as e:
    print(f"-> FAILED in {time.time() - t0:.2f}s: {e}")
