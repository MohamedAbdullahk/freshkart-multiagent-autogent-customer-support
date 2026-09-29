import streamlit as st

from api_client import check_health, get_sample_tickets, get_options

LOG_ICONS = {"message": "💬", "tool_call": "🔧", "tool_result": "📦"}


def is_dev_mode() -> bool:
    """Demo: read the sidebar toggle. Production: read DEV_MODE from the environment instead."""
    return st.session_state.get("view_as") == "Developer"


# Cached backend reads: Streamlit reruns the script on every click,
# so these avoid repeating the same HTTP calls each time.
@st.cache_data(ttl=10, show_spinner=False)
def cached_health() -> bool:
    return check_health()


@st.cache_data(ttl=300, show_spinner=False)
def cached_sample_tickets() -> list:
    return get_sample_tickets()


@st.cache_data(ttl=300, show_spinner=False)
def cached_options() -> dict:
    return get_options()


def render_metrics(result: dict) -> None:
    metrics = result["metrics"]
    col1, col2, col3 = st.columns(3)
    col1.metric("LLM turns", metrics["llm_turns"])
    col2.metric("Tool calls", metrics["tool_calls"])
    col3.metric("Time", f'{metrics["duration_seconds"]}s')


def render_guardrail(result: dict) -> None:
    triggered = result["guardrail_triggered"]
    if triggered is None:
        st.caption("Guardrail: not applicable (sequential)")
    elif triggered:
        st.warning("Guardrail triggered")
        for event in result["guardrail_events"]:
            st.markdown(f"- {event}")
    else:
        st.success("Guardrail: not triggered")


def render_timeline(result: dict) -> None:
    for i, log in enumerate(result["logs"], start=1):
        icon = LOG_ICONS.get(log["type"], "•")
        st.markdown(f"`{i:02d}` {icon} **{log['agent']}**")
        content = log.get("content") or ""
        if log["type"] == "message":
            st.markdown(content.replace("TERMINATE", "").strip())
        else:
            st.code(content, language="json")