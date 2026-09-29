from autogen import AssistantAgent
from app.config import LLM_CONFIG, OPENAI_MODEL

print(f"Model: {OPENAI_MODEL}")

test_agent = AssistantAgent(
    name="Test_Agent",
    system_message="You are a friendly FreshKart support assistant. Reply in one short line.",
    llm_config=LLM_CONFIG,
)

reply = test_agent.generate_reply(
    messages=[{"role": "user", "content": "Hi, are you working?"}]
)

print("Agent reply:", reply)