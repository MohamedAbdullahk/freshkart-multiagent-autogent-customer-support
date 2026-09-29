NON_LLM_AGENTS = {"Customer", "Tool_Executor"}
FINAL_AGENT = "Customer_Liaison_Agent"


def _build_logs(messages: list) -> list:
    """Convert raw chat messages into a simple timeline for the frontend."""
    logs = []
    for msg in messages:
        name = msg.get("name", "")
        if msg.get("tool_calls"):
            for call in msg["tool_calls"]:
                fn = call["function"]
                logs.append({"agent": name, "type": "tool_call",
                             "content": f'{fn["name"]}({fn["arguments"]})'})
        elif msg.get("tool_responses") or msg.get("role") == "tool":
            logs.append({"agent": name, "type": "tool_result",
                         "content": msg.get("content", "")})
        else:
            logs.append({"agent": name, "type": "message",
                         "content": msg.get("content", "")})
    return logs


def _final_response(messages: list) -> str:
    """Return the last message written by the Customer Liaison agent."""
    for msg in reversed(messages):
        if msg.get("name") == FINAL_AGENT and msg.get("content"):
            return msg["content"].replace("TERMINATE", "").strip()
    return ""


def build_result(messages, approach, use_tools, guardrail_events,
                 duration_seconds, include_logs) -> dict:
    """Build the standard result format used by the API and the frontend."""
    final = _final_response(messages)
    status = "ok" if final else "incomplete"

    # Customer mode: send only what the customer is allowed to see
    if not include_logs:
        return {"status": status, "final_response": final}

    speakers = [m.get("name", "") for m in messages]
    tool_calls = [
        call["function"]["name"]
        for m in messages
        for call in (m.get("tool_calls") or [])
    ]

    return {
        "status": status,
        "final_response": final,
        "approach": approach,
        "use_tools": use_tools,
        "metrics": {
            "llm_turns": len([s for s in speakers if s not in NON_LLM_AGENTS]),
            "tool_calls": len(tool_calls),
            "duration_seconds": round(duration_seconds, 1),
        },
        "tools_used": tool_calls,
        # None = approach has no guardrails; True/False = whether any guardrail fired
        "guardrail_triggered": None if guardrail_events is None else len(guardrail_events) > 0,
        "guardrail_events": guardrail_events or [],
        "speaker_order": speakers,
        "logs": _build_logs(messages),
    }