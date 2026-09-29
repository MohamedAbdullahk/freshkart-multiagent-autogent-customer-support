import streamlit as st

from api_client import run_ticket, BackendError
from ui_helpers import is_dev_mode, render_metrics, render_guardrail, render_timeline

FALLBACK_ANSWER = "Sorry, we could not complete your request right now. Please try again in a moment."

dev_mode = is_dev_mode()

st.title("How can we help you?")
st.caption("Ask about orders, payments, login, or delivery.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    if st.button("New conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# Show previous messages
for entry in st.session_state.chat_history:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])
        details = entry.get("details")
        if dev_mode and details:
            with st.expander("Behind the scenes (developer only)"):
                render_metrics(details)
                render_guardrail(details)
                render_timeline(details)

# New message
message = st.chat_input("Type your message")
if message:
    st.session_state.chat_history.append({"role": "user", "content": message})

    with st.chat_message("user"):
        st.markdown(message)

    with st.chat_message("assistant"):
        with st.spinner("Our support team is checking this for you..."):
            try:
                # Customer page always uses the recommended setup
                result = run_ticket(message, include_logs=dev_mode)
                answer = result.get("final_response") or FALLBACK_ANSWER
            except BackendError as error:
                result = None
                # Customers see a friendly message; developers also see the technical reason
                answer = f"{FALLBACK_ANSWER}\n\n`{error}`" if dev_mode else FALLBACK_ANSWER

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "details": result if (dev_mode and result and "metrics" in result) else None,
    })
    st.rerun()