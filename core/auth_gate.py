import streamlit as st
from core.config import settings

def require_auth() -> bool:
    """Checks if password protection is enabled via STUDIO_PASSWORD or st.secrets.
    
    If STUDIO_PASSWORD is set and user is not authenticated, renders a clean login gate.
    If STUDIO_PASSWORD is not set (local dev), automatically allows access.
    """
    configured_pwd = settings.STUDIO_PASSWORD
    if not configured_pwd:
        return True

    if st.session_state.get("studio_authenticated") is True:
        return True

    st.markdown("""
        <div style="text-align: center; margin-top: 50px; margin-bottom: 20px;">
            <h2>🔒 MicroDrama Studio Access Gate</h2>
            <p style="color: #8E8E93;">This studio instance is protected. Enter your studio password to continue.</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("studio_login_form"):
            entered_pwd = st.text_input("Studio Access Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("🔓 Unlock Studio", use_container_width=True, type="primary")

            if submit:
                if entered_pwd == configured_pwd:
                    st.session_state["studio_authenticated"] = True
                    st.success("Access Granted! Loading studio...")
                    st.rerun()
                else:
                    st.error("Incorrect password. Access denied.")

    return False
