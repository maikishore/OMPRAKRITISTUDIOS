import io
import os
import sys
import time
from pathlib import Path
from typing import Optional, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from PIL import Image

from core.database import ScopedSession
from core.project_service import ProjectService
from core.scene_service import SceneService
from core.shot_service import ShotService
from core.asset_service import AssetService
from core.modal_service import ModalService
from core.models import Asset, Shot
from core.enums import AssetType, ShotStatus
from providers.image.factory import ImageProviderFactory
from providers.image.base import ImageGenerationRequest
from providers.video.factory import VideoProviderFactory
from providers.video.base import VideoGenerationRequest
from core.auth_gate import require_auth

st.set_page_config(
    page_title="Video Studio & Modal GPU Control | MicroDrama Studio",
    page_icon="📹",
    layout="wide"
)

if not require_auth():
    st.stop()

# -----------------------------------------------------------------------------
# TOP BANNER: MODAL SERVERLESS GPU CONTROL & INACTIVITY AUTO-SHUTDOWN
# -----------------------------------------------------------------------------
st.title("📹 Video Studio & Modal GPU Playground")
st.caption("Practice end-to-end Text-to-Image-to-Video generation, manage Modal GPU deployment, and configure auto-shutdown timers.")

with st.expander("⚡ **Modal Serverless GPU Control Panel & Auto-Shutdown Settings**", expanded=False):
    c_m1, c_m2, c_m3, c_m4 = st.columns([2, 1.5, 1.5, 1.5])
    
    with c_m1:
        profile = ModalService.get_current_profile()
        is_video_dep, video_data = ModalService.is_app_deployed("microdrama-studio-video")
        is_img_dep, img_data = ModalService.is_app_deployed("microdrama-studio-image")
        
        status_video_str = "🟢 Ready / Deployed" if is_video_dep else "⚪ Stopped / Standby"
        status_img_str = "🟢 Ready / Deployed" if is_img_dep else "⚪ Stopped / Standby"
        
        st.markdown(f"**Modal Profile:** `{profile or 'Local / Not Logged In'}`")
        st.markdown(f"**Video Worker (`LTX/Wan`):** {status_video_str}")
        st.markdown(f"**Image Worker (`FLUX`):** {status_img_str}")

    with c_m2:
        inactivity_mins = st.selectbox(
            "⏳ Inactivity Auto-Shutdown",
            options=[5, 10, 15, 30, 60],
            index=2,  # 15 minutes default
            help="If no generation requests arrive within this time window, Modal automatically terminates the GPU instance to ensure zero idle cost."
        )
        st.caption(f"GPU stops billing after **{inactivity_mins} mins** of inactivity.")

    with c_m3:
        if st.button("🚀 Deploy Video Worker", use_container_width=True, type="primary"):
            with st.spinner(f"Deploying `modal/video_worker.py` (Inactivity timeout: {inactivity_mins}m)..."):
                success, logs = ModalService.deploy_worker(
                    "modal/video_worker.py",
                    root_dir=ROOT_DIR,
                    inactivity_timeout_minutes=inactivity_mins
                )
                if success:
                    st.success("✅ Video worker deployed successfully!")
                    with st.expander("View Deployment Logs"):
                        st.code(logs)
                    st.rerun()
                else:
                    st.error("Deployment failed.")
                    st.code(logs)

    with c_m4:
        if st.button("🛑 Stop GPU Now", use_container_width=True, disabled=not is_video_dep):
            with st.spinner("Stopping `microdrama-studio-video` on Modal..."):
                ok, msg = ModalService.stop_app("microdrama-studio-video")
                if ok:
                    st.success("Stopped GPU worker to save credits.")
                    st.rerun()
                else:
                    st.error(msg)

st.markdown("---")

# -----------------------------------------------------------------------------
# MAIN WORKSPACE TABS
# -----------------------------------------------------------------------------
tab_t2v, tab_i2v, tab_prod = st.tabs([
    "🎥 1. Text-to-Video (LTX-2.5 Multimodal)",
    "🧪 2. Text-to-Image-to-Video Practice Lab",
    "🎬 3. Project Shot Video Production"
])

# =============================================================================
# TAB 1: TEXT-TO-VIDEO (LTX-2.5 MULTIMODAL FOUNDATION)
# =============================================================================
with tab_t2v:
    st.subheader("🎥 Text-to-Video Studio (Lightricks LTX-2.5)")
    st.write("Generate high-fidelity cinematic video clips with natively synchronized audio directly from text descriptions.")

    t2v_col_left, t2v_col_right = st.columns([1, 1], gap="large")

    with t2v_col_left:
        t2v_presets = [
            "A cinematic medium close-up of a stylish detective turning head slowly under rain, neon blue reflections, footsteps on wet asphalt, 8k",
            "An elegant woman in an evening gown entering a lavish ballroom, camera tracking forward smoothly, murmuring guests in background",
            "A lone traveler walking across a windswept desert at golden hour, sand blowing in breeze, cinematic wide anamorphic",
            "Cyberpunk motorcycle speeding through a high-tech illuminated tunnel, motion blur, engine roar, dramatic lens flare"
        ]
        t2v_sel_preset = st.selectbox("💡 Cinematic Presets", ["(Custom Prompt)"] + t2v_presets, key="t2v_preset_sel")
        t2v_def_prompt = t2v_sel_preset if t2v_sel_preset != "(Custom Prompt)" else (
            st.session_state.get("t2v_prompt") or t2v_presets[0]
        )
        t2v_prompt = st.text_area("Video Scene Prompt", value=t2v_def_prompt, height=90, key="t2v_prompt_input")
        t2v_neg_prompt = st.text_input(
            "Negative Prompt",
            value="blurry, distorted, jitter, bad anatomy, watermark, low quality",
            key="t2v_neg_prompt_input"
        )

        c_t2v_cam, c_t2v_ar = st.columns(2)
        with c_t2v_cam:
            t2v_camera = st.selectbox(
                "Camera Movement",
                ["Slow Push-In (Dolly)", "Smooth Pan Left", "Smooth Pan Right", "Tracking Shot", "Dynamic Orbit", "Handheld Realism", "Static Lock"],
                key="t2v_cam_sel"
            )
        with c_t2v_ar:
            t2v_ar = st.selectbox("Aspect Ratio", ["16:9 (Widescreen 960x544)", "9:16 (Vertical 544x960)", "1:1 (Square 512x512)"], key="t2v_ar_sel")
            if "16:9" in t2v_ar:
                t2v_w, t2v_h = 960, 544
            elif "9:16" in t2v_ar:
                t2v_w, t2v_h = 544, 960
            else:
                t2v_w, t2v_h = 512, 512

        c_t2v_dur, c_t2v_prov = st.columns(2)
        with c_t2v_dur:
            t2v_frames = st.select_slider(
                "Frames / Duration",
                options=[48, 72, 97, 121],
                value=72,
                format_func=lambda x: f"{x} frames (~{round(x/24, 1)}s)",
                key="t2v_frames_sel"
            )
        with c_t2v_prov:
            t2v_provider_choice = st.selectbox("Video Engine Backend", ["auto", "modal", "mock"], key="t2v_prov_sel")

        t2v_sync_audio = st.checkbox("🔊 Generate Synchronized Audio Effects (LTX-2.5)", value=True, key="t2v_audio_cb")

        if st.button("🎬 Generate Text-to-Video", type="primary", use_container_width=True, key="t2v_gen_btn"):
            full_prompt = f"{t2v_prompt}, camera {t2v_camera.lower()}, cinematic lighting, hyper-realistic"
            with st.spinner(f"Generating {t2v_frames} frames ({t2v_camera}) on LTX-2.5..."):
                try:
                    vid_prov = VideoProviderFactory.get_provider(t2v_provider_choice)
                    t2v_req = VideoGenerationRequest(
                        prompt=full_prompt,
                        negative_prompt=t2v_neg_prompt,
                        width=t2v_w,
                        height=t2v_h,
                        fps=24,
                        num_frames=t2v_frames,
                        num_inference_steps=30,
                        guidance_scale=3.5,
                        seed=42,
                        parameters={"audio": t2v_sync_audio, "engine": "LTX-2.5"}
                    )
                    t0 = time.time()
                    v_res = vid_prov.generate(t2v_req)
                    dt = round(time.time() - t0, 2)
                    st.session_state["t2v_video_bytes"] = v_res.video_bytes
                    st.session_state["t2v_video_duration"] = v_res.duration
                    st.session_state["t2v_video_latency"] = dt
                    st.success(f"✅ Text-to-Video rendered in {dt}s ({v_res.duration}s clip)!")
                except Exception as e:
                    st.error(f"Generation error: {e}")

    with t2v_col_right:
        st.markdown("### 📺 Rendered Video Player")
        t2v_bytes = st.session_state.get("t2v_video_bytes")
        if t2v_bytes:
            st.video(t2v_bytes)
            spec_col1, spec_col2 = st.columns(2)
            with spec_col1:
                st.caption(f"⏱️ Duration: **{st.session_state.get('t2v_video_duration', 0)}s**")
                st.caption(f"⚡ Generation Time: **{st.session_state.get('t2v_video_latency', 0)}s**")
            with spec_col2:
                st.caption(f"📐 Resolution: **{t2v_w}x{t2v_h}**")
                st.caption("🔊 Audio: **Synchronized**" if t2v_sync_audio else "🔇 Silent")

            st.download_button(
                "⬇️ Download Video (MP4)",
                data=t2v_bytes,
                file_name="ltx25_text_to_video.mp4",
                mime="video/mp4",
                use_container_width=True,
                key="t2v_dl_btn"
            )
        else:
            st.info("Rendered video preview will appear here once generated.")

# =============================================================================
# TAB 2: TEXT-TO-IMAGE-TO-VIDEO PRACTICE LAB
# =============================================================================
with tab_i2v:
    st.subheader("🧪 Practice Lab: Text ➡️ Keyframe Image ➡️ Video Clip")
    st.write("Generate a deterministic high-fidelity keyframe from text, then animate it into a coherent video clip with camera dynamics.")

    col_left, col_right = st.columns([1, 1], gap="large")

    # LEFT COLUMN: STAGE 1 (KEYFRAME GENERATION)
    with col_left:
        st.markdown("### 🖼️ Stage 1: Keyframe Image")
        
        prompt_presets = [
            "A cinematic medium close-up of a stylish cyberpunk detective standing in rain, neon blue and amber reflections, 8k photorealistic, hyper-detailed",
            "An elegant woman in a trench coat looking around a grand sunlit architectural atrium, cinematic lighting, shallow depth of field",
            "A dramatic close-up of a warrior turning head towards camera with intense focus, volumetric fog, dramatic rim lighting",
            "A vintage toy shop interior with warm tungsten practical lights, soft shadows, 35mm film grain"
        ]
        
        selected_preset = st.selectbox("💡 Prompt Presets (Optional)", ["(Custom Prompt)"] + prompt_presets)
        
        default_prompt = selected_preset if selected_preset != "(Custom Prompt)" else (
            st.session_state.get("practice_image_prompt") or prompt_presets[0]
        )
        
        practice_prompt = st.text_area(
            "Image Prompt (Text-to-Image)",
            value=default_prompt,
            height=100,
            key="practice_prompt_input"
        )
        
        c_ar, c_prov = st.columns(2)
        with c_ar:
            aspect_ratio_opt = st.selectbox("Aspect Ratio", ["16:9 (Widescreen)", "9:16 (Vertical)", "1:1 (Square)"])
            if "16:9" in aspect_ratio_opt:
                w, h = 768, 512
            elif "9:16" in aspect_ratio_opt:
                w, h = 512, 768
            else:
                w, h = 512, 512

        with c_prov:
            img_provider_choice = st.selectbox("Image Backend", ["auto", "modal", "cloudflare", "mock"], index=0)

        # Image generation trigger
        if st.button("✨ Step 1: Generate Keyframe Image", type="primary", use_container_width=True):
            with st.spinner("Generating Keyframe Image..."):
                try:
                    img_provider = ImageProviderFactory.get_provider(img_provider_choice)
                    req = ImageGenerationRequest(
                        prompt=practice_prompt,
                        width=w,
                        height=h,
                        num_inference_steps=28,
                        guidance_scale=4.0,
                        seed=42
                    )
                    res = img_provider.generate(req)
                    st.session_state["practice_image_bytes"] = res.image_bytes
                    st.session_state["practice_image_prompt"] = practice_prompt
                    st.success("✅ Keyframe generated successfully!")
                except Exception as e:
                    st.error(f"Image generation error: {e}")

        # Display Current Keyframe
        current_img_bytes = st.session_state.get("practice_image_bytes")
        if current_img_bytes:
            st.image(current_img_bytes, caption="Active Keyframe Image", use_container_width=True)
        else:
            st.info("👆 Click **'Generate Keyframe Image'** above to generate or preview the starting frame.")

    # RIGHT COLUMN: STAGE 2 (IMAGE-TO-VIDEO GENERATION)
    with col_right:
        st.markdown("### 🎬 Stage 2: Animate into Video Clip")
        
        vid_prompt = st.text_area(
            "Video Motion Prompt",
            value=st.session_state.get("practice_video_prompt") or f"{practice_prompt}, subtle cinematic movement, slow atmospheric drift",
            height=70,
            key="practice_video_prompt_input"
        )
        
        c_cam, c_mot = st.columns(2)
        with c_cam:
            camera_motion = st.selectbox(
                "Camera Movement",
                ["Slow Push-In (Dolly)", "Smooth Pan Left", "Smooth Pan Right", "Gentle Zoom Out", "Orbit Clockwise", "Static Lock"]
            )
        with c_mot:
            num_frames = st.select_slider(
                "Duration / Frames",
                options=[24, 48, 72, 97],
                value=48,
                format_func=lambda x: f"{x} frames (~{round(x/24, 1)}s)"
            )

        c_fps, c_vprov = st.columns(2)
        with c_fps:
            fps_val = st.selectbox("Frame Rate", [24, 30], index=0)
        with c_vprov:
            video_provider_choice = st.selectbox("Video Backend", ["auto", "modal", "mock"], index=0)

        # Video Generation Trigger
        gen_video_btn = st.button("🎥 Step 2: Generate Video (Image-to-Video)", type="primary", use_container_width=True)
        
        if gen_video_btn:
            if not current_img_bytes:
                st.warning("⚠️ Please generate a Keyframe Image in Stage 1 first!")
            else:
                with st.spinner(f"Synthesizing {num_frames} frames ({camera_motion}) on Video Engine..."):
                    try:
                        full_motion_prompt = f"{vid_prompt}, camera {camera_motion.lower()}, cinematic temporal coherence"
                        vid_provider = VideoProviderFactory.get_provider(video_provider_choice)
                        
                        v_req = VideoGenerationRequest(
                            prompt=full_motion_prompt,
                            start_frame_bytes=current_img_bytes,
                            width=w,
                            height=h,
                            fps=fps_val,
                            num_frames=num_frames,
                            num_inference_steps=30,
                            guidance_scale=3.5,
                            seed=42
                        )
                        
                        t0 = time.time()
                        v_res = vid_provider.generate(v_req)
                        dt = round(time.time() - t0, 2)
                        
                        st.session_state["practice_video_bytes"] = v_res.video_bytes
                        st.session_state["practice_video_duration"] = v_res.duration
                        st.session_state["practice_video_latency"] = dt
                        st.success(f"✅ Video generated in {dt}s ({v_res.duration}s clip)!")
                    except Exception as e:
                        st.error(f"Video synthesis error: {e}")

        # Display Generated Video
        current_vid_bytes = st.session_state.get("practice_video_bytes")
        if current_vid_bytes:
            st.video(current_vid_bytes)
            st.download_button(
                "⬇️ Download Video (MP4)",
                data=current_vid_bytes,
                file_name="practice_shot_video.mp4",
                mime="video/mp4",
                use_container_width=True
            )
        else:
            st.info("Rendered video preview will appear here once generated.")


# =============================================================================
# TAB 2: PROJECT SHOT VIDEO PRODUCTION
# =============================================================================
with tab_prod:
    st.subheader("🎬 Project Shot Production Video Pipeline")
    
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        st.warning("⚠️ No active project selected. Select a project from the sidebar to produce scene videos.")
    else:
        db = ScopedSession()
        try:
            project = ProjectService.get_project(db, project_id)
            st.markdown(f"**Active Project:** `{project.title}` | **Aspect Ratio:** `{project.aspect_ratio}`")
            
            scenes = SceneService.list_scenes_by_project(db, project_id)
            if not scenes:
                st.info("No scenes found in this project. Create scenes in **05. Scenes** first.")
            else:
                for sc in scenes:
                    with st.expander(f"🎬 Scene {sc.scene_number}: {sc.title or 'Untitled Scene'}", expanded=True):
                        shots = ShotService.list_shots_by_scene(db, sc.id)
                        if not shots:
                            st.caption("No shots in this scene. Decompose in **06. Shots**.")
                            continue

                        for sh in shots:
                            sh_col1, sh_col2, sh_col3 = st.columns([1, 1.5, 1.5])
                            
                            # Col 1: Approved Keyframe
                            with sh_col1:
                                st.markdown(f"**Shot {sh.shot_number}** ({sh.shot_type or 'Medium'})")
                                # Find keyframe asset
                                keyframe_asset = None
                                if sh.reference_asset_ids:
                                    for a_id in sh.reference_asset_ids:
                                        a = db.query(Asset).filter(Asset.id == a_id, Asset.type == AssetType.KEYFRAME.value).first()
                                        if a:
                                            keyframe_asset = a
                                            break
                                
                                if keyframe_asset and Path(keyframe_asset.file_path).exists():
                                    st.image(keyframe_asset.file_path, use_container_width=True)
                                else:
                                    st.info("No keyframe rendered yet (Go to **07. Images**)")

                            # Col 2: Motion Prompt & Settings
                            with sh_col2:
                                st.caption(f"**Camera Movement:** `{sh.camera_movement or 'Static'}` | **Angle:** `{sh.camera_angle or 'Eye-level'}`")
                                st.caption(f"**Action:** {sh.action or 'None'}")
                                
                                default_vid_prompt = sh.video_prompt or f"{sh.action or ''}, camera {sh.camera_movement or 'smooth pan'}, cinematic 8k"
                                shot_vid_prompt = st.text_area(
                                    f"Motion Prompt (Shot {sh.shot_number})",
                                    value=default_vid_prompt,
                                    height=80,
                                    key=f"shot_vprompt_{sh.id}"
                                )

                            # Col 3: Video Render Action & Player
                            with sh_col3:
                                # Check if video asset already exists
                                video_asset = db.query(Asset).filter(
                                    Asset.project_id == project_id,
                                    Asset.type == AssetType.VIDEO_CLIP.value,
                                    Asset.parameters.contains({"shot_id": sh.id})
                                ).first()

                                if st.button(f"🎬 Render Shot {sh.shot_number} Video", key=f"render_vid_btn_{sh.id}", use_container_width=True):
                                    with st.spinner(f"Generating video for Shot {sh.shot_number}..."):
                                        try:
                                            # Read keyframe bytes if available
                                            kf_bytes = None
                                            if keyframe_asset and Path(keyframe_asset.file_path).exists():
                                                with open(keyframe_asset.file_path, "rb") as kf_f:
                                                    kf_bytes = kf_f.read()

                                            v_prov = VideoProviderFactory.get_provider("auto")
                                            v_req = VideoGenerationRequest(
                                                prompt=shot_vid_prompt,
                                                start_frame_bytes=kf_bytes,
                                                num_frames=48,
                                                fps=24,
                                                seed=42
                                            )
                                            v_res = v_prov.generate(v_req)
                                            
                                            # Save video asset
                                            saved_asset = AssetService.save_asset(
                                                db=db,
                                                project_id=project_id,
                                                asset_type=AssetType.VIDEO_CLIP,
                                                file_data=v_res.video_bytes,
                                                mime_type="video/mp4",
                                                filename=f"shot_{sc.scene_number}_{sh.shot_number}_video.mp4",
                                                provider="modal_video",
                                                model="LTX-Video",
                                                prompt=shot_vid_prompt,
                                                parameters={"shot_id": sh.id, "duration": v_res.duration}
                                            )
                                            st.success("✅ Shot video rendered and saved to asset library!")
                                            st.rerun()
                                        except Exception as e_v:
                                            st.error(f"Render failed: {e_v}")

                                if video_asset and Path(video_asset.file_path).exists():
                                    st.video(video_asset.file_path)
                                else:
                                    st.caption("No video clip rendered yet.")

        finally:
            db.close()
