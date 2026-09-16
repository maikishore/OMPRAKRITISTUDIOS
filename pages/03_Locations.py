import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.location_service import LocationService
from core.enums import ProjectStatus
from ai.location_engine import LocationEngine
from schemas.location import LocationCreate, LocationUpdate

st.set_page_config(page_title="03 Locations | MicroDrama Studio", page_icon="🏛️", layout="wide")

st.title("🏛️ 03. Location Bible & Environments")
st.caption("AI Location Extraction, Architectural Design, Materials & Lighting Atmosphere")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("⚠️ Please select a project from the sidebar first.")
    st.stop()

db = ScopedSession()
engine = LocationEngine()

try:
    project = ProjectService.get_project(db, project_id)
    if not project:
        st.error("Project not found.")
        st.stop()

    locations = LocationService.list_project_locations(db, project_id)

    # Top Control Bar
    top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
    with top_col1:
        st.subheader(f"🎬 Project: {project.title}")
        st.caption(f"Project Status: **{project.status}** | Locations: **{len(locations)} Defined**")
    with top_col2:
        all_approved = len(locations) > 0 and all(l.is_approved for l in locations)
        st.metric("Locations Status", "✅ APPROVED" if all_approved else "📝 IN PROGRESS")
    with top_col3:
        if all_approved:
            st.success("All Location Bibles Approved.")
        else:
            st.info("Review locations & click 'Approve All' when ready.")

    st.markdown("---")

    # Generation Trigger Bar
    gen_col1, gen_col2, gen_col3 = st.columns([2, 1, 1])
    with gen_col1:
        st.write("**AI Extraction:** Extract core staging environments from your story using Gemma 4 (26B).")
    with gen_col2:
        generate_clicked = st.button("✨ Generate with Gemma 4", type="primary", use_container_width=True)
    with gen_col3:
        seed_clicked = st.button("🌱 Load 'After Closing' Environments", use_container_width=True)

    if generate_clicked:
        with st.spinner("Extracting environments with Gemma 4..."):
            extracted = engine.generate_locations_from_story(project)
            for loc_data in extracted:
                LocationService.create_location(db, loc_data)
            st.success(f"Generated {len(extracted)} locations from story!")
            st.rerun()

    if seed_clicked:
        seed_locs = engine._get_fallback_locations(project.id)
        for loc_data in seed_locs:
            LocationService.create_location(db, loc_data)
        st.success("Loaded 'After Closing' 5 core environments!")
        st.rerun()

    # Location Cards
    if locations:
        st.markdown("### 🏢 Key Staging Environments")

        for idx, loc in enumerate(locations):
            with st.expander(f"🏛️ {loc.name} {'✅ Approved' if loc.is_approved else '⏳ Draft'}", expanded=(idx==0)):
                with st.form(f"loc_form_{loc.id}"):
                    l1, l2 = st.columns(2)
                    with l1:
                        l_name = st.text_input("Name", value=loc.name, key=f"loc_n_{loc.id}")
                        l_time = st.text_input("Time of Day / Atmosphere", value=loc.time_of_day or "Night / After Closing", key=f"loc_t_{loc.id}")
                    with l2:
                        l_desc = st.text_area("Spatial Description", value=loc.description or "", height=80, key=f"loc_d_{loc.id}")

                    c_arch, c_mat = st.columns(2)
                    with c_arch:
                        l_arch = st.text_area("Architecture & Layout", value=loc.architecture or "", height=70, key=f"loc_a_{loc.id}")
                    with c_mat:
                        l_mat = st.text_area("Materials & Textures", value=loc.materials or "", height=70, key=f"loc_m_{loc.id}")

                    l_light = st.text_area("Lighting Atmosphere", value=loc.lighting or "", height=70, key=f"loc_l_{loc.id}")
                    l_continuity = st.text_area("Continuity Constraints (one per line)", value="\n".join(loc.continuity_constraints or []), height=70, key=f"loc_c_{loc.id}")

                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        save_loc = st.form_submit_button("💾 Save Location")
                    with b_col2:
                        delete_loc = st.form_submit_button("🗑️ Delete Location")

                    if save_loc:
                        LocationService.update_location(
                            db,
                            loc.id,
                            LocationUpdate(
                                name=l_name,
                                time_of_day=l_time,
                                description=l_desc,
                                architecture=l_arch,
                                materials=l_mat,
                                lighting=l_light,
                                continuity_constraints=[c.strip() for c in l_continuity.split("\n") if c.strip()]
                            )
                        )
                        st.success(f"Updated {l_name}!")
                        st.rerun()

                    if delete_loc:
                        LocationService.delete_location(db, loc.id)
                        st.warning(f"Deleted {loc.name}")
                        st.rerun()

        # Approval Gate
        st.markdown("---")
        app_col1, app_col2 = st.columns([2, 1])
        with app_col1:
            st.write("Ready to lock location bibles? Approving locks environmental architecture and lighting for scene generation.")
        with app_col2:
            if st.button("✅ APPROVE All Locations", type="primary", use_container_width=True):
                LocationService.approve_all_locations(db, project.id)
                st.success("🎉 All locations approved! Project status updated to LOCATIONS_READY.")
                st.rerun()

    else:
        st.info("No locations generated yet. Click **'Generate with Gemma 4'** or **'Load Environments'** to create your location bible.")

    # Manual Addition
    with st.expander("➕ Manually Add Location"):
        with st.form("add_loc_form"):
            new_name = st.text_input("Name", placeholder="e.g. Central Mall Atrium")
            new_desc = st.text_area("Description", placeholder="Spatial summary...")
            new_arch = st.text_area("Architecture", placeholder="Brutalist glass atrium...")
            new_light = st.text_area("Lighting", placeholder="Overcast moonlight and fluorescent cyan...")
            add_loc_btn = st.form_submit_button("Add Location")

            if add_loc_btn and new_name.strip():
                LocationService.create_location(
                    db,
                    LocationCreate(
                        project_id=project.id,
                        name=new_name.strip(),
                        description=new_desc.strip() if new_desc else None,
                        architecture=new_arch.strip() if new_arch else None,
                        lighting=new_light.strip() if new_light else None
                    )
                )
                st.success(f"Added {new_name}!")
                st.rerun()

finally:
    db.close()
