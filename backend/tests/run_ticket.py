import json
import sys

from app.workflows.runner import run_ticket
from tests.tickets import TICKETS

# Usage: python -m tests.run_ticket <T1|T2|T3> <sequential|hierarchical> <on|off> [customer|logs]
ticket_id = sys.argv[1] if len(sys.argv) > 1 else "T1"
approach = sys.argv[2] if len(sys.argv) > 2 else "hierarchical"
use_tools = (sys.argv[3] if len(sys.argv) > 3 else "on") == "on"
extra = sys.argv[4] if len(sys.argv) > 4 else ""
customer_mode = extra == "customer"
show_logs = extra == "logs"

result = run_ticket(
    TICKETS[ticket_id],
    approach=approach,
    use_tools=use_tools,
    include_logs=not customer_mode,
)

if customer_mode:
    # Show exactly what the customer would receive
    print(json.dumps(result, indent=2))
    sys.exit()

metrics = result["metrics"]
guardrail = result["guardrail_triggered"]

print("=" * 60)
print(f"TICKET {ticket_id} | {approach} | tools {'on' if use_tools else 'off'} | status: {result['status']}")
print("Speaker order:", " → ".join(result["speaker_order"]))
print(f"LLM turns: {metrics['llm_turns']} | Tool calls: {metrics['tool_calls']} | Time: {metrics['duration_seconds']}s")
print("Tools used:", ", ".join(result["tools_used"]) or "none")
print("Guardrail triggered:", "n/a" if guardrail is None else guardrail)
for event in result["guardrail_events"]:
    print(f"  - {event}")

if show_logs:
    print("-" * 60)
    print("TIMELINE:")
    for i, log in enumerate(result["logs"], start=1):
        text = (log["content"] or "").replace("\n", " ")
        print(f"{i:02d}. [{log['type']}] {log['agent']}: {text[:160]}")

print("-" * 60)
print(result["final_response"])