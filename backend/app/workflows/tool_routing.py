def with_tool_routing(base_selector, executor):
    """Wrap a speaker selector so tool calls go to the executor and results go back to the caller."""

    def select_next_speaker(last_speaker, groupchat):
        last_msg = groupchat.messages[-1]

        # Tool call: the executor runs it
        if last_msg.get("tool_calls"):
            return executor

        # Tool result: send it back to the agent that asked for it
        if last_speaker is executor:
            caller_name = groupchat.messages[-2]["name"]
            return groupchat.agent_by_name(caller_name)

        # Normal message: use the workflow's own rule
        return base_selector(last_speaker, groupchat)

    return select_next_speaker