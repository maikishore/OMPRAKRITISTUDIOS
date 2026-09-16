import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.enums import ProjectStatus
from ai.story_engine import StoryEngine
from schemas.story import StorySchema

st.set_page_config(page_title="01 Story Engine | MicroDrama Studio", page_icon="📖", layout="wide")

st.title("📖 01. Story Engine")
st.caption("AI-Assisted Structured Story, 3-Act Breakdown & World Rules")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("⚠️ Please select or create an active project from the sidebar first.")
    st.stop()

db = ScopedSession()
engine = StoryEngine()

try:
    project = ProjectService.get_project(db, project_id)
    if not project:
        st.error("Project not found.")
        st.stop()

    story = project.story

    # Top Header Controls
    top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
    with top_col1:
        st.subheader(f"🎬 Project: {project.title}")
        st.caption(f"Genre: **{project.genre}** | Target Runtime: **{project.target_duration_seconds // 60}m 00s**")
    with top_col2:
        status_label = "✅ APPROVED" if (story and story.is_approved) else "📝 DRAFT / IN PROGRESS"
        st.metric("Story Status", status_label)
    with top_col3:
        if story and story.is_approved:
            st.success("Story is Approved & Locked.")
        else:
            st.info("Draft Mode: Edit and click 'Approve Story' when finalized.")

    st.markdown("---")

    # Generation Trigger Bar
    gen_col1, gen_col2, gen_col3 = st.columns([2, 1, 1])
    with gen_col1:
        custom_idea = st.text_input(
            "Core Idea / Prompt for Gemma 4:",
            value=project.logline or "",
            placeholder="e.g. Trapped in a mall after closing, players forced to play games..."
        )
    with gen_col2:
        st.write("")
        st.write("")
        generate_clicked = st.button("✨ Generate with Gemma 4", type="primary", use_container_width=True)
    with gen_col3:
        st.write("")
        st.write("")
        seed_clicked = st.button("🌱 Load 'After Closing' Seed", use_container_width=True)

    # Handle Generation
    if generate_clicked:
        with st.spinner("Writing cinematic story using Cloudflare Gemma 4 (26B)..."):
            idea_to_use = custom_idea.strip() if custom_idea.strip() else (project.logline or project.title)
            new_story_schema = engine.generate_story(
                title=project.title,
                genre=project.genre,
                idea=idea_to_use,
                target_duration_seconds=project.target_duration_seconds
            )
            engine.save_story(db, project.id, new_story_schema, approve=False)
            st.success("Story generated and saved as draft!")
            st.rerun()

    if seed_clicked:
        seed_schema = engine._get_fallback_story(project.title, project.genre, "After Closing horror mall seed")
        engine.save_story(db, project.id, seed_schema, approve=False)
        st.success("Loaded 'After Closing' benchmark story structure!")
        st.rerun()

    # Story Editor Form
    if story:
        st.markdown("### 📝 Structured Story Editor")

        with st.form("story_editor_form"):
            col_premise, col_tone = st.columns(2)
            with col_premise:
                premise = st.text_area("Premise", value=story.premise or "", height=80)
                theme = st.text_input("Central Theme", value=story.theme or "")
            with col_tone:
                tone = st.text_input("Visual & Emotional Tone", value=story.tone or "")
                ending = st.text_area("Climatic Ending / Twist", value=story.ending or "", height=80)

            synopsis = st.text_area("Full Narrative Synopsis (~10 min)", value=story.synopsis or "", height=150)

            st.markdown("#### 🎭 3-Act Structure")
            acts_data = story.acts or []
            act_cols = st.columns(3)
            updated_acts = []
            for i, col in enumerate(act_cols):
                act_item = acts_data[i] if i < len(acts_data) else {"act": i+1, "title": f"Act {i+1}", "description": "", "key_revelation": ""}
                with col:
                    st.markdown(f"**Act {i+1}**")
                    a_title = st.text_input(f"Title {i+1}", value=act_item.get("title", ""), key=f"act_t_{i}")
                    a_desc = st.text_area(f"Description {i+1}", value=act_item.get("description", ""), height=100, key=f"act_d_{i}")
                    a_rev = st.text_input(f"Key Revelation {i+1}", value=act_item.get("key_revelation", ""), key=f"act_r_{i}")
                    updated_acts.append({"act": i+1, "title": a_title, "description": a_desc, "key_revelation": a_rev})

            st.markdown("#### 📌 Narrative Rules & Anchors")
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                rules_text = st.text_area("World & Story Rules (one per line)", value="\n".join(story.story_rules or []), height=120)
            with r_col2:
                clues_text = st.text_area("Narrative Clues (one per line)", value="\n".join(story.clues or []), height=120)
            with r_col3:
                continuity_text = st.text_area("Continuity Rules (one per line)", value="\n".join(story.continuity_rules or []), height=120)

            st.markdown("---")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                save_draft = st.form_submit_button("💾 Save Changes as Draft", use_container_width=True)
            with btn_col2:
                approve_story = st.form_submit_button("✅ Save & APPROVE Story", type="primary", use_container_width=True)

            if save_draft or approve_story:
                updated_schema = StorySchema(
                    premise=premise,
                    theme=theme,
                    tone=tone,
                    synopsis=synopsis,
                    ending=ending,
                    story_rules=[r.strip() for r in rules_text.split("\n") if r.strip()],
                    acts=updated_acts,
                    clues=[c.strip() for c in clues_text.split("\n") if c.strip()],
                    continuity_rules=[cr.strip() for cr in continuity_text.split("\n") if cr.strip()]
                )
                engine.save_story(db, project.id, updated_schema, approve=bool(approve_story))
                if approve_story:
                    st.success("🎉 Story approved! Project advanced to STORY_APPROVED. Ready for Phase 2 (Characters & Locations).")
                else:
                    st.success("Draft saved successfully!")
                st.rerun()
    else:
        st.info("No story generated yet. Click **'Generate with Gemma 4'** or **'Load Seed'** above to begin.")

finally:
    db.close()
