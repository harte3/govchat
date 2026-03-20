import streamlit as st
import anthropic
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAM.gov AI Assistant",
    page_icon="🏛️",
    layout="wide",
)

# ── Secrets helper ────────────────────────────────────────────────────────────
def get_secret(key: str) -> str:
    """Load from Streamlit secrets (production) with .env fallback (local dev)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")

SAM_API_KEY       = get_secret("SAM_API_KEY")
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
APP_PASSWORD      = get_secret("APP_PASSWORD")

# ── Password gate ─────────────────────────────────────────────────────────────
def check_password():
    """Block access until the user enters the correct org password."""
    if not APP_PASSWORD:
        # No password configured — skip gate (useful during initial setup)
        return

    if st.session_state.get("authenticated"):
        return

    st.markdown("""
    <div style="max-width:400px; margin:10vh auto; text-align:center;">
        <h1>🏛️ SAM.gov AI Assistant</h1>
        <p style="color:#666;">Enter your organization password to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("Organization Password", type="password",
                            label_visibility="collapsed", placeholder="Enter password…")
        if st.button("Login", use_container_width=True, type="primary"):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
    st.stop()

check_password()

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
    st.caption("**APIs used:**\n- SAM.gov Opportunities v2\n- SAM.gov Contract Awards v1\n\n**Rate limits:** 10 req/day (public), 1,000/day (registered)")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Startup check ─────────────────────────────────────────────────────────────
if not SAM_API_KEY or not ANTHROPIC_API_KEY:
    st.error(
        "⚠️ **Missing API keys.** "
        "Add `SAM_API_KEY` and `ANTHROPIC_API_KEY` to your Streamlit secrets "
        "(or a local `.env` file for development).",
        icon="🔑",
    )
    st.stop()

# ── SAM.gov API helpers ───────────────────────────────────────────────────────

def search_opportunities(
    api_key: str,
    keyword: str = None,
    title: str = None,
    ptype: str = None,
    department: str = None,
    naics_code: str = None,
    set_aside: str = None,
    posted_from: str = None,
    posted_to: str = None,
    limit: int = 10,
    state: str = None,
) -> dict:
    """Search SAM.gov contract opportunities."""
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"

    if not posted_from:
        posted_from = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    if not posted_to:
        posted_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "limit": min(limit, 25),
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    if keyword:
        params["title"] = keyword
    if title:
        params["title"] = title
    if ptype:
        params["ptype"] = ptype
    if department:
        params["deptname"] = department
    if naics_code:
        params["naicsCode"] = naics_code
    if set_aside:
        params["typeOfSetAsideDescription"] = set_aside
    if state:
        params["placeOfPerformanceState"] = state

    try:
        response = requests.get(base_url, params=params, timeout=20)
        data = response.json()

        if response.status_code != 200:
            return {"error": f"API error {response.status_code}: {data.get('errorMessage', str(data))}"}

        opportunities = data.get("opportunitiesData", [])
        results = []
        for opp in opportunities:
            contacts = opp.get("pointOfContact", [])
            contact_email = contacts[0].get("email", "N/A") if contacts else "N/A"
            results.append({
                "title": opp.get("title", "N/A"),
                "solicitation_number": opp.get("solicitationNumber", "N/A"),
                "department": opp.get("department", "N/A"),
                "agency": opp.get("subtierName", opp.get("subTier", "N/A")),
                "type": opp.get("type", "N/A"),
                "naics_code": opp.get("naicsCode", "N/A"),
                "set_aside": opp.get("typeOfSetAsideDescription", "N/A"),
                "posted_date": opp.get("postedDate", "N/A"),
                "response_deadline": opp.get("responseDeadLine", "N/A"),
                "active": opp.get("active", "N/A"),
                "contact_email": contact_email,
                "ui_link": opp.get("uiLink", ""),
            })

        return {
            "total_records": data.get("totalRecords", len(results)),
            "returned": len(results),
            "date_range": f"{posted_from} to {posted_to}",
            "opportunities": results,
        }
    except Exception as e:
        return {"error": str(e)}


def search_contract_awards(
    api_key: str,
    naics_code: str = None,
    department_code: str = None,
    state: str = None,
    last_modified_from: str = None,
    limit: int = 10,
) -> dict:
    """Search SAM.gov contract awards."""
    base_url = "https://api.sam.gov/contract-awards/v1/search"

    if not last_modified_from:
        last_modified_from = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    last_modified_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "lastModifiedDate": f"[{last_modified_from},{last_modified_to}]",
        "limit": min(limit, 25),
    }
    if naics_code:
        params["naicsCode"] = naics_code
    if department_code:
        params["contractingDepartmentCode"] = department_code
    if state:
        params["placeOfPerformanceState"] = state

    try:
        response = requests.get(base_url, params=params, timeout=20)
        if response.status_code != 200:
            return {"error": f"API error {response.status_code}: {response.text[:300]}"}
        data = response.json()
        return {"awards": data, "date_range": f"{last_modified_from} to {last_modified_to}"}
    except Exception as e:
        return {"error": str(e)}


def get_today_date() -> dict:
    """Returns today's date for use in API queries."""
    today = datetime.now()
    return {
        "today": today.strftime("%m/%d/%Y"),
        "thirty_days_ago": (today - timedelta(days=30)).strftime("%m/%d/%Y"),
        "seven_days_ago":  (today - timedelta(days=7)).strftime("%m/%d/%Y"),
    }

# ── Claude tool definitions ───────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_today_date",
        "description": "Get today's date and common relative dates (7 days ago, 30 days ago). Use this before building date-based queries.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search_opportunities",
        "description": (
            "Search SAM.gov for federal contract opportunities (solicitations, awards, etc.). "
            "Use this when the user asks about open bids, RFPs, RFQs, solicitations, or contract opportunities. "
            "Dates must be in MM/DD/YYYY format."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword":     {"type": "string", "description": "Keyword to search in opportunity titles"},
                "ptype":       {"type": "string", "description": "Notice type: 'o'=solicitation, 'p'=presolicitation, 'a'=award notice, 'r'=sources sought, 'k'=special notice"},
                "department":  {"type": "string", "description": "Department name (e.g. 'Department of Defense', 'NASA')"},
                "naics_code":  {"type": "string", "description": "NAICS code (e.g. '541512')"},
                "set_aside":   {"type": "string", "description": "Set-aside type, e.g. 'Small Business', '8(a)', 'HUBZone', 'WOSB'"},
                "posted_from": {"type": "string", "description": "Start date MM/DD/YYYY"},
                "posted_to":   {"type": "string", "description": "End date MM/DD/YYYY"},
                "limit":       {"type": "integer", "description": "Max results (1-25)", "default": 10},
                "state":       {"type": "string", "description": "2-letter state code (e.g. 'VA', 'CA')"},
            },
            "required": [],
        },
    },
    {
        "name": "search_contract_awards",
        "description": "Search SAM.gov for awarded contracts. Use when the user asks about who won contracts, award amounts, or past awards.",
        "input_schema": {
            "type": "object",
            "properties": {
                "naics_code":         {"type": "string", "description": "NAICS code filter"},
                "department_code":    {"type": "string", "description": "Contracting department code, e.g. '9700' for DoD"},
                "state":              {"type": "string", "description": "2-letter state code for place of performance"},
                "last_modified_from": {"type": "string", "description": "Start date MM/DD/YYYY"},
                "limit":              {"type": "integer", "description": "Max results (1-25)", "default": 10},
            },
            "required": [],
        },
    },
]

SYSTEM_PROMPT = """You are a helpful SAM.gov research assistant. You help users find federal contract opportunities, award data, and vendor information from SAM.gov.

When a user asks a question:
1. Use get_today_date first if the question involves recent or current data.
2. Choose the right tool: search_opportunities for open solicitations/RFPs, search_contract_awards for awarded contracts.
3. Summarize results clearly. Present key details like titles, agencies, deadlines, and solicitation numbers.
4. If no results are found, explain why and suggest alternative search terms or date ranges.
5. Always mention the total number of results found and the date range searched.
6. Format opportunity lists using markdown with bold titles and bullet points for details.
7. Be specific and factual — only report what the API actually returned.

Common NAICS codes:
- 541512: Computer Systems Design
- 541511: Custom Computer Programming
- 541519: Other Computer Related Services
- 541330: Engineering Services
- 541690: Other Scientific/Technical Consulting
- 336411: Aircraft Manufacturing

Common ptype codes:
- o = Solicitation (RFP, RFQ, IFB)
- p = Presolicitation
- a = Award Notice
- r = Sources Sought
- k = Special Notice
"""

# ── Agentic loop ──────────────────────────────────────────────────────────────

def run_agent(user_message: str):
    """Run agentic loop — keys come from secrets, not the UI."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": user_message}]
    status_placeholder = st.empty()
    result_text = ""

    for _ in range(6):
        status_placeholder.info("🤔 Thinking…")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_calls, text_blocks = [], []
        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        result_text = "\n".join(text_blocks)

        if response.stop_reason == "end_turn" or not tool_calls:
            status_placeholder.empty()
            break

        tool_results = []
        for tc in tool_calls:
            status_placeholder.info(f"🔍 Querying SAM.gov — `{tc.name}`…")
            with st.expander(f"🔧 Tool call: `{tc.name}`", expanded=False):
                st.json(tc.input)

            if tc.name == "get_today_date":
                output = get_today_date()
            elif tc.name == "search_opportunities":
                output = search_opportunities(api_key=SAM_API_KEY, **tc.input)
            elif tc.name == "search_contract_awards":
                output = search_contract_awards(api_key=SAM_API_KEY, **tc.input)
            else:
                output = {"error": f"Unknown tool: {tc.name}"}

            with st.expander(f"📦 Result: `{tc.name}`", expanded=False):
                st.json(output)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(output),
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    status_placeholder.empty()
    return result_text or "I wasn't able to find relevant results. Please try rephrasing your question."

# ── Chat UI ───────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")
else:
    user_input = st.chat_input("Ask about federal contracts, opportunities, or awards…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        answer = run_agent(user_input)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
