import sys
from pathlib import Path

# Ensure OMVERSION root is in Python sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import init_db, ScopedSession
from core.project_service import ProjectService
from schemas.project import ProjectCreate
import core.enums as enums

# Set page config with modern cinematic theme
st.set_page_config(
    page_title="MicroDrama Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB tables on startup
init_db()

# Custom CSS for modern dark-mode cinematic interface
st.markdown("""
<style>
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #FF6B6B 0%, #FFE66D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #8E8E93;
        font-size: 1.0rem;
        margin-bottom: 1.5rem;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #2C2C2E;
        color: #0A84FF;
        border: 1px solid #0A84FF44;
    }
</style>
""", unsafe_allow_html=True)

def render_sidebar():
    st.sidebar.markdown("### 🎬 **MICRODRAMA STUDIO**")
    st.sidebar.caption("AI 10-Minute Production Pipeline")
    st.sidebar.markdown("---")

    db = ScopedSession()
    try:
        projects = ProjectService.list_projects(db)
        if not projects:
            # Auto-seed the benchmark project on fresh database
            seed_proj = ProjectService.create_project(
                db,
                ProjectCreate(
                    title="After Closing",
                    genre="Horror",
                    target_duration_seconds=600,
                    logline="Trapped in a shopping mall after closing, Lucy and David must complete broadcast games only to discover the trials are transforming them into mannequins."
                )
            )
            projects = [seed_proj]

        project_options = {p.id: f"{p.title} ({p.genre})" for p in projects}

        if "current_project_id" not in st.session_state and projects:
            st.session_state.current_project_id = projects[0].id

        selected_id = st.sidebar.selectbox(
            "📁 Active Project",
            options=list(project_options.keys()),
            format_func=lambda x: project_options.get(x, "Select Project"),
            index=0 if projects else None
        )
        if selected_id:
            st.session_state.current_project_id = selected_id

        # Quick Project Creation Modal / Expander
        with st.sidebar.expander("➕ New Project"):
            with st.form("new_project_form"):
                new_title = st.text_input("Title", placeholder="e.g. After Closing")
                new_genre = st.selectbox("Genre", ["Horror", "Thriller", "Sci-Fi", "Mystery", "Drama", "Romance", "Comedy", "Fantasy"])
                new_duration = st.slider("Target Duration (mins)", 3, 15, 10) * 60
                new_logline = st.text_area("Logline / Idea", placeholder="Brief logline...")
                submitted = st.form_submit_button("Create Project")

                if submitted and new_title.strip():
                    created = ProjectService.create_project(
                        db,
                        ProjectCreate(
                            title=new_title.strip(),
                            genre=new_genre,
                            target_duration_seconds=new_duration,
                            logline=new_logline.strip() if new_logline else None
                        )
                    )
                    st.session_state.current_project_id = created.id
                    st.sidebar.success(f"Created: {created.title}")
                    st.rerun()

        # Display current project quick status badge
        if "current_project_id" in st.session_state and st.session_state.current_project_id:
            current_project = ProjectService.get_project(db, st.session_state.current_project_id)
            if current_project:
                st.sidebar.markdown("---")
                st.sidebar.markdown(f"**Status:** <span class='status-badge'>{current_project.status}</span>", unsafe_allow_html=True)
                st.sidebar.markdown(f"**Target:** `{current_project.target_duration_seconds // 60}m 00s`")

    finally:
        db.close()

    st.sidebar.markdown("---")
    st.sidebar.caption("MicroDrama Studio v0.1.0 (Local / Supabase Ready)")

render_sidebar()

# Main landing dashboard
st.markdown('<div class="main-header">🎬 MicroDrama Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Reusable 10-Minute AI Micro-Drama Production Pipeline</div>', unsafe_allow_html=True)

if "current_project_id" not in st.session_state or not st.session_state.current_project_id:
    st.info("👈 Please select or create a project from the sidebar to begin production.")
else:
    db = ScopedSession()
    try:
        project = ProjectService.get_project(db, st.session_state.current_project_id)
        if project:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Project", project.title)
            col2.metric("Genre", project.genre)
            col3.metric("Target Runtime", f"{project.target_duration_seconds // 60}m 00s")
            col4.metric("Status", project.status)

            st.markdown("### 📋 Production Navigation")
            st.write("Navigate through the multi-page tabs in the left sidebar to produce each stage of your micro-drama:")

            nav_cols = st.columns(3)
            with nav_cols[0]:
                st.markdown("""
                **Story & Universe**
                - `01 Story`: Structured 3-Act Script & Premise
                - `02 Characters`: Visual Profiles & Master References
                - `03 Locations`: Architectural Specs & Atmosphere
                - `04 Visual Style`: Cinematic Tone & Color Palette
                """)
            with nav_cols[1]:
                st.markdown("""
                **Breakdown & Keyframes**
                - `05 Scenes`: Scene Sequencing & Runtime Budget
                - `06 Shots`: Shotlist & Camera Direction
                - `07 Images`: FLUX/Qwen Keyframe Generation
                - `08 Videos`: LTX-2.x Modal Video Engine
                """)
            with nav_cols[2]:
                st.markdown("""
                **Review & Assembly**
                - `09 Review`: Approval & Prompt Re-Generation
                - `10 Final`: Timeline Assembly & Export
                - `11 Asset Library`: Project Media Vault
                - `12 Jobs`: Background Task Monitor
                """)
    finally:
        db.close()
