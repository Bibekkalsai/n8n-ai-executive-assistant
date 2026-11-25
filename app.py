import os
import uuid
import requests
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="AI Executive Assistant",
    page_icon="⚡",
    layout="wide",
)

# --- Helper to Load Secrets Safely ---
def get_secret(key: str, default: str = "") -> str:
    if os.getenv(key):
        return os.getenv(key, default)
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

# --- Session State Init ---
if "session_id" not in st.session_state:
    st.session_state.session_id = f"bibek-session-{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# --- Sidebar: Connection & Controls ---
with st.sidebar:
    st.title("⚙️ Agent Controls")
    webhook_url = st.text_input(
        "n8n Webhook URL",
        value=get_secret("N8N_WEBHOOK_URL", ""),
        placeholder="https://your-instance.app.n8n.cloud/webhook/...",
        type="password",
        help="Loaded automatically from Streamlit Secrets, or paste your Production POST URL here.",
    )
    api_key = st.text_input(
        "Webhook API Key (Header Auth)",
        value=get_secret("N8N_API_KEY", ""),
        placeholder="Optional X-API-Key secret",
        type="password",
    )
    st.caption(f"**Session ID:** `{st.session_state.session_id}`")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Session", use_container_width=True):
            st.session_state.session_id = f"bibek-session-{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.divider()
    st.markdown(
        "**Connected Stack:**\n"
        "- 🔍 SerpApi Live Search\n"
        "- 📅 Google Calendar\n"
        "- 📧 Gmail (Search, Read, Send)\n"
        "- ✅ Google Tasks\n"
        "- 📊 Google Sheets + Calculator\n"
        "- 📝 Google Docs"
    )

# --- Header & Capability Showcase ---
st.title("⚡ Personal AI Executive Assistant")
st.caption("Powered by n8n • Gemini • Google Workspace • SerpApi")

capabilities = [
    {
        "icon": "📊",
        "title": "Expense Tracker",
        "desc": "Log INR expenses to Google Sheets & compute monthly category totals.",
        "prompt": "Log an expense of 150 rupees for lunch today, then check my November 2026 spending summary.",
    },
    {
        "icon": "📅",
        "title": "Smart Calendar",
        "desc": "Check free slots and schedule events in IST (+05:30).",
        "prompt": "Check my schedule for tomorrow and book a 1-hour 'System Design Study' block at 5 PM if I'm free.",
    },
    {
        "icon": "📧",
        "title": "Gmail Triage",
        "desc": "Search inbox threads, read full email bodies, and send updates.",
        "prompt": "Find my latest email from GitHub or Google and summarize its full contents.",
    },
    {
        "icon": "✅",
        "title": "Task Manager",
        "desc": "Create, list, and clean up action items in Google Tasks.",
        "prompt": "Add a task 'Review n8n workflow logs' due tomorrow and show all my active tasks.",
    },
    {
        "icon": "📝",
        "title": "Google Docs Briefs",
        "desc": "Draft, read, and append structured reports in Google Docs.",
        "prompt": "Create a Google Doc titled 'Weekly Action Plan' with 3 priority milestones for this week.",
    },
    {
        "icon": "🔍",
        "title": "Live Web Research",
        "desc": "Pull real-time search results and citations via SerpApi.",
        "prompt": "Search the web for the latest GATE 2027 exam dates and official organizing institute.",
    },
]

# Render 3x2 Capability Cards
for row_start in range(0, len(capabilities), 3):
    cols = st.columns(3)
    for idx, cap in enumerate(capabilities[row_start : row_start + 3]):
        with cols[idx]:
            with st.container(border=True):
                st.subheader(f"{cap['icon']} {cap['title']}")
                st.write(cap["desc"])
                if st.button(f"Try {cap['title']}", key=f"btn_{row_start+idx}", use_container_width=True):
                    st.session_state.pending_prompt = cap["prompt"]

st.divider()

# --- Helper to Call n8n Webhook ---
def query_agent(user_text: str) -> str:
    if not webhook_url:
        return "⚠️ Please configure `N8N_WEBHOOK_URL` in Streamlit Secrets or paste it in the sidebar."
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        resp = requests.post(
            webhook_url,
            json={"query": user_text, "sessionId": st.session_state.session_id},
            headers=headers,
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        # Handles standard n8n 'Respond to Webhook' shapes
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        if isinstance(data, dict):
            return (
                data.get("output")
                or data.get("text")
                or data.get("response")
                or str(data)
            )
        return str(data)
    except requests.exceptions.RequestException as e:
        return f"❌ Webhook connection error: {e}"

# --- Render Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle Input (Either from Quick-Action Button or Chat Box) ---
chat_input = st.chat_input("Ask your assistant to manage emails, tasks, calendar, expenses, docs, or search...")
active_prompt = st.session_state.pending_prompt or chat_input
st.session_state.pending_prompt = None

if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Executing workflow..."):
            reply = query_agent(active_prompt)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})