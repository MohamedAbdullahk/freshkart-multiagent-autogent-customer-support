import streamlit as st

from ui_helpers import cached_health

st.set_page_config(page_title="FreshKart Support", page_icon="🛒", layout="wide")

with st.sidebar:
    st.header("🛒 FreshKart")
    st.radio("View as", ["Customer", "Developer"], key="view_as", horizontal=True)
    if cached_health():
        st.caption("🟢 Backend connected")
    else:
        st.caption("🔴 Backend offline. Start FastAPI on port 8000.")

customer_page = st.Page("views/customer_support.py", title="Customer support", icon="💬", default=True)
lab_page = st.Page("views/agent_lab.py", title="Agent lab", icon="🧪")

# Customer view shows only the support page; developer view also shows the Agent lab
pages = [customer_page]
if st.session_state.view_as == "Developer":
    pages.append(lab_page)

st.navigation(pages).run()