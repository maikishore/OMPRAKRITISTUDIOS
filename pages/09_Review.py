import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService

st.title("⚖️ 09. Review & Regeneration")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Project: {project.title}")
    st.info("Phase 6 implementation will provide clip review, rejection reasons feedback loops, and prompt versioning.")
finally:
    db.close()
