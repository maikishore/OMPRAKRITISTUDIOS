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
from schemas.shot import ShotCreate
from ai.shot_engine import ShotEngine
from ai.image_prompt_engine import PromptCompiler
from core.enums import ShotStatus, ProjectStatus

st.set_page_config(page_title="Shotlist & Prompt Compiler | MicroDrama Studio", page_icon="🎞️", layout="wide")

def render_shots_page():
    st.title("🎞️ Shot Breakdown & Deterministic Prompt Compiler")
    st.caption("Break down scenes into granular 3–10s cinematic shots and synthesize production prompts from the Production Bible.")

    with get_db_session() as db:
        projects = ProjectService.list_projects(db)
        if not projects:
            st.warning("No projects found. Please create one on the Dashboard.")
            return

        current_pid = st.session_state.get("current_project_id")
        project_ids = [p.id for p in projects]
        default_idx = project_ids.index(current_pid) if current_pid in project_ids else 0

        project_options = {p.id: f"{p.title} ({p.genre}) - [{p.status}]" for p in projects}
        selected_id = st.sidebar.selectbox("Active Project", options=project_ids, index=default_idx, format_func=lambda x: project_options[x])
        st.session_state["current_project_id"] = selected_id
        project = ProjectService.get_project(db, selected_id)
        if not project:
            return

        scenes = SceneService.list_scenes_by_project(db, project.id)
        if not scenes:
            st.warning("No scenes found for this project. Please generate or create scenes on Page 05 Scenes first.")
            return

        # Fetch production bible elements for deterministic prompt compilation
        characters = CharacterService.list_characters_by_project(db, project.id)
        locations = LocationService.list_locations_by_project(db, project.id)
        style = StyleService.get_style_by_project(db, project.id)

        # Scene selection
        scene_options = {
            s.id: f"Scene {s.scene_number:02d}: {s.title} ({s.duration_seconds}s) — [{len(s.shots)} Shots]"
            for s in scenes
        }
        selected_scene_id = st.selectbox("Select Scene to Direct", options=list(scene_options.keys()), format_func=lambda x: scene_options[x])
        scene = SceneService.get_scene(db, selected_scene_id)
        if not scene:
            return

        # Scene context header card
        loc = LocationService.get_location(db, scene.location_id) if scene.location_id else None
        loc_name = loc.name if loc else "Unassigned"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Scene Number", f"Scene {scene.scene_number:02d}")
        c2.metric("Scene Target Runtime", f"{scene.duration_seconds}s")
        c3.metric("Location", loc_name)
        c4.metric("Characters in Scene", ", ".join(scene.characters) if scene.characters else "None")

        st.info(f"**Scene Purpose:** {scene.purpose or 'Dramatic progression'}  \n**Summary:** {scene.summary or 'No summary provided.'}")

        # Action Toolbar
        shots = ShotService.list_shots_by_scene(db, scene.id)
        st.markdown("---")
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1.5])

        # Prepare bible dictionaries for compilation
        style_dict = {
            "cinematic_realism": getattr(style, "cinematic_realism", "") if style else "",
            "contrast": getattr(style, "contrast", "") if style else "",
            "film_grain": getattr(style, "film_grain", "") if style else "",
            "depth_of_field": getattr(style, "depth_of_field", "") if style else "",
            "lighting_language": getattr(style, "lighting_language", "") if style else ""
        }

        loc_dict = {
            "name": getattr(loc, "name", "Interior") if loc else "Interior",
            "architecture": getattr(loc, "architecture", "") if loc else "",
            "materials": getattr(loc, "materials", "") if loc else "",
            "lighting": getattr(loc, "lighting", "") if loc else "",
            "visual_anchor_prompt": getattr(loc, "visual_anchor_prompt", getattr(loc, "visual_identity", "")) if loc else ""
        }

        chars_list = [
            {
                "name": c.name,
                "signature_costume": getattr(c, "signature_costume", getattr(c, "clothing", "")),
                "physical_traits": getattr(c, "physical_traits", getattr(c, "appearance", "")),
                "visual_anchor_prompt": getattr(c, "visual_anchor_prompt", getattr(c, "identity_prompt", ""))
            }
            for c in characters
        ]

        with btn_col1:
            if st.button(f"🤖 Generate Shots for Scene {scene.scene_number:02d} (Gemma 4 26B)", use_container_width=True, type="primary"):
                with st.spinner(f"Decomposing Scene {scene.scene_number} into granular shots using Gemma 4 26B & compiling deterministic prompts..."):
                    engine = ShotEngine()
                    scene_dict = {
                        "scene_number": scene.scene_number,
                        "title": scene.title,
                        "summary": scene.summary,
                        "purpose": scene.purpose,
                        "duration_seconds": scene.duration_seconds,
                        "location_name": loc_name,
                        "characters": scene.characters,
                        "time_of_day": scene.time_of_day,
                        "emotional_state": scene.emotional_state,
                        "visual_direction": scene.visual_direction,
                        "sound_design": scene.sound_design
                    }

                    generated_shots = engine.generate_shots_for_scene(
                        scene_data=scene_dict,
                        style_data=style_dict,
                        location_data=loc_dict,
                        characters_data=chars_list
                    )

                    ShotService.batch_create_shots_for_scene(db, scene.id, generated_shots)
                    st.success(f"Generated {len(generated_shots)} shots with compiled prompts!")
                    st.rerun()

        with btn_col2:
            if st.button(f"🌱 Load Seed Shots for Scene {scene.scene_number:02d}", use_container_width=True):
                seed_shots = ShotEngine.get_seed_shots_for_scene(scene.scene_number)
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
                st.success(f"Loaded {len(seed_shots)} seed shots!")
                st.rerun()

        with btn_col3:
            if st.button("➕ Add Manual Shot", use_container_width=True):
                new_num = len(shots) + 1
                manual_shot = ShotCreate(
                    scene_id=scene.id,
                    shot_number=new_num,
                    duration_seconds=5.0,
                    shot_type="Medium Shot",
                    camera_angle="Eye-level",
                    camera_movement="Slow Dolly in",
                    lens="50mm prime",
                    action="Character action description...",
                    emotion="Tense",
                    lighting="Dramatic low key",
                    sound="Subtle ambient rumble"
                )
                created_shot = ShotService.create_shot(db, manual_shot)
                # Compile initial prompt
                img_prompt = PromptCompiler.compile_image_prompt(
                    style_data=style_dict,
                    location_data=loc_dict,
                    characters_data=chars_list,
                    scene_data={"visual_direction": scene.visual_direction},
                    shot_data={"shot_type": "Medium Shot", "lens": "50mm prime", "action": manual_shot.action}
                )
                vid_prompt = PromptCompiler.compile_video_prompt(
                    style_data=style_dict,
                    location_data=loc_dict,
                    characters_data=chars_list,
                    shot_data={"shot_type": "Medium Shot", "camera_movement": "Slow Dolly in", "duration_seconds": 5.0}
                )
                ShotService.update_shot(db, created_shot.id, {"image_prompt": img_prompt, "video_prompt": vid_prompt})
                st.success(f"Added Shot {new_num}!")
                st.rerun()

        # Shot List Display
        st.markdown(f"### Shotlist for Scene {scene.scene_number:02d} ({len(shots)} Shots)")
        if not shots:
            st.info("No shots created for this scene yet. Click 'Generate Shots with Gemma 4 26B' or 'Load Seed Shots'.")
            return

        total_shot_duration = sum(s.duration_seconds for s in shots)
        st.caption(f"Total Shot Duration: **{total_shot_duration:.1f}s** / Scene Target: **{scene.duration_seconds}s**")

        for shot in shots:
            shot_status_icon = "✅ Approved" if shot.status == ShotStatus.APPROVED.value else "📝 Draft"
            chars_badge = ", ".join(shot.characters) if shot.characters else "No character in frame"

            exp_label = (
                f"🎞️ Shot {shot.shot_number:02d}: [{shot.shot_type}] {shot.camera_movement} ({shot.duration_seconds}s) "
                f"| 👥 {chars_badge} | {shot_status_icon}"
            )

            with st.expander(exp_label, expanded=(shot.shot_number <= 2)):
                with st.form(key=f"shot_form_{shot.id}"):
                    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
                    with r1_col1:
                        new_shot_type = st.selectbox(
                            "Shot Type",
                            options=["Wide Shot", "Extreme Wide Shot", "Medium Shot", "Medium Close-up", "Close-up", "Extreme Close-up", "Over-the-Shoulder", "Point-of-View"],
                            index=["Wide Shot", "Extreme Wide Shot", "Medium Shot", "Medium Close-up", "Close-up", "Extreme Close-up", "Over-the-Shoulder", "Point-of-View"].index(shot.shot_type) if shot.shot_type in ["Wide Shot", "Extreme Wide Shot", "Medium Shot", "Medium Close-up", "Close-up", "Extreme Close-up", "Over-the-Shoulder", "Point-of-View"] else 0
                        )
                    with r1_col2:
                        new_angle = st.text_input("Camera Angle", value=shot.camera_angle or "Eye-level")
                    with r1_col3:
                        new_movement = st.text_input("Camera Movement", value=shot.camera_movement or "Slow Dolly")
                    with r1_col4:
                        new_lens = st.text_input("Lens Package", value=shot.lens or "50mm prime")

                    r2_col1, r2_col2, r2_col3 = st.columns([2, 1, 1])
                    with r2_col1:
                        new_chars_str = st.text_input("Characters in Frame (comma separated)", value=", ".join(shot.characters) if shot.characters else "")
                    with r2_col2:
                        new_duration = st.number_input("Duration (s)", min_value=1.0, max_value=20.0, value=float(shot.duration_seconds), step=0.5)
                    with r2_col3:
                        new_emotion = st.text_input("Character Emotion", value=shot.emotion or "Tense")

                    new_action = st.text_area("Physical Action & Movement", value=shot.action or "", height=70)
                    new_dialogue = st.text_input("Dialogue (if spoken)", value=shot.dialogue or "")

                    r3_col1, r3_col2 = st.columns(2)
                    with r3_col1:
                        new_lighting = st.text_input("Lighting Setup", value=shot.lighting or "")
                    with r3_col2:
                        new_sound = st.text_input("Sound / Foley Cue", value=shot.sound or "")

                    # Compiled Prompts Section
                    st.markdown("#### 🎯 Compiled Production Prompts")
                    new_image_prompt = st.text_area(
                        "🖼️ Keyframe Image Prompt (Deterministic: FLUX / Qwen)",
                        value=shot.image_prompt or "",
                        height=100
                    )
                    new_video_prompt = st.text_area(
                        "🎥 Video Generation Prompt (Temporal Dynamics: LTX-2.3)",
                        value=shot.video_prompt or "",
                        height=90
                    )

                    # Prompt Version History
                    versions = ShotService.list_prompt_versions(db, "shot_image", shot.id)
                    if versions:
                        st.caption(f"📜 Prompt Revisions: {len(versions)} recorded versions in database (latest v{versions[0].version})")

                    b_col1, b_col2, b_col3, b_col4 = st.columns([2, 2, 1.5, 1.5])
                    with b_col1:
                        save_shot_btn = st.form_submit_button("💾 Save Shot & Prompts", use_container_width=True)
                    with b_col2:
                        recompile_btn = st.form_submit_button("🔄 Recompile Prompts from Bible", use_container_width=True)
                    with b_col3:
                        approve_shot_btn = st.form_submit_button("✅ Approve Shot", use_container_width=True)
                    with b_col4:
                        delete_shot_btn = st.form_submit_button("🗑️ Delete", use_container_width=True)

                    if save_shot_btn:
                        char_list = [c.strip() for c in new_chars_str.split(",") if c.strip()]
                        ShotService.update_shot(db, shot.id, {
                            "shot_type": new_shot_type,
                            "camera_angle": new_angle,
                            "camera_movement": new_movement,
                            "lens": new_lens,
                            "characters": char_list,
                            "duration_seconds": new_duration,
                            "emotion": new_emotion,
                            "action": new_action,
                            "dialogue": new_dialogue or None,
                            "lighting": new_lighting,
                            "sound": new_sound,
                            "image_prompt": new_image_prompt,
                            "video_prompt": new_video_prompt
                        })
                        st.success(f"Shot {shot.shot_number} saved and prompt version recorded!")
                        st.rerun()

                    if recompile_btn:
                        recompiled_img = PromptCompiler.compile_image_prompt(
                            style_data=style_dict,
                            location_data=loc_dict,
                            characters_data=chars_list,
                            scene_data={"visual_direction": scene.visual_direction},
                            shot_data={
                                "shot_type": new_shot_type,
                                "camera_angle": new_angle,
                                "lens": new_lens,
                                "action": new_action,
                                "emotion": new_emotion,
                                "lighting": new_lighting
                            }
                        )
                        recompiled_vid = PromptCompiler.compile_video_prompt(
                            style_data=style_dict,
                            location_data=loc_dict,
                            characters_data=chars_list,
                            scene_data={"sound_design": scene.sound_design},
                            shot_data={
                                "shot_type": new_shot_type,
                                "camera_movement": new_movement,
                                "duration_seconds": new_duration,
                                "action": new_action,
                                "emotion": new_emotion,
                                "lighting": new_lighting
                            }
                        )
                        ShotService.update_shot(db, shot.id, {
                            "image_prompt": recompiled_img,
                            "video_prompt": recompiled_vid
                        })
                        st.success("Prompts recompiled from production bible!")
                        st.rerun()

                    if approve_shot_btn:
                        ShotService.update_shot(db, shot.id, {"status": ShotStatus.APPROVED.value})
                        st.success(f"Shot {shot.shot_number} approved!")
                        st.rerun()

                    if delete_shot_btn:
                        ShotService.delete_shot(db, shot.id)
                        st.warning(f"Deleted Shot {shot.shot_number}!")
                        st.rerun()

        # Global Shotlist Approval
        st.markdown("---")
        all_shots = ShotService.list_shots_by_project(db, project.id)
        app1, app2 = st.columns([3, 1.5])
        with app1:
            st.info(f"📊 Project-wide: **{len(all_shots)} total shots** configured across {len(scenes)} scenes.")
        with app2:
            if st.button("🔒 Approve All Shots & Lock Shotlist", use_container_width=True, type="primary"):
                ShotService.approve_all_shots_for_project(db, project.id)
                st.balloons()
                st.success(f"Project status transitioned to '{ProjectStatus.SHOTS_READY.value}'! Ready for Phase 4 Image Generation.")
                st.rerun()

if __name__ == "__main__":
    render_shots_page()
