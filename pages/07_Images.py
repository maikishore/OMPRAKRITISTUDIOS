import sys
import io
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from PIL import Image
from core.database import get_db_session
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.location_service import LocationService
from core.style_service import StyleService
from core.scene_service import SceneService
from core.shot_service import ShotService
from core.asset_service import AssetService
from providers.image.factory import get_image_provider
from providers.image.base import ImageGenerationRequest
from core.enums import AssetType, ShotStatus
from core.models import Asset

st.set_page_config(page_title="Image Generation & Asset Gallery | MicroDrama Studio", page_icon="🖼️", layout="wide")

def render_images_page():
    st.title("🖼️ Image Generation & Master Asset Studio")
    st.caption("Generate Master Character Portraits (Face-Lock), Environment Concept Stills, and Shot Keyframes with Modal GPU (FLUX.1 [dev] / IP-Adapter).")

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

        characters = CharacterService.list_characters_by_project(db, project.id)
        locations = LocationService.list_locations_by_project(db, project.id)
        scenes = SceneService.list_scenes_by_project(db, project.id)
        style = StyleService.get_style_by_project(db, project.id)

        # Global Provider Selector Bar
        prov_col1, prov_col2, prov_col3 = st.columns([2, 1.5, 1.5])
        with prov_col1:
            provider_choice = st.selectbox(
                "Active Image Generation Backend",
                options=["modal", "cloudflare", "mock"],
                format_func=lambda x: {
                    "modal": "🚀 Modal Serverless GPU (FLUX.1 [dev] + IP-Adapter Face-Lock)",
                    "cloudflare": "⚡ Cloudflare Workers AI (@cf/black-forest-labs/flux-1-schnell)",
                    "mock": "🛠️ Local GPU Emulation / Mock (Instant Testing)"
                }.get(x, x),
                index=0
            )
        with prov_col2:
            st.metric("Total Project Assets", len(AssetService.list_assets_by_project(db, project.id)))
        with prov_col3:
            st.metric("Visual Style", "Locked & Active" if (style and style.is_approved) else "Draft")

        st.markdown("---")

        tab_chars, tab_locs, tab_shots, tab_gallery = st.tabs([
            "👤 Character Master References",
            "📍 Location Master References",
            "🎞️ Shot Keyframes (Face-Locked)",
            "🖼️ Studio Asset Gallery"
        ])

        # -------------------------------------------------------------
        # TAB 1: CHARACTER MASTER REFERENCES
        # -------------------------------------------------------------
        with tab_chars:
            st.subheader("👤 Character Identity & Master Visual References")
            st.caption("Generate ultra-consistent master reference portraits for each character. Once approved, this master face is injected into all downstream shots via IP-Adapter.")

            if not characters:
                st.info("No characters created yet. Please create characters on Page 02 Characters.")
            else:
                char_map = {c.id: c.name for c in characters}
                selected_char_id = st.selectbox("Select Character to Generate", options=list(char_map.keys()), format_func=lambda x: char_map[x], key="char_select_box")
                character = CharacterService.get_character(db, selected_char_id)

                if character:
                    c_col1, c_col2 = st.columns([2, 2])
                    with c_col1:
                        st.markdown(f"**Character:** {character.name} ({character.role or 'Protagonist'})")
                        st.markdown(f"**Physical Traits:** {getattr(character, 'physical_traits', character.appearance or 'N/A')}")
                        st.markdown(f"**Costume:** {getattr(character, 'signature_costume', character.clothing or 'N/A')}")

                        char_prompt = st.text_area(
                            "Master Portrait Prompt",
                            value=character.identity_prompt or f"Cinematic 35mm portrait photograph of {character.name}, {character.appearance}, wearing {character.clothing}, soft chiaroscuro lighting, 8k resolution, raw photo.",
                            height=120,
                            key=f"char_prompt_{character.id}"
                        )

                        p_c1, p_c2 = st.columns(2)
                        with p_c1:
                            char_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=42, key=f"char_seed_{character.id}")
                        with p_c2:
                            char_steps = st.slider("Inference Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"char_steps_{character.id}")

                        if st.button("✨ Generate Character Reference", type="primary", use_container_width=True, key=f"gen_btn_char_{character.id}"):
                            with st.spinner(f"Generating high-fidelity portrait for {character.name} using {provider_choice.upper()}..."):
                                provider = get_image_provider(provider_choice)
                                req = ImageGenerationRequest(
                                    prompt=char_prompt,
                                    width=768,
                                    height=1344,
                                    num_inference_steps=char_steps,
                                    seed=int(char_seed)
                                )
                                res = provider.generate(req)
                                saved_asset = AssetService.save_image_asset(
                                    db=db,
                                    project_id=project.id,
                                    asset_type=AssetType.CHARACTER_REFERENCE.value,
                                    image_bytes=res.image_bytes,
                                    prompt=char_prompt,
                                    seed=int(char_seed),
                                    provider=provider_choice,
                                    model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]"
                                )
                                st.success(f"Generated and stored reference asset `{saved_asset.id[:8]}`!")
                                st.rerun()

                    with c_col2:
                        st.markdown("#### Master Visual Reference Status")
                        master_asset = AssetService.get_asset(db, character.master_reference_asset_id) if character.master_reference_asset_id else None

                        if master_asset and Path(master_asset.file_path).exists():
                            st.image(master_asset.file_path, caption=f"⭐ APPROVED MASTER FACE: {character.name}", use_container_width=True)
                            st.success("✅ This image is active as the master reference for IP-Adapter face locking.")
                            if st.button("🗑️ Delete Master Reference", key=f"del_master_char_{master_asset.id}"):
                                AssetService.delete_asset(db, master_asset.id)
                                st.success(f"Deleted master reference for {character.name}.")
                                st.rerun()
                        else:
                            st.warning("⚠️ No approved master reference asset set for this character.")

                        # Show recent candidate portraits
                        recent_char_assets = db.query(Asset).filter(
                            Asset.project_id == project.id,
                            Asset.type == AssetType.CHARACTER_REFERENCE.value
                        ).order_by(Asset.created_at.desc()).limit(6).all() if characters else []

                        if recent_char_assets:
                            st.markdown("##### Candidate Reference Images")
                            for cand in recent_char_assets:
                                if Path(cand.file_path).exists():
                                    st.image(cand.file_path, width=220)
                                    cand_b1, cand_b2 = st.columns([3, 1])
                                    with cand_b1:
                                        if st.button(f"⭐ Set Master ({cand.id[:6]})", key=f"set_master_char_{cand.id}"):
                                            AssetService.set_character_master_reference(db, character.id, cand.id)
                                            st.success(f"Locked {character.name}'s master face to asset `{cand.id[:8]}`!")
                                            st.rerun()
                                    with cand_b2:
                                        if st.button("🗑️", key=f"del_char_cand_{cand.id}", help="Delete this image"):
                                            AssetService.delete_asset(db, cand.id)
                                            st.success(f"Deleted asset {cand.id[:6]}.")
                                            st.rerun()

        # -------------------------------------------------------------
        # TAB 2: LOCATION MASTER REFERENCES
        # -------------------------------------------------------------
        with tab_locs:
            st.subheader("📍 Location Environments & Concept Stills")
            st.caption("Generate master architectural concept stills for staging environments to maintain spatial and lighting continuity.")

            if not locations:
                st.info("No locations found. Please configure locations on Page 03 Locations.")
            else:
                loc_map = {l.id: l.name for l in locations}
                selected_loc_id = st.selectbox("Select Location to Generate", options=list(loc_map.keys()), format_func=lambda x: loc_map[x], key="loc_select_box")
                loc = LocationService.get_location(db, selected_loc_id)

                if loc:
                    l_col1, l_col2 = st.columns([2, 2])
                    with l_col1:
                        st.markdown(f"**Environment:** {loc.name}")
                        st.markdown(f"**Architecture:** {loc.architecture or 'Modern commercial'}")
                        st.markdown(f"**Lighting:** {loc.lighting or 'Commercial lighting'}")

                        loc_prompt = st.text_area(
                            "Environment Concept Prompt",
                            value=loc.visual_identity or f"Wide architectural concept photograph of {loc.name}, {loc.architecture}, {loc.materials}, lighting: {loc.lighting}, cinematic composition, 8k resolution, raw photo.",
                            height=120,
                            key=f"loc_prompt_{loc.id}"
                        )

                        lp_c1, lp_c2 = st.columns(2)
                        with lp_c1:
                            loc_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=108, key=f"loc_seed_{loc.id}")
                        with lp_c2:
                            loc_steps = st.slider("Inference Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"loc_steps_{loc.id}")

                        if st.button("✨ Generate Location Reference", type="primary", use_container_width=True, key=f"gen_btn_loc_{loc.id}"):
                            with st.spinner(f"Generating concept still for {loc.name} using {provider_choice.upper()}..."):
                                provider = get_image_provider(provider_choice)
                                req = ImageGenerationRequest(
                                    prompt=loc_prompt,
                                    width=1024,
                                    height=576 if project.aspect_ratio == "16:9" else 1344,
                                    num_inference_steps=loc_steps,
                                    seed=int(loc_seed)
                                )
                                res = provider.generate(req)
                                saved_asset = AssetService.save_image_asset(
                                    db=db,
                                    project_id=project.id,
                                    asset_type=AssetType.LOCATION_REFERENCE.value,
                                    image_bytes=res.image_bytes,
                                    prompt=loc_prompt,
                                    seed=int(loc_seed),
                                    provider=provider_choice,
                                    model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]"
                                )
                                st.success(f"Generated and stored environment reference `{saved_asset.id[:8]}`!")
                                st.rerun()

                    with l_col2:
                        st.markdown("#### Master Location Reference Status")
                        master_loc_asset = AssetService.get_asset(db, loc.master_reference_asset_id) if loc.master_reference_asset_id else None

                        if master_loc_asset and Path(master_loc_asset.file_path).exists():
                            st.image(master_loc_asset.file_path, caption=f"⭐ APPROVED MASTER ENVIRONMENT: {loc.name}", use_container_width=True)
                            st.success("✅ This image is active as the master environment reference.")
                            if st.button("🗑️ Delete Master Reference", key=f"del_master_loc_{master_loc_asset.id}"):
                                AssetService.delete_asset(db, master_loc_asset.id)
                                st.success(f"Deleted master location reference for {loc.name}.")
                                st.rerun()
                        else:
                            st.warning("⚠️ No approved master reference asset set for this location.")

                        # Show recent candidate location stills
                        recent_loc_assets = db.query(Asset).filter(
                            Asset.project_id == project.id,
                            Asset.type == AssetType.LOCATION_REFERENCE.value
                        ).order_by(Asset.created_at.desc()).limit(6).all() if locations else []

                        if recent_loc_assets:
                            st.markdown("##### Candidate Location Images")
                            for cand in recent_loc_assets:
                                if Path(cand.file_path).exists():
                                    st.image(cand.file_path, width=220)
                                    cand_l1, cand_l2 = st.columns([3, 1])
                                    with cand_l1:
                                        if st.button(f"⭐ Set Master ({cand.id[:6]})", key=f"set_master_loc_{cand.id}"):
                                            AssetService.set_location_master_reference(db, loc.id, cand.id)
                                            st.success(f"Locked {loc.name}'s master environment to asset `{cand.id[:8]}`!")
                                            st.rerun()
                                    with cand_l2:
                                        if st.button("🗑️", key=f"del_loc_cand_{cand.id}", help="Delete this image"):
                                            AssetService.delete_asset(db, cand.id)
                                            st.success(f"Deleted asset {cand.id[:6]}.")
                                            st.rerun()

        # -------------------------------------------------------------
        # TAB 3: SHOT KEYFRAMES (FACE-LOCKED)
        # -------------------------------------------------------------
        with tab_shots:
            st.subheader("🎞️ Shot Keyframe Generation & Face-Locking")
            st.caption("Generate high-fidelity initial keyframes for each shot. Automatically passes approved Character Master Portraits into IP-Adapter for zero face drift.")

            if not scenes:
                st.info("No scenes found. Please configure scenes on Page 05 Scenes.")
            else:
                scene_map = {s.id: f"Scene {s.scene_number:02d}: {s.title} ({len(s.shots)} Shots)" for s in scenes}
                selected_sc_id = st.selectbox("Select Scene", options=list(scene_map.keys()), format_func=lambda x: scene_map[x], key="sc_kf_select")
                active_scene = SceneService.get_scene(db, selected_sc_id)
                scene_shots = ShotService.list_shots_by_scene(db, active_scene.id) if active_scene else []

                if not scene_shots:
                    st.info("No shots in this scene. Please generate shots on Page 06 Shots.")
                else:
                    shot_map = {sh.id: f"Shot {sh.shot_number:02d}: [{sh.shot_type}] {sh.camera_movement} ({sh.duration_seconds}s)" for sh in scene_shots}
                    selected_sh_id = st.selectbox("Select Shot to Generate Keyframe", options=list(shot_map.keys()), format_func=lambda x: shot_map[x], key="sh_kf_select")
                    shot = ShotService.get_shot(db, selected_sh_id)

                    if shot:
                        sh_col1, sh_col2 = st.columns([2, 2])
                        with sh_col1:
                            st.markdown(f"**Shot {shot.shot_number:02d} Action:** {shot.action}")
                            st.markdown(f"**Camera / Lens:** {shot.shot_type}, {shot.camera_angle}, {shot.lens}")
                            st.markdown(f"**Characters in Frame:** {', '.join(shot.characters) if shot.characters else 'None'}")

                            # Check for Master References to inject
                            conditioning_refs = []
                            ref_descriptions = []
                            for ch_name in shot.characters:
                                for ch in characters:
                                    if ch.name.lower() == ch_name.lower() and ch.master_reference_asset_id:
                                        m_asset = AssetService.get_asset(db, ch.master_reference_asset_id)
                                        if m_asset and Path(m_asset.file_path).exists():
                                            with open(m_asset.file_path, "rb") as rf:
                                                conditioning_refs.append(rf.read())
                                                ref_descriptions.append(f"🔒 {ch.name} Master Face (Asset `{m_asset.id[:8]}`)")

                            if ref_descriptions:
                                st.success(f"**Active Conditioning:** {', '.join(ref_descriptions)}")
                            else:
                                st.info("ℹ️ No master character face references found; generating from raw prompt.")

                            kf_prompt = st.text_area(
                                "Compiled Keyframe Image Prompt",
                                value=shot.image_prompt or "Cinematic shot...",
                                height=130,
                                key=f"kf_prompt_{shot.id}"
                            )

                            kf_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=42 + shot.shot_number, key=f"kf_seed_{shot.id}")

                            if st.button("🚀 Generate Shot Keyframe", type="primary", use_container_width=True, key=f"gen_kf_{shot.id}"):
                                with st.spinner(f"Generating Keyframe for Shot {shot.shot_number:02d} on {provider_choice.upper()}..."):
                                    provider = get_image_provider(provider_choice)
                                    req = ImageGenerationRequest(
                                        prompt=kf_prompt,
                                        width=768,
                                        height=1344,
                                        num_inference_steps=28 if provider_choice == "modal" else 4,
                                        seed=int(kf_seed),
                                        reference_images=conditioning_refs
                                    )
                                    res = provider.generate(req)
                                    saved_kf = AssetService.save_image_asset(
                                        db=db,
                                        project_id=project.id,
                                        asset_type=AssetType.KEYFRAME.value,
                                        image_bytes=res.image_bytes,
                                        prompt=kf_prompt,
                                        seed=int(kf_seed),
                                        provider=provider_choice,
                                        model="FLUX.1 [dev] + IP-Adapter" if provider_choice == "modal" else "FLUX.1 [schnell]"
                                    )
                                    AssetService.link_shot_keyframe(db, shot.id, saved_kf.id)
                                    st.success(f"Generated & Linked Keyframe `{saved_kf.id[:8]}` to Shot {shot.shot_number:02d}!")
                                    st.rerun()

                        with sh_col2:
                            st.markdown("#### Shot Keyframe Status")
                            linked_kf = None
                            if shot.reference_asset_ids:
                                linked_kf = AssetService.get_asset(db, shot.reference_asset_ids[-1])

                            if linked_kf and Path(linked_kf.file_path).exists():
                                st.image(linked_kf.file_path, caption=f"Keyframe: Scene {active_scene.scene_number:02d} - Shot {shot.shot_number:02d} ({shot.status})", use_container_width=True)
                                st.success(f"✅ Shot status: **{shot.status}**")
                                if st.button("🗑️ Delete Shot Keyframe", key=f"del_shot_kf_{linked_kf.id}"):
                                    AssetService.delete_asset(db, linked_kf.id)
                                    st.success(f"Deleted keyframe and reset Shot {shot.shot_number:02d} to Draft.")
                                    st.rerun()
                            else:
                                st.warning("No keyframe generated for this shot yet.")

        # -------------------------------------------------------------
        # TAB 4: STUDIO ASSET GALLERY
        # -------------------------------------------------------------
        with tab_gallery:
            st.subheader("🖼️ Studio Asset Gallery & Image Inspector")
            all_assets = AssetService.list_assets_by_project(db, project.id)

            if not all_assets:
                st.info("No generated assets in this project yet.")
            else:
                f_col1, f_col2 = st.columns([2, 2])
                with f_col1:
                    type_filter = st.multiselect(
                        "Filter by Asset Type",
                        options=[AssetType.CHARACTER_REFERENCE.value, AssetType.LOCATION_REFERENCE.value, AssetType.KEYFRAME.value],
                        default=[AssetType.CHARACTER_REFERENCE.value, AssetType.LOCATION_REFERENCE.value, AssetType.KEYFRAME.value]
                    )

                filtered = [a for a in all_assets if a.type in type_filter]
                st.caption(f"Showing **{len(filtered)} assets**")

                cols = st.columns(3)
                for idx, asset in enumerate(filtered):
                    col = cols[idx % 3]
                    with col:
                        if Path(asset.file_path).exists():
                            st.image(asset.file_path, use_container_width=True)
                            approved_tag = "⭐ MASTER / APPROVED" if asset.is_approved else "Draft"
                            st.caption(f"**{asset.type.upper()}** | `{asset.id[:8]}` | {approved_tag}")
                            with st.expander("🔍 View Prompt & Specs"):
                                st.write(f"**Prompt:** {asset.prompt}")
                                st.write(f"**Model:** {asset.model} ({asset.provider})")
                                st.write(f"**Seed:** {asset.seed} | **Resolution:** {asset.width}x{asset.height}")
                            if st.button("🗑️ Delete Asset", key=f"del_gal_asset_{asset.id}", use_container_width=True):
                                AssetService.delete_asset(db, asset.id)
                                st.success(f"Deleted asset `{asset.id[:8]}`.")
                                st.rerun()
                        else:
                            st.caption(f"Asset `{asset.id[:8]}` (File missing on disk)")
                            if st.button("🗑️ Clean Orphan DB Record", key=f"del_orphan_{asset.id}", use_container_width=True):
                                AssetService.delete_asset(db, asset.id)
                                st.rerun()

if __name__ == "__main__":
    render_images_page()
