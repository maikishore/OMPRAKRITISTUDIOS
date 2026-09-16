import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.asset_service import AssetService

st.title("🗄️ Asset Library")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("Please select a project from the sidebar.")
    st.stop()

db = ScopedSession()
try:
    project = ProjectService.get_project(db, project_id)
    st.subheader(f"Assets for: {project.title}")
    assets = AssetService.list_project_assets(db, project_id)

    if not assets:
        st.info("No generated or uploaded assets found for this project yet.")
    else:
        st.write(f"Total Assets: {len(assets)}")
        for a in assets:
            st.markdown(f"- **{a.type}** (`{a.mime_type}`) - {a.file_path} (Approved: {a.is_approved})")
finally:
    db.close()
