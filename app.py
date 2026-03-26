import streamlit as st

from auth import check_password, get_secret
from agent import run_agent

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAM.gov AI Assistant",
    page_icon="🏛️",
    layout="wide",
)

# ── Auth gate (must run before any other UI) ──────────────────────────────────
check_password()

# ── Load secrets ──────────────────────────────────────────────────────────────
SAM_API_KEY       = get_secret("SAM_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")

if not SAM_API_KEY or not ANTHROPIC_API_KEY:
    st.error(
        "⚠️ **Missing API keys.** "
        "Add `SAM_API_KEY` and `ANTHROPIC_API_KEY` to your Streamlit secrets "
        "(or a local `.env` file for development).",
        icon="🔑",
    )
    st.stop()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }
    .main-header {
        background: linear-gradient(135deg, #1a3a6b 0%, #2e6da4 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 1.8rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }
    div[data-testid="stChatMessage"] { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏛️ SAM.gov AI Assistant</h1>
    <p>Ask me about federal contract opportunities, award data, or vendor registrations on SAM.gov</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("💡 Example Questions")
    examples = [
        "Find IT software opportunities posted this week",
        "Show me DoD solicitations closing soon",
        "Search for small business set-aside contracts in Virginia",
        "Find opportunities with NAICS code 541512",
        "Show recent award notices from NASA",
        "What opportunities are available for cybersecurity?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state["pending_input"] = ex

    st.divider()
    st.caption(
        "**APIs used:**\n"
        "- SAM.gov Opportunities v2\n"
        "- SAM.gov Contract Awards v1\n\n"
        "**Rate limits:** 10 req/day (public), 1,000/day (registered)"
    )
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")
else:
    user_input = st.chat_input("Ask about federal contracts, opportunities, or awards…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            answer = run_agent(user_input, SAM_API_KEY, ANTHROPIC_API_KEY)
        except Exception as e:
            answer = f"⚠️ Something went wrong: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
