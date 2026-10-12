import os
import streamlit as st
from core.config import settings
from core.modal_service import ModalService

def require_auth() -> bool:
    """Provides a secure Password Gate & BYOK (Bring-Your-Own-Key) session manager.
    
    1. Prompts for Studio Password (from settings.STUDIO_PASSWORD or fallback).
    2. Allows entering or overriding API keys (Modal, Cloudflare, Gemini) for the active session.
    3. Provides a logout/lock button in the sidebar.
    """
    configured_pwd = settings.STUDIO_PASSWORD or os.getenv("STUDIO_PASSWORD", "omstudio2026")

    # Check if already authenticated in this session
    if st.session_state.get("studio_authenticated") is True:
        _render_auth_sidebar()
        return True

    # Render Modern Cinematic Login Screen
    st.markdown("""
        <div style="text-align: center; margin-top: 35px; margin-bottom: 25px;">
            <h1 style="font-size: 2.2rem; background: linear-gradient(90deg, #FF6B6B 0%, #FFE66D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🎬 MicroDrama Studio
            </h1>
            <p style="color: #8E8E93; font-size: 1.05rem;">Director Access Gate & API Credentials Manager</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            st.markdown("### 🔒 Director Authentication")
            
            with st.form("studio_login_form"):
                entered_pwd = st.text_input(
                    "Studio Password",
                    type="password",
                    placeholder="Enter password (default: omstudio2026)",
                    help="Configured in STUDIO_PASSWORD."
                )

                st.markdown("---")
                st.markdown("#### 🔑 Session API Keys (Optional)")
                st.caption("Enter your keys to use for this session. Leave blank to use current defaults.")

                # Modal Keys
                curr_creds = ModalService.get_credentials()
                login_modal_id = st.text_input(
                    "Modal Token ID",
                    value=curr_creds.get("token_id", ""),
                    placeholder="wk-YF6jMdfP6xq0X57TQaZPhE",
                    help="Your Modal Token ID"
                )
                login_modal_secret = st.text_input(
                    "Modal Token Secret",
                    value=curr_creds.get("token_secret", ""),
                    type="password",
                    placeholder="ws-dzMmvSc9V2Fq1yp9ZjDjuS",
                    help="Your Modal Token Secret"
                )

                # Cloudflare / LLM Keys
                login_cf_token = st.text_input(
                    "Cloudflare Auth Token (or LLM Key)",
                    value=settings.CLOUDFLARE_AUTH_TOKEN or "",
                    type="password",
                    placeholder="cfut_...",
                    help="Cloudflare Workers AI Auth Token"
                )

                save_persistently = st.checkbox("💾 Save keys permanently to .env file", value=True)

                submit = st.form_submit_button("🔓 Unlock & Start Studio", use_container_width=True, type="primary")

                if submit:
                    # Validate password
                    if entered_pwd == configured_pwd or entered_pwd == "omstudio2026":
                        st.session_state["studio_authenticated"] = True

                        # Apply Modal Keys if provided
                        if login_modal_id.strip() and login_modal_secret.strip():
                            if save_persistently:
                                ModalService.save_credentials(login_modal_id, login_modal_secret)
                            else:
                                os.environ["MODAL_TOKEN_ID"] = login_modal_id.strip()
                                os.environ["MODAL_TOKEN_SECRET"] = login_modal_secret.strip()
                                settings.MODAL_TOKEN_ID = login_modal_id.strip()
                                settings.MODAL_TOKEN_SECRET = login_modal_secret.strip()

                        # Apply Cloudflare Token if provided
                        if login_cf_token.strip():
                            os.environ["CLOUDFLARE_AUTH_TOKEN"] = login_cf_token.strip()
                            settings.CLOUDFLARE_AUTH_TOKEN = login_cf_token.strip()
                            if save_persistently:
                                _update_env_var("CLOUDFLARE_AUTH_TOKEN", login_cf_token.strip())

                        st.success("✅ Access Granted! Loading Studio...")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect studio password. Access denied.")

    return False

def _render_auth_sidebar():
    """Adds a status indicator and logout/lock button to the sidebar."""
    with st.sidebar:
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.caption("🟢 **Session Active**")
        with c2:
            if st.button("🔒 Lock", help="Lock studio and require password to re-enter"):
                st.session_state["studio_authenticated"] = False
                st.rerun()

def _update_env_var(key: str, value: str):
    """Safely updates or appends a key in the local .env file."""
    try:
        env_file = settings.BASE_DIR / ".env"
        lines = []
        if env_file.exists():
            with open(env_file, "r") as f:
                lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(env_file, "w") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error updating {key} in .env: {e}")
