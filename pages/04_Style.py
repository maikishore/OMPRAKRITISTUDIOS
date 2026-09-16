import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.style_service import StyleService
from core.enums import ProjectStatus
from ai.style_engine import StyleEngine
from schemas.style import VisualStyleSchema

st.set_page_config(page_title="04 Visual Style | MicroDrama Studio", page_icon="🎨", layout="wide")

st.title("🎨 04. Visual Style & Cinematic Rules")
st.caption("Cinematography Language, Lighting Atmosphere, Lens Packages & Color Progression")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("⚠️ Please select a project from the sidebar first.")
    st.stop()

db = ScopedSession()
engine = StyleEngine()

try:
    project = ProjectService.get_project(db, project_id)
    if not project:
        st.error("Project not found.")
        st.stop()

    style = StyleService.get_project_style(db, project_id)

    # Top Control Bar
    top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
    with top_col1:
        st.subheader(f"🎬 Project: {project.title}")
        st.caption(f"Genre: **{project.genre}** | Tone: **{project.story.tone if project.story else 'Atmospheric'}**")
    with top_col2:
        is_approved = bool(style and style.is_approved)
        st.metric("Style Status", "✅ APPROVED" if is_approved else "📝 IN PROGRESS")
    with top_col3:
        if is_approved:
            st.success("Visual Style is Locked & Active.")
        else:
            st.info("Tune visual rules & click 'Approve Style' when ready.")

    st.markdown("---")

    # Generation Trigger Bar
    gen_col1, gen_col2, gen_col3 = st.columns([2, 1, 1])
    with gen_col1:
        st.write("**AI Style Design:** Synthesize cinematography & visual grammar tailored to your story using Gemma 4.")
    with gen_col2:
        generate_clicked = st.button("✨ Generate with Gemma 4", type="primary", use_container_width=True)
    with gen_col3:
        seed_clicked = st.button("🌱 Load 'After Closing' Style", use_container_width=True)

    if generate_clicked:
        with st.spinner("Designing visual style with Gemma 4..."):
            extracted = engine.generate_style_from_story(project)
            StyleService.save_or_update_style(db, project.id, extracted, approve=False)
            st.success("Cinematic style generated and saved as draft!")
            st.rerun()

    if seed_clicked:
        seed_style = engine._get_fallback_style(project.genre)
        StyleService.save_or_update_style(db, project.id, seed_style, approve=False)
        st.success("Loaded 'After Closing' cinematic benchmark style!")
        st.rerun()

    # Style Editor Form
    if style:
        st.markdown("### 📽️ Cinematography & Optical Specifications")

        with st.form("style_editor_form"):
            c1, c2 = st.columns(2)
            with c1:
                realism = st.text_input("Cinematic Realism", value=style.cinematic_realism or "35mm Photochemical film look")
                lens = st.text_input("Lens Preferences & Focal Lengths", value=style.lens_preferences or "Anamorphic Primes (35mm, 50mm, 85mm)")
                dof = st.text_input("Depth of Field & Bokeh", value=style.depth_of_field or "Shallow T2.0 with oval bokeh")
                grain = st.text_input("Film Grain Texture", value=style.film_grain or "Organic 35mm 500T grain")
            with c2:
                camera = st.text_area("Camera Language & Choreography", value=style.camera_language or "", height=70)
                contrast = st.text_input("Contrast & Tonal Curve", value=style.contrast or "High contrast with deep crushed blacks")
                design = st.text_area("Production Design & Textures", value=style.production_design or "", height=70)

            lighting = st.text_area("Lighting Philosophy", value=style.lighting_language or "", height=70)
            color = st.text_area("Color Grading Progression Across Acts", value=style.color_progression or "", height=70)
            motifs = st.text_area("Visual Motifs (one per line)", value="\n".join(style.visual_motifs or []), height=70)

            st.markdown("---")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                save_draft = st.form_submit_button("💾 Save Changes as Draft", use_container_width=True)
            with btn_col2:
                approve_style = st.form_submit_button("✅ Save & APPROVE Visual Style", type="primary", use_container_width=True)

            if save_draft or approve_style:
                updated_schema = VisualStyleSchema(
                    cinematic_realism=realism,
                    camera_language=camera,
                    lens_preferences=lens,
                    lighting_language=lighting,
                    color_progression=color,
                    contrast=contrast,
                    depth_of_field=dof,
                    film_grain=grain,
                    production_design=design,
                    visual_motifs=[m.strip() for m in motifs.split("\n") if m.strip()]
                )
                StyleService.save_or_update_style(db, project.id, updated_schema, approve=bool(approve_style))
                if approve_style:
                    st.success("🎉 Visual Style approved! Project status updated to STYLE_READY. Production Bible is Complete!")
                else:
                    st.success("Style saved as draft!")
                st.rerun()

    else:
        st.info("No visual style generated yet. Click **'Generate with Gemma 4'** or **'Load Style'** to define your cinematic look.")

finally:
    db.close()
