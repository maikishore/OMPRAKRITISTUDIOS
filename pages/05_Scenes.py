import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import get_db_session
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.location_service import LocationService
from core.style_service import StyleService
from core.scene_service import SceneService
from core.shot_service import ShotService
from schemas.scene import SceneCreate
from ai.scene_engine import SceneEngine
from core.enums import ProjectStatus

st.set_page_config(page_title="Scenes Breakdown | MicroDrama Studio", page_icon="🎬", layout="wide")

def format_time(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def render_scenes_page():
    st.title("🎬 Scene Breakdown & Timeline")
    st.caption("Decompose approved 3-Act Story and Production Bible into structured cinematic scenes (~10 minutes total runtime).")

    with get_db_session() as db:
        projects = ProjectService.list_projects(db)
        if not projects:
            st.warning("No projects found. Please create one on the Dashboard.")
            return

        # Project selector
        current_pid = st.session_state.get("current_project_id")
        project_ids = [p.id for p in projects]
        default_idx = project_ids.index(current_pid) if current_pid in project_ids else 0

        project_options = {p.id: f"{p.title} ({p.genre}) - [{p.status}]" for p in projects}
        selected_id = st.sidebar.selectbox("Active Project", options=project_ids, index=default_idx, format_func=lambda x: project_options[x])
        st.session_state["current_project_id"] = selected_id
        project = ProjectService.get_project(db, selected_id)
        if not project:
            return

        story = project.story
        characters = CharacterService.list_characters_by_project(db, project.id)
        locations = LocationService.list_locations_by_project(db, project.id)
        style = StyleService.get_style_by_project(db, project.id)
        scenes = SceneService.list_scenes_by_project(db, project.id)

        # Runtime & Budget Metrics Bar
        runtime_stats = SceneService.calculate_total_runtime(db, project.id)
        total_s = runtime_stats["total_seconds"]
        target_s = runtime_stats["target_seconds"]
        delta_s = runtime_stats["delta_seconds"]
        scene_count = runtime_stats["scene_count"]
        pct = runtime_stats["percent_of_target"]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Scenes", f"{scene_count}")
        col2.metric("Runtime / Target", f"{format_time(total_s)} / {format_time(target_s)}")
        col3.metric("Runtime Delta", f"{'+' if delta_s > 0 else ''}{delta_s}s", delta_color="off" if abs(delta_s) <= 60 else "inverse")
        col4.metric("Budget Fill", f"{pct}%")
        col5.metric("Project Status", project.status)

        # Progress bar
        progress_val = min(1.0, max(0.0, total_s / target_s if target_s > 0 else 0.0))
        st.progress(progress_val, text=f"Runtime Budget: {format_time(total_s)} of {format_time(target_s)} ({pct}%)")

        if total_s > 0 and abs(delta_s) > 60:
            if delta_s > 60:
                st.warning(f"⚠️ Current scenes exceed target runtime by {delta_s}s ({format_time(delta_s)}). Consider trimming scene durations.")
            else:
                st.info(f"ℹ️ Current scenes are {abs(delta_s)}s ({format_time(abs(delta_s))}) under target runtime.")

        st.markdown("---")

        # Action Toolbar
        action_col1, action_col2, action_col3 = st.columns([2, 2, 1.5])

        with action_col1:
            if st.button("🤖 Generate Scenes with Gemma 4 26B", use_container_width=True, type="primary"):
                if not story or not story.structured_data:
                    st.error("No approved 3-Act story found for this project. Please build and approve a story on Page 01.")
                else:
                    with st.spinner("Decomposing story into 8-12 cinematic scenes using Gemma 4 26B..."):
                        engine = SceneEngine()
                        char_names = [c.name for c in characters]
                        loc_names = [l.name for l in locations]
                        style_summary = style.cinematic_realism if style else ""

                        generated_scenes = engine.generate_scenes(
                            title=project.title,
                            genre=project.genre,
                            target_duration_seconds=project.target_duration_seconds,
                            story_context=story.structured_data,
                            character_names=char_names,
                            location_names=loc_names,
                            visual_style_summary=style_summary
                        )

                        # Match location names to location IDs
                        loc_name_to_id = {l.name.lower(): l.id for l in locations}
                        for sc in generated_scenes:
                            loc_name = sc.get("location_name", "").lower()
                            for known_name, l_id in loc_name_to_id.items():
                                if known_name in loc_name or loc_name in known_name:
                                    sc["location_id"] = l_id
                                    break

                        SceneService.batch_create_scenes(db, project.id, generated_scenes)
                        st.success(f"Generated {len(generated_scenes)} scenes successfully!")
                        st.rerun()

        with action_col2:
            if st.button("🌱 Load Seed Scenes (After Closing)", use_container_width=True):
                seed_scenes = SceneEngine.get_seed_scenes_for_after_closing(project.target_duration_seconds)
                # Match location names
                loc_name_to_id = {l.name.lower(): l.id for l in locations}
                for sc in seed_scenes:
                    loc_name = sc.get("location_name", "").lower()
                    for known_name, l_id in loc_name_to_id.items():
                        if known_name in loc_name or loc_name in known_name:
                            sc["location_id"] = l_id
                            break
                created_scenes = SceneService.batch_create_scenes(db, project.id, seed_scenes)

                # Prepare bible dictionaries for prompt compiler
                style_dict = {"cinematic_realism": style.cinematic_realism} if style else {}
                chars_list = [{"name": c.name, "signature_costume": getattr(c, 'signature_costume', ''), "physical_traits": getattr(c, 'physical_traits', ''), "visual_anchor_prompt": getattr(c, 'visual_anchor_prompt', '')} for c in characters]

                # Auto-populate seed shots for each created scene
                from ai.image_prompt_engine import PromptCompiler
                for sc in created_scenes:
                    seed_shots = ShotEngine.get_seed_shots_for_scene(sc.scene_number)
                    loc = LocationService.get_location(db, sc.location_id) if sc.location_id else None
                    loc_dict = {"name": getattr(loc, "name", "Interior"), "architecture": getattr(loc, "architecture", ""), "lighting": getattr(loc, "lighting", "")} if loc else {}

                    for s in seed_shots:
                        s["image_prompt"] = PromptCompiler.compile_image_prompt(
                            style_data=style_dict,
                            location_data=loc_dict,
                            characters_data=chars_list,
                            scene_data={"visual_direction": sc.visual_direction},
                            shot_data=s
                        )
                        s["video_prompt"] = PromptCompiler.compile_video_prompt(
                            style_data=style_dict,
                            location_data=loc_dict,
                            characters_data=chars_list,
                            scene_data={"sound_design": sc.sound_design},
                            shot_data=s
                        )
                    ShotService.batch_create_shots_for_scene(db, sc.id, seed_shots)

                st.success(f"Loaded 10 canonical seed scenes and all accompanying shots for 'After Closing'!")
                st.rerun()

        with action_col3:
            if st.button("➕ Add Empty Scene", use_container_width=True):
                new_num = len(scenes) + 1
                new_scene_in = SceneCreate(
                    project_id=project.id,
                    scene_number=new_num,
                    title=f"Scene {new_num}: Untitled Scene",
                    duration_seconds=50,
                    summary="New scene action description...",
                    purpose="Dramatic progression",
                    emotional_state="Tense"
                )
                created = SceneService.create_scene(db, new_scene_in)
                # Seed default shots for new scene
                seed_shots = ShotEngine.get_seed_shots_for_scene(new_num)
                ShotService.batch_create_shots_for_scene(db, created.id, seed_shots)
                st.success(f"Added Scene {new_num} with initial shots!")
                st.rerun()

        # Batch Shot Generation Toolbar if shots missing
        total_project_shots = len(ShotService.list_shots_by_project(db, project.id))
        if scenes and total_project_shots == 0:
            st.warning("⚠️ Scenes exist, but shots have not been generated yet.")
            if st.button("⚡ Generate All Shots for All Scenes Now", type="primary", use_container_width=True):
                with st.spinner("Generating shots for all scenes with deterministic prompts..."):
                    style_dict = {"cinematic_realism": style.cinematic_realism} if style else {}
                    chars_list = [{"name": c.name, "signature_costume": getattr(c, 'signature_costume', ''), "physical_traits": getattr(c, 'physical_traits', ''), "visual_anchor_prompt": getattr(c, 'visual_anchor_prompt', '')} for c in characters]
                    from ai.image_prompt_engine import PromptCompiler
                    for sc in scenes:
                        seed_shots = ShotEngine.get_seed_shots_for_scene(sc.scene_number)
                        loc = LocationService.get_location(db, sc.location_id) if sc.location_id else None
                        loc_dict = {"name": getattr(loc, "name", "Interior"), "architecture": getattr(loc, "architecture", ""), "lighting": getattr(loc, "lighting", "")} if loc else {}
                        for s in seed_shots:
                            s["image_prompt"] = PromptCompiler.compile_image_prompt(
                                style_data=style_dict,
                                location_data=loc_dict,
                                characters_data=chars_list,
                                scene_data={"visual_direction": sc.visual_direction},
                                shot_data=s
                            )
                            s["video_prompt"] = PromptCompiler.compile_video_prompt(
                                style_data=style_dict,
                                location_data=loc_dict,
                                characters_data=chars_list,
                                scene_data={"sound_design": sc.sound_design},
                                shot_data=s
                            )
                        ShotService.batch_create_shots_for_scene(db, sc.id, seed_shots)
                st.success("All shots generated across all scenes!")
                st.rerun()

        st.markdown("### Scene Sequence")

        if not scenes:
            st.info("No scenes created yet. Click 'Generate Scenes with Gemma 4 26B' or 'Load Seed Scenes' to get started.")
            return

        # Location ID to name lookup
        loc_id_to_name = {l.id: l.name for l in locations}
        loc_options = {None: "— Unassigned —"} | {l.id: l.name for l in locations}

        for scene in scenes:
            loc_label = loc_id_to_name.get(scene.location_id, "No Location")
            scene_shots = ShotService.list_shots_by_scene(db, scene.id)
            shot_count = len(scene_shots)
            status_badge = "✅ Approved" if scene.is_approved else "📝 Draft"

            header_text = (
                f"🎬 Scene {scene.scene_number:02d}: **{scene.title}** "
                f"({format_time(scene.duration_seconds)}) | 📍 {loc_label} | 🎞️ {shot_count} Shots | {status_badge}"
            )

            with st.expander(header_text, expanded=(scene.scene_number <= 2)):
                with st.form(key=f"scene_form_{scene.id}"):
                    f_col1, f_col2, f_col3 = st.columns([3, 2, 1.5])
                    with f_col1:
                        new_title = st.text_input("Scene Title", value=scene.title or "")
                    with f_col2:
                        loc_keys = list(loc_options.keys())
                        cur_idx = loc_keys.index(scene.location_id) if scene.location_id in loc_keys else 0
                        new_loc_id = st.selectbox("Location", options=loc_keys, index=cur_idx, format_func=lambda x: loc_options[x])
                    with f_col3:
                        new_duration = st.number_input("Duration (seconds)", min_value=5, max_value=300, value=int(scene.duration_seconds), step=5)

                    r2_col1, r2_col2, r2_col3 = st.columns(3)
                    with r2_col1:
                        new_time = st.text_input("Time of Day", value=scene.time_of_day or "Night")
                    with r2_col2:
                        new_beat = st.text_input("Story Beat", value=scene.story_beat or "Act 1 - Setup")
                    with r2_col3:
                        new_emotion = st.text_input("Emotional State / Tension", value=scene.emotional_state or "Mounting tension")

                    new_chars_str = st.text_input("Characters Present (comma separated)", value=", ".join(scene.characters) if scene.characters else "")
                    new_summary = st.text_area("Dramatic Action & Summary", value=scene.summary or "", height=80)
                    new_purpose = st.text_input("Story Purpose / Function", value=scene.purpose or "")

                    r4_col1, r4_col2 = st.columns(2)
                    with r4_col1:
                        new_visual = st.text_area("Visual Direction & Lighting Mood", value=scene.visual_direction or "", height=70)
                    with r4_col2:
                        new_sound = st.text_area("Sound Design & Music Cues", value=scene.sound_design or "", height=70)

                    new_continuity = st.text_input("Continuity Notes & Key Props", value=scene.continuity_notes or "")

                    btn_col1, btn_col2, btn_col3 = st.columns([2, 1.5, 1.5])
                    with btn_col1:
                        save_submitted = st.form_submit_button("💾 Save Scene Changes", use_container_width=True)
                    with btn_col2:
                        approve_submitted = st.form_submit_button("✅ Mark Approved", use_container_width=True)
                    with btn_col3:
                        delete_submitted = st.form_submit_button("🗑️ Delete Scene", use_container_width=True)

                    if save_submitted:
                        char_list = [c.strip() for c in new_chars_str.split(",") if c.strip()]
                        SceneService.update_scene(db, scene.id, {
                            "title": new_title,
                            "location_id": new_loc_id,
                            "duration_seconds": new_duration,
                            "time_of_day": new_time,
                            "story_beat": new_beat,
                            "emotional_state": new_emotion,
                            "characters": char_list,
                            "summary": new_summary,
                            "purpose": new_purpose,
                            "visual_direction": new_visual,
                            "sound_design": new_sound,
                            "continuity_notes": new_continuity
                        })
                        st.success("Scene updated!")
                        st.rerun()

                    if approve_submitted:
                        SceneService.update_scene(db, scene.id, {"is_approved": True})
                        st.success(f"Scene {scene.scene_number} approved!")
                        st.rerun()

                    if delete_submitted:
                        SceneService.delete_scene(db, scene.id)
                        st.warning(f"Deleted Scene {scene.scene_number}!")
                        st.rerun()

                # Embedded Shot Preview inside Scene
                st.markdown(f"**🎞️ Shots in Scene {scene.scene_number:02d} ({len(scene_shots)} Shots):**")
                if scene_shots:
                    for sh in scene_shots:
                        sh_status = "✅" if sh.status == "approved" else "📝"
                        st.caption(f"{sh_status} **Shot {sh.shot_number:02d}** [{sh.shot_type}] ({sh.duration_seconds}s) — *{sh.action[:90] if sh.action else 'No action description'}...*")
                else:
                    st.caption("No shots generated for this scene yet.")
                    if st.button(f"⚡ Populate Shots for Scene {scene.scene_number:02d}", key=f"btn_pop_shots_{scene.id}"):
                        seed_shots = ShotEngine.get_seed_shots_for_scene(scene.scene_number)
                        style_dict = {"cinematic_realism": style.cinematic_realism} if style else {}
                        chars_list = [{"name": c.name, "signature_costume": getattr(c, 'signature_costume', ''), "physical_traits": getattr(c, 'physical_traits', ''), "visual_anchor_prompt": getattr(c, 'visual_anchor_prompt', '')} for c in characters]
                        loc = LocationService.get_location(db, scene.location_id) if scene.location_id else None
                        loc_dict = {"name": getattr(loc, "name", "Interior"), "architecture": getattr(loc, "architecture", ""), "lighting": getattr(loc, "lighting", "")} if loc else {}
                        from ai.image_prompt_engine import PromptCompiler
                        for s in seed_shots:
                            s["image_prompt"] = PromptCompiler.compile_image_prompt(
                                style_data=style_dict,
                                location_data=loc_dict,
                                characters_data=chars_list,
                                scene_data={"visual_direction": scene.visual_direction},
                                shot_data=s
                            )
                            s["video_prompt"] = PromptCompiler.compile_video_prompt(
                                style_data=style_dict,
                                location_data=loc_dict,
                                characters_data=chars_list,
                                scene_data={"sound_design": scene.sound_design},
                                shot_data=s
                            )
                        ShotService.batch_create_shots_for_scene(db, scene.id, seed_shots)
                        st.success(f"Generated {len(seed_shots)} shots for Scene {scene.scene_number:02d}!")
                        st.rerun()

        # Approval Gate
        st.markdown("---")
        app_col1, app_col2 = st.columns([3, 1.5])
        with app_col1:
            st.info("💡 Once all scenes and running times are locked, approve all scenes to transition to **SCENES_READY**.")
        with app_col2:
            if st.button("🔒 Approve All Scenes & Lock Timeline", use_container_width=True, type="primary"):
                SceneService.approve_all_scenes(db, project.id)
                st.balloons()
                st.success(f"Project status updated to '{ProjectStatus.SCENES_READY.value}'! Proceed to 06 Shots.")
                st.rerun()

if __name__ == "__main__":
    render_scenes_page()
