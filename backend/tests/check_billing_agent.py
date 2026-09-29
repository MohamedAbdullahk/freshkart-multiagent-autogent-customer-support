from app.agents.factory import create_specialists, create_tool_executor

agents = create_specialists()
billing = agents["Billing_Agent"]
executor = create_tool_executor()

ticket = "I was charged Rs. 850 twice for order #FK1023, but the app shows 'Payment Failed'."

result = executor.initiate_chat(billing, message=ticket, max_turns=4)

print("\n" + "=" * 60)
print("BILLING AGENT FINAL ANALYSIS:")
print(result.summary)