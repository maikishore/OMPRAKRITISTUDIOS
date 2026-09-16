import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService

st.title("🎨 04. Visual Style & Cinematic Rules")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Project: {project.title}")
    st.info("Phase 2 implementation will provide camera language, lens preferences, lighting progression, and color palettes.")
finally:
    db.close()
