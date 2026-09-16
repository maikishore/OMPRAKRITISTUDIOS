import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService

st.title("🎞️ 10. Final Assembly & Movie Compiler")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Project: {project.title}")
    st.info("Phase 7 implementation will provide shot reordering, audio muxing, FFmpeg assembly, and master MP4 export.")
finally:
    db.close()
