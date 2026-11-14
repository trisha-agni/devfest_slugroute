from slugroute.agent.advisor import SlugAdvisor

print("1. Initializing advisor...")
advisor = SlugAdvisor()
print("2. Sending prompt to Gemini...")

print("--- Turn 1: Planning ---")
reply1 = advisor.chat(
  "I am a CS freshman who has completed CSE 20 and MATH 19A. "
  "Can I take CSE 101 next quarter, and what should my plan to take it look like?"
)
print(reply1)

print("\n--- Turn 2: Follow-up ---")
reply2 = advisor.chat("What are good AI electives I can take once I finish CSE 101?")
print(reply2)
