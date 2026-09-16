import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.config import settings

st.title("⚙️ Studio Settings & Configurations")

st.subheader("Cloud & Model Providers")
st.text_input("Database URL", value=settings.DATABASE_URL, disabled=True)
st.text_input("Media Storage Root", value=str(settings.STORAGE_ROOT), disabled=True)
st.text_input("LLM Provider", value=settings.LLM_PROVIDER)
st.text_input("LLM Model", value=settings.LLM_MODEL)

st.markdown("---")
st.subheader("Modal & Cloud GPU Cluster")
st.text_input("Modal App Name", value=settings.MODAL_APP_NAME)
st.text_input("Modal Environment", value=settings.MODAL_ENVIRONMENT)

st.success("Settings loaded from `.env`. In production, you can switch the Database URL to Supabase PostgreSQL.")
