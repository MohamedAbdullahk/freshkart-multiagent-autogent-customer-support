import copy
from autogen import AssistantAgent, UserProxyAgent, GroupChatManager

from app.config import LLM_CONFIG
from app.agents import prompts
from app.tools.order_tools import (
    get_order_details,
    get_payment_history,
    get_delivery_status,
    get_system_status,
    get_store_info,
    get_policy,
)

# Agent name -> system prompt
AGENT_PROMPTS = {
    "Triage_Agent": prompts.TRIAGE_PROMPT,
    "Tech_Support_Agent": prompts.TECH_PROMPT,
    "Billing_Agent": prompts.BILLING_PROMPT,
    "Delivery_Agent": prompts.DELIVERY_PROMPT,
    "Quality_Compliance_Agent": prompts.COMPLIANCE_PROMPT,
    "Customer_Liaison_Agent": prompts.LIAISON_PROMPT,
}

# Agent name -> allowed tools
AGENT_TOOLS = {
    "Triage_Agent": [],
    "Tech_Support_Agent": [get_system_status, get_order_details],
    "Billing_Agent": [get_payment_history, get_order_details, get_policy],
    "Delivery_Agent": [get_delivery_status, get_policy],
    "Quality_Compliance_Agent": [get_policy],
    "Customer_Liaison_Agent": [get_store_info],
}


def create_specialists(with_tools: bool = True) -> dict:
    """Create the specialist agents. Set with_tools=False to create them without tools."""
    agents = {}
    for name, system_message in AGENT_PROMPTS.items():
        agent = AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=copy.deepcopy(LLM_CONFIG),
        )
        if with_tools:
            # Caller side: tell the LLM which tools this agent is allowed to use
            for func in AGENT_TOOLS[name]:
                agent.register_for_llm(description=func.__doc__.strip())(func)
        agents[name] = agent
    return agents


def create_tool_executor() -> UserProxyAgent:
    """Non-LLM agent that executes tool calls for all specialists."""
    all_tools = {
        func.__name__: func
        for tools in AGENT_TOOLS.values()
        for func in tools
    }
    return UserProxyAgent(
        name="Tool_Executor",
        human_input_mode="NEVER",
        llm_config=False,
        code_execution_config=False,
        function_map=all_tools,
        default_auto_reply="",
        # A reply without a tool call means the tool work is finished
        is_termination_msg=lambda msg: not msg.get("tool_calls"),
    )


def create_manager() -> AssistantAgent:
    """Create the Manager agent that decides which specialist speaks next."""
    return AssistantAgent(
        name="Manager_Agent",
        system_message=prompts.MANAGER_PROMPT,
        llm_config=copy.deepcopy(LLM_CONFIG),
    )


def create_customer() -> UserProxyAgent:
    """Non-LLM agent that brings the customer ticket into the group chat."""
    return UserProxyAgent(
        name="Customer",
        human_input_mode="NEVER",
        llm_config=False,
        code_execution_config=False,
        default_auto_reply="",
    )


def create_chat_manager(groupchat) -> GroupChatManager:
    """Message router for the group chat. No LLM, because our selector decides the next speaker."""
    return GroupChatManager(
        groupchat=groupchat,
        llm_config=False,
        is_termination_msg=lambda m: (m.get("content") or "").rstrip().endswith("TERMINATE"),
    )