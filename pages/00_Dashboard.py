import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.asset_service import AssetService
from core.job_service import JobService

st.title("📊 Project Dashboard")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    if not project:
        st.error("Selected project not found.")
        st.stop()

    st.subheader(f"🎬 {project.title}")
    st.caption(f"Genre: {project.genre} | Status: {project.status} | Target: {project.target_duration_seconds // 60} minutes")
    if project.logline:
        st.info(f"**Logline:** {project.logline}")

    col1, col2, col3, col4 = st.columns(4)
    char_count = len(project.characters)
    loc_count = len(project.locations)
    scene_count = len(project.scenes)
    shot_count = sum(len(s.shots) for s in project.scenes)

    col1.metric("Characters", f"{char_count}")
    col2.metric("Locations", f"{loc_count}")
    col3.metric("Scenes", f"{scene_count}")
    col4.metric("Total Shots", f"{shot_count}")

    st.markdown("---")
    st.markdown("### 📈 Production Pipeline Progress")
    
    # Check completeness of each phase
    story_ok = bool(project.story and project.story.is_approved)
    chars_ok = char_count > 0 and all(c.is_approved for c in project.characters)
    locs_ok = loc_count > 0 and all(l.is_approved for l in project.locations)
    style_ok = bool(project.visual_style and project.visual_style.is_approved)
    scenes_ok = scene_count > 0 and all(s.is_approved for s in project.scenes)

    steps = [
        ("01 Story", story_ok),
        ("02 Characters", chars_ok),
        ("03 Locations", locs_ok),
        ("04 Visual Style", style_ok),
        ("05 Scenes", scenes_ok),
        ("06 Shots", shot_count > 0),
        ("07 Keyframes", False),
        ("08 Videos", False),
        ("09 Review", False),
        ("10 Final Assembly", False),
    ]

    prog_cols = st.columns(5)
    for idx, (label, is_done) in enumerate(steps):
        with prog_cols[idx % 5]:
            icon = "✅" if is_done else "⏳"
            st.markdown(f"**{label}**<br>{icon} {'Completed' if is_done else 'Pending'}", unsafe_allow_html=True)
finally:
    db.close()
