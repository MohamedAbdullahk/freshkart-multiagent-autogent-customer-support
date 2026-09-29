import streamlit as st

from api_client import run_ticket, compare_tickets, BackendError
from ui_helpers import (
    cached_sample_tickets,
    cached_options,
    render_metrics,
    render_guardrail,
    render_timeline,
)

CUSTOM_TICKET = "Custom ticket"

st.title("Agent lab")
st.caption("Run the same ticket through different agent setups and compare the results.")

# Load ticket samples and approaches from the backend (cached)
try:
    samples = cached_sample_tickets()
    approaches = cached_options()["approaches"]
except BackendError as error:
    st.error(str(error))
    st.stop()


def config_picker(side: str, default_approach: str) -> dict:
    """Approach and tools selector for one column."""
    st.subheader(side)
    default_index = approaches.index(default_approach) if default_approach in approaches else 0
    approach = st.selectbox("Approach", approaches, index=default_index, key=f"{side}_approach")
    tools = st.radio("Tools", ["On", "Off"], horizontal=True, key=f"{side}_tools")
    if tools == "Off":
        st.warning("Demo mode: agents may guess without real data.")
    return {"approach": approach, "use_tools": tools == "On"}


def show_result(side: str, result: dict, config: dict) -> None:
    """Show one run: metrics, guardrail, answer, and an optional timeline."""
    tools_label = "tools on" if config["use_tools"] else "tools off"
    st.markdown(f"#### {side}: {config['approach']} · {tools_label}")

    if result["status"] != "ok":
        st.error("The agents did not produce a final answer.")

    render_metrics(result)
    render_guardrail(result)

    st.markdown("**Final answer**")
    with st.container(border=True):
        st.markdown(result["final_response"] or "_No answer_")

    st.caption("Tools used: " + (", ".join(result["tools_used"]) or "none"))
    st.caption("Speaker order: " + " → ".join(result["speaker_order"]))

    # Render the timeline only when asked, so reruns stay fast
    if st.toggle("Show agent timeline", key=f"{side}_timeline"):
        with st.container(border=True):
            render_timeline(result)


def show_comparison(left: dict, right: dict) -> None:
    """Right vs left difference. Green means the right side used less."""
    lm, rm = left["metrics"], right["metrics"]
    st.markdown("### Right vs left")
    col1, col2, col3 = st.columns(3)
    col1.metric("LLM turns", rm["llm_turns"], delta=rm["llm_turns"] - lm["llm_turns"], delta_color="inverse")
    col2.metric("Tool calls", rm["tool_calls"], delta=rm["tool_calls"] - lm["tool_calls"], delta_color="inverse")
    time_delta = round(rm["duration_seconds"] - lm["duration_seconds"], 1)
    col3.metric("Time", f'{rm["duration_seconds"]}s', delta=f"{time_delta}s", delta_color="inverse")


# 1. Ticket
labels = [f'{t["id"]} - {t["title"]}' for t in samples] + [CUSTOM_TICKET]
choice = st.selectbox("Ticket", labels)
if choice == CUSTOM_TICKET:
    message = st.text_area(
        "Custom ticket",
        placeholder="Type a customer message, for example: My order FK1025 is late. Where is it?",
        height=100,
    )
else:
    message = samples[labels.index(choice)]["message"]
    st.info(message)

# 2. Mode and configs
mode = st.radio("Mode", ["Single run", "Compare"], horizontal=True)
compare = mode == "Compare"

left_col, right_col = st.columns(2)
with left_col:
    left_config = config_picker("Left", "sequential" if compare else "hierarchical")
right_config = None
if compare:
    with right_col:
        right_config = config_picker("Right", "hierarchical")

# The current selection; results are shown only if they belong to it
current_request = {
    "message": (message or "").strip(),
    "left": left_config,
    "right": right_config,
}

# 3. Run
button_label = "Run both" if compare else "Run"
if compare:
    st.caption("Compare runs the ticket twice, so it uses about 2x API cost and time.")

if st.button(button_label, type="primary"):
    if len(current_request["message"]) < 3:
        st.warning("Type a ticket message first (at least 3 characters).")
    else:
        with st.spinner("Agents are working on the ticket..."):
            try:
                if compare:
                    data = compare_tickets(current_request["message"], left_config, right_config)
                    left_result, right_result = data["left"], data["right"]
                else:
                    left_result = run_ticket(current_request["message"], include_logs=True, **left_config)
                    right_result = None
                st.session_state.lab_results = {
                    "request": current_request,
                    "left": left_result,
                    "right": right_result,
                }
            except BackendError as error:
                st.error(str(error))

# 4. Results
results = st.session_state.get("lab_results")
if results and results["request"] == current_request:
    st.divider()
    if results["right"]:
        show_comparison(results["left"], results["right"])
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            show_result("Left", results["left"], current_request["left"])
        with col2:
            show_result("Right", results["right"], current_request["right"])
    else:
        show_result("Result", results["left"], current_request["left"])
elif results:
    st.info("Settings changed. Click Run to see results for the new selection.")