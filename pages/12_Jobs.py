import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.job_service import JobService

st.title("⚡ Background Jobs Monitor")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Jobs for: {project.title}")
    jobs = JobService.list_project_jobs(db, project_id)

    if not jobs:
        st.info("No active or past generation jobs for this project.")
    else:
        for j in jobs:
            st.markdown(f"**Job ID:** `{j.id}` | **Type:** {j.type} | **Status:** `{j.status}` | **Progress:** {int(j.progress*100)}%")
            if j.error:
                st.error(f"Error: {j.error}")
finally:
    db.close()
