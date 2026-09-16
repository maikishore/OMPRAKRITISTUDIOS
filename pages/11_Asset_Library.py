import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import get_db_session
from core.project_service import ProjectService
from core.asset_service import AssetService

st.set_page_config(page_title="Asset Library | MicroDrama Studio", page_icon="🗄️", layout="wide")

st.title("🗄️ Project Asset Library")
st.caption("Central repository of all generated Master Character References, Concept Locations, Shot Keyframes, and Video Clips.")

with get_db_session() as db:
    projects = ProjectService.list_projects(db)
    if not projects:
        st.warning("No projects found.")
        st.stop()

    current_pid = st.session_state.get("current_project_id")
    project_ids = [p.id for p in projects]
    default_idx = project_ids.index(current_pid) if current_pid in project_ids else 0

    project_options = {p.id: f"{p.title} ({p.genre})" for p in projects}
    selected_id = st.sidebar.selectbox("Active Project", options=project_ids, index=default_idx, format_func=lambda x: project_options[x])
    st.session_state["current_project_id"] = selected_id
    project = ProjectService.get_project(db, selected_id)

    assets = AssetService.list_assets_by_project(db, project.id)

    if not assets:
        st.info("No generated assets found in this project. Generate images on Page 07 Images.")
    else:
        st.subheader(f"Assets for {project.title} ({len(assets)} items)")
        cols = st.columns(3)
        for idx, asset in enumerate(assets):
            col = cols[idx % 3]
            with col:
                if Path(asset.file_path).exists():
                    st.image(asset.file_path, use_container_width=True)
                    st.markdown(f"**{asset.type.upper()}** (`{asset.id[:8]}`)")
                    st.caption(f"Model: {asset.model} | Approved: {'✅' if asset.is_approved else '❌'}")
                    act_col1, act_col2 = st.columns([2, 1])
                    with act_col1:
                        with open(asset.file_path, "rb") as file:
                            st.download_button(
                                label="⬇️ Download",
                                data=file,
                                file_name=Path(asset.file_path).name,
                                mime=asset.mime_type,
                                key=f"dl_{asset.id}",
                                use_container_width=True
                            )
                    with act_col2:
                        if st.button("🗑️ Delete", key=f"del_lib_{asset.id}", use_container_width=True):
                            AssetService.delete_asset(db, asset.id)
                            st.success(f"Deleted `{asset.id[:8]}`")
                            st.rerun()
                else:
                    st.warning(f"File missing on disk: `{asset.file_path}`")
                    if st.button("🗑️ Clean Record", key=f"del_lib_orphan_{asset.id}"):
                        AssetService.delete_asset(db, asset.id)
                        st.rerun()
