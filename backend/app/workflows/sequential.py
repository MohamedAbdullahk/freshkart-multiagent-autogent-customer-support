from autogen import GroupChat

from app.agents.factory import (
    create_specialists,
    create_tool_executor,
    create_customer,
    create_chat_manager,
)
from app.workflows.tool_routing import with_tool_routing

# Fixed speaking order for the sequential approach
PIPELINE = [
    "Triage_Agent",
    "Tech_Support_Agent",
    "Billing_Agent",
    "Delivery_Agent",
    "Quality_Compliance_Agent",
    "Customer_Liaison_Agent",
]


def _pipeline_selector(customer, agents):
    """Round robin: pick the next agent in PIPELINE order, stop after the last one."""
    order = [agents[name] for name in PIPELINE]

    def select_next_speaker(last_speaker, groupchat):
        if last_speaker is customer:
            return order[0]
        position = order.index(last_speaker)
        if position + 1 < len(order):
            return order[position + 1]
        return None

    return select_next_speaker


def run_sequential(ticket: str, use_tools: bool = True, verbose: bool = True) -> dict:
    agents = create_specialists(with_tools=use_tools)
    customer = create_customer()

    selector = _pipeline_selector(customer, agents)
    members = [customer, *agents.values()]

    # Tools on: add the executor and wrap the selector with tool routing
    if use_tools:
        executor = create_tool_executor()
        selector = with_tool_routing(selector, executor)
        members.append(executor)

    groupchat = GroupChat(
        agents=members,
        messages=[],
        max_round=30,
        speaker_selection_method=selector,
    )
    chat_manager = create_chat_manager(groupchat)

    customer.initiate_chat(chat_manager, message=ticket, silent=not verbose)

    # Sequential has no guardrails, so events are not applicable (None)
    return {"messages": groupchat.messages, "guardrail_events": None}