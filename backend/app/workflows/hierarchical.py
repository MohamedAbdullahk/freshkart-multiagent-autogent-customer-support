import re
from autogen import GroupChat

from app.agents.factory import (
    create_specialists,
    create_manager,
    create_tool_executor,
    create_customer,
    create_chat_manager,
)
from app.workflows.tool_routing import with_tool_routing

# If any of these agents spoke, compliance review is mandatory before the final reply
AGENTS_REQUIRING_REVIEW = {"Tech_Support_Agent", "Billing_Agent", "Delivery_Agent"}
FINAL_AGENT = "Customer_Liaison_Agent"
COMPLIANCE_AGENT = "Quality_Compliance_Agent"


def _manager_selector(manager_agent, agents, guardrail_events):
    """Follow the Manager's NEXT decision, with code-level guardrails."""

    def select_next_speaker(last_speaker, groupchat):
        # Rule 1: final reply is written, stop the chat
        if last_speaker.name == FINAL_AGENT:
            return None

        # Rule 2: Manager spoke, follow the "NEXT:" decision
        if last_speaker is manager_agent:
            content = groupchat.messages[-1].get("content") or ""
            match = re.search(r"NEXT:\s*(\w+)", content)
            chosen = match.group(1) if match else FINAL_AGENT
            if chosen not in agents:
                chosen = FINAL_AGENT

            spoken = {m.get("name") for m in groupchat.messages}

            # Guardrail 1: never call the same specialist twice
            if chosen in spoken and chosen != FINAL_AGENT:
                guardrail_events.append(f"Blocked repeat call to {chosen}")
                chosen = FINAL_AGENT

            # Guardrail 2: specialist answers must be reviewed before the final reply
            if chosen == FINAL_AGENT and spoken & AGENTS_REQUIRING_REVIEW and COMPLIANCE_AGENT not in spoken:
                guardrail_events.append("Compliance review enforced before final reply")
                chosen = COMPLIANCE_AGENT

            return agents[chosen]

        # Rule 3: Customer or a specialist spoke, control goes back to the Manager
        return manager_agent

    return select_next_speaker


def run_hierarchical(ticket: str, use_tools: bool = True, verbose: bool = True) -> dict:
    # Manager replaces Triage in this approach
    agents = create_specialists(with_tools=use_tools)
    agents.pop("Triage_Agent")
    manager_agent = create_manager()
    customer = create_customer()

    guardrail_events = []
    selector = _manager_selector(manager_agent, agents, guardrail_events)
    members = [customer, manager_agent, *agents.values()]

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

    return {"messages": groupchat.messages, "guardrail_events": guardrail_events}