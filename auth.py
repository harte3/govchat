import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str) -> str:
    """Load from Streamlit secrets (production) with .env fallback (local dev)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "")


def check_password():
    """Block access until the user enters the correct org password.
    If APP_PASSWORD is not configured, the gate is skipped entirely."""
    app_password = get_secret("APP_PASSWORD")

    if not app_password:
        return  # No password set — open access

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
            if pwd == app_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
    st.stop()
