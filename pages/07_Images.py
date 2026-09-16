import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService

st.title("🖼️ 07. Keyframe Generation (FLUX / Qwen)")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Project: {project.title}")
    st.info("Phase 4 implementation will provide async Modal FLUX/Qwen image generation, multi-reference conditioning, and keyframe approvals.")
finally:
    db.close()
