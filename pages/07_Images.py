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
from core.character_sheet_service import CharacterSheetService
from core.location_sheet_service import LocationSheetService

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
        # TAB 1: CHARACTER MASTER REFERENCES & MODEL SHEETS
        # -------------------------------------------------------------
        with tab_chars:
            st.subheader("👤 Character Master Reference & Expression Matrix")
            st.caption("Generate multi-angle model sheets, 360° turnarounds, and emotional expression matrices with FLUX to anchor downstream video models.")

            if not characters:
                st.info("No characters created yet. Please create characters on Page 02 Characters.")
            else:
                char_map = {c.id: c.name for c in characters}
                selected_char_id = st.selectbox("Select Active Character", options=list(char_map.keys()), format_func=lambda x: char_map[x], key="char_select_box")
                character = CharacterService.get_character(db, selected_char_id)

                if character:
                    # 1. CHARACTER HEADER OVERVIEW & MASTER BANNER
                    with st.container(border=True):
                        h_c1, h_c2, h_c3 = st.columns([1.5, 2.5, 1.5])
                        with h_c1:
                            st.markdown(f"### {character.name}")
                            st.caption(f"**Role:** {character.role or 'Protagonist'}")
                        with h_c2:
                            st.markdown(f"**Physical Appearance:** {getattr(character, 'physical_traits', character.appearance or 'N/A')}")
                            st.markdown(f"**Signature Costume:** {getattr(character, 'signature_costume', character.clothing or 'N/A')}")
                        with h_c3:
                            master_asset = AssetService.get_asset(db, character.master_reference_asset_id) if character.master_reference_asset_id else None
                            if master_asset and Path(master_asset.file_path).exists():
                                st.success("⭐ **Master Face Locked**")
                                st.image(master_asset.file_path, width=90)
                            else:
                                st.warning("⚠️ No Master Face Set")

                    st.markdown("---")

                    # 2. GENERATION STUDIO (Single Preset or Batch Core Suite)
                    st.markdown("#### 🎨 Pose & Expression Generator Studio")
                    with st.container(border=True):
                        preset_list = CharacterSheetService.list_presets()
                        preset_map = {p["key"]: f"{p['name']} ({p['aspect_ratio']})" for p in preset_list}
                        
                        preset_sel_col, preset_desc_col = st.columns([2, 2])
                        with preset_sel_col:
                            selected_preset_key = st.selectbox(
                                "Select Pose / Angle / Expression Preset",
                                options=list(preset_map.keys()),
                                format_func=lambda x: preset_map[x],
                                key=f"preset_sel_{character.id}"
                            )
                        with preset_desc_col:
                            p_info = next((p for p in preset_list if p["key"] == selected_preset_key), {})
                            st.info(f"💡 {p_info.get('description', '')}")

                        compiled = CharacterSheetService.compile_prompt(character, selected_preset_key)

                        char_prompt = st.text_area(
                            f"Prompt for {compiled['preset_name']}",
                            value=compiled["prompt"],
                            height=100,
                            key=f"char_prompt_{character.id}_{selected_preset_key}"
                        )

                        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.2, 1.2, 1.2, 1.5])
                        with ctrl_col1:
                            char_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=42, key=f"seed_{character.id}_{selected_preset_key}")
                        with ctrl_col2:
                            char_steps = st.slider("Inference Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"steps_{character.id}_{selected_preset_key}")
                        with ctrl_col3:
                            st.text_input("Resolution", value=f"{compiled['width']}x{compiled['height']}", disabled=True)
                        with ctrl_col4:
                            st.write("") # vertical spacing
                            gen_preset_btn = st.button("✨ Render Pose / Angle", type="primary", use_container_width=True, key=f"gen_single_{character.id}_{selected_preset_key}")

                        if gen_preset_btn:
                            with st.spinner(f"Rendering {compiled['preset_name']} for {character.name} on {provider_choice.upper()}..."):
                                provider = get_image_provider(provider_choice)
                                req = ImageGenerationRequest(
                                    prompt=char_prompt,
                                    width=compiled["width"],
                                    height=compiled["height"],
                                    num_inference_steps=char_steps,
                                    seed=int(char_seed)
                                )
                                res = provider.generate(req)
                                saved_asset = AssetService.save_image_asset(
                                    db=db,
                                    project_id=project.id,
                                    asset_type=AssetType.CHARACTER_SHEET.value if "TURNAROUND" in selected_preset_key else AssetType.CHARACTER_REFERENCE.value,
                                    image_bytes=res.image_bytes,
                                    prompt=char_prompt,
                                    seed=int(char_seed),
                                    provider=provider_choice,
                                    model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                    parameters={
                                        "character_id": character.id,
                                        "character_name": character.name,
                                        "preset_key": selected_preset_key,
                                        "preset_name": compiled["preset_name"]
                                    }
                                )
                                if selected_preset_key == "MASTER_PORTRAIT" and not character.master_reference_asset_id:
                                    AssetService.set_character_master_reference(db, character.id, saved_asset.id)
                                st.success(f"Generated & Saved `{saved_asset.id[:8]}` ({compiled['preset_name']})!")
                                st.rerun()

                        # Batch suite expander
                        with st.expander("⚡ Batch Render: Core Character Suite (Master + Turnaround + Terror + Full Body)"):
                            st.caption("Automatically generates all 4 primary identity anchors sequentially for complete 360° video readiness.")
                            if st.button("🚀 Render All 4 Core Assets in Sequence", key=f"batch_suite_{character.id}"):
                                core_suite_keys = ["MASTER_PORTRAIT", "TURNAROUND_3ANGLE", "EXPRESSION_TERROR", "FULL_BODY_STANCE"]
                                progress_bar = st.progress(0)
                                provider = get_image_provider(provider_choice)
                                for idx, p_key in enumerate(core_suite_keys):
                                    c_spec = CharacterSheetService.compile_prompt(character, p_key)
                                    with st.spinner(f"Generating {c_spec['preset_name']} ({idx+1}/{len(core_suite_keys)})..."):
                                        r = provider.generate(ImageGenerationRequest(
                                            prompt=c_spec["prompt"],
                                            width=c_spec["width"],
                                            height=c_spec["height"],
                                            num_inference_steps=char_steps,
                                            seed=int(char_seed) + idx * 10
                                        ))
                                        sa = AssetService.save_image_asset(
                                            db=db,
                                            project_id=project.id,
                                            asset_type=AssetType.CHARACTER_SHEET.value if "TURNAROUND" in p_key else AssetType.CHARACTER_REFERENCE.value,
                                            image_bytes=r.image_bytes,
                                            prompt=c_spec["prompt"],
                                            seed=int(char_seed) + idx * 10,
                                            provider=provider_choice,
                                            model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                            parameters={
                                                "character_id": character.id,
                                                "character_name": character.name,
                                                "preset_key": p_key,
                                                "preset_name": c_spec["preset_name"]
                                            }
                                        )
                                        if p_key == "MASTER_PORTRAIT" and not character.master_reference_asset_id:
                                            AssetService.set_character_master_reference(db, character.id, sa.id)
                                    progress_bar.progress((idx + 1) / len(core_suite_keys))
                                st.success(f"🎉 Generated full Character Sheet Suite for {character.name}!")
                                st.rerun()

                    st.markdown("---")

                    # 3. CHARACTER VISUAL MATRIX & INDIVIDUAL POSE RE-GENERATION (FILTERED FOR THIS CHARACTER ONLY)
                    all_char_assets = db.query(Asset).filter(
                        Asset.project_id == project.id,
                        Asset.type.in_([AssetType.CHARACTER_REFERENCE.value, AssetType.CHARACTER_SHEET.value])
                    ).order_by(Asset.created_at.desc()).all() if characters else []

                    def is_for_character(a: Asset, c) -> bool:
                        params = a.parameters if isinstance(a.parameters, dict) else {}
                        if params.get("character_id") == c.id:
                            return True
                        if c.master_reference_asset_id == a.id:
                            return True
                        c_name_low = c.name.lower().strip()
                        param_name_low = str(params.get("character_name", "")).lower().strip()
                        if param_name_low and (c_name_low in param_name_low or param_name_low in c_name_low):
                            return True
                        prompt_low = (a.prompt or "").lower()
                        if c_name_low in prompt_low:
                            return True
                        c_tokens = [t for t in c_name_low.replace("(", " ").replace(")", " ").replace("-", " ").split() if len(t) > 1]
                        if any(t in prompt_low for t in c_tokens):
                            return True
                        return False

                    char_assets = [a for a in all_char_assets if is_for_character(a, character)]

                    st.markdown(f"#### 🎭 Generated Poses & Expressions for {character.name} ({len(char_assets)} Assets)")
                    st.caption(f"Review, set master identity, or click **'🔄 Edit Prompt & Regenerate'** on any image to re-render that specific pose for {character.name}.")

                    if not char_assets:
                        st.info(f"No poses or sheets generated yet for {character.name}. Use the studio above to generate presets.")
                    else:
                        cols = st.columns(3)
                        for idx, asset in enumerate(char_assets):
                            col = cols[idx % 3]
                            with col:
                                with st.container(border=True):
                                    if Path(asset.file_path).exists():
                                        st.image(asset.file_path, use_container_width=True)
                                        
                                        p_label = (asset.parameters or {}).get("preset_name", asset.type) if isinstance(asset.parameters, dict) else asset.type
                                        is_master = (character.master_reference_asset_id == asset.id)
                                        
                                        st.markdown(f"**{p_label}**" + (" `⭐ MASTER`" if is_master else ""))
                                        st.caption(f"ID: `{asset.id[:8]}` | Seed: `{asset.seed}` | {asset.width}x{asset.height}")

                                        # Action Row 1: Master, Download, Delete
                                        ab_col1, ab_col2, ab_col3 = st.columns([1.5, 1, 1])
                                        with ab_col1:
                                            if not is_master:
                                                if st.button("⭐ Set Master", key=f"set_m_{asset.id}", use_container_width=True):
                                                    AssetService.set_character_master_reference(db, character.id, asset.id)
                                                    st.success(f"Locked {character.name}'s master face to asset `{asset.id[:8]}`!")
                                                    st.rerun()
                                            else:
                                                st.button("✅ Active", key=f"active_m_{asset.id}", disabled=True, use_container_width=True)
                                        with ab_col2:
                                            with open(asset.file_path, "rb") as af:
                                                st.download_button("⬇️", data=af, file_name=f"{character.name}_{asset.id[:6]}.png", mime="image/png", key=f"dl_{asset.id}", use_container_width=True)
                                        with ab_col3:
                                            if st.button("🗑️", key=f"del_char_{asset.id}", help="Delete this pose", use_container_width=True):
                                                AssetService.delete_asset(db, asset.id)
                                                st.success(f"Deleted pose asset `{asset.id[:8]}`.")
                                                st.rerun()

                                        # Action Row 2: Prompt-based Individual Regeneration Expander
                                        with st.expander("🔄 Edit Prompt & Regenerate This Pose"):
                                            custom_regen_prompt = st.text_area(
                                                "Custom Prompt for this Pose",
                                                value=asset.prompt or "",
                                                height=90,
                                                key=f"regen_prompt_{asset.id}"
                                            )
                                            rg_c1, rg_c2 = st.columns(2)
                                            with rg_c1:
                                                regen_seed = st.number_input("New Seed", min_value=1, max_value=9999999, value=(asset.seed or 42) + 1, key=f"rg_seed_{asset.id}")
                                            with rg_c2:
                                                regen_steps = st.slider("Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"rg_steps_{asset.id}")

                                            if st.button("🚀 Re-Render This Pose", type="primary", use_container_width=True, key=f"btn_regen_{asset.id}"):
                                                with st.spinner(f"Regenerating pose on {provider_choice.upper()}..."):
                                                    provider = get_image_provider(provider_choice)
                                                    r_req = ImageGenerationRequest(
                                                        prompt=custom_regen_prompt,
                                                        width=asset.width or 768,
                                                        height=asset.height or 1344,
                                                        num_inference_steps=regen_steps,
                                                        seed=int(regen_seed)
                                                    )
                                                    r_res = provider.generate(r_req)
                                                    # Save as new asset variation tagged to this character
                                                    r_params = dict(asset.parameters or {})
                                                    r_params["character_id"] = character.id
                                                    r_params["character_name"] = character.name
                                                    new_asset = AssetService.save_image_asset(
                                                        db=db,
                                                        project_id=project.id,
                                                        asset_type=asset.type,
                                                        image_bytes=r_res.image_bytes,
                                                        prompt=custom_regen_prompt,
                                                        seed=int(regen_seed),
                                                        provider=provider_choice,
                                                        model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                                        parameters=r_params
                                                    )
                                                    if is_master:
                                                        AssetService.set_character_master_reference(db, character.id, new_asset.id)
                                                    st.success(f"Regenerated pose as `{new_asset.id[:8]}`!")
                                                    st.rerun()
                                    else:
                                        st.warning(f"File missing on disk: `{asset.id[:8]}`")
                                        if st.button("🗑️ Clean Record", key=f"del_orphan_c_{asset.id}"):
                                            AssetService.delete_asset(db, asset.id)
                                            st.rerun()

        # -------------------------------------------------------------
        # TAB 2: LOCATION MASTER REFERENCES & WORLD CONCEPT STILLS
        # -------------------------------------------------------------
        with tab_locs:
            st.subheader("📍 Location Master References & Staging Angles")
            st.caption("Generate multi-angle environment reference plates, lighting variations, and CCTV concepts to ensure scene architectural continuity.")

            if not locations:
                st.info("No locations created yet. Please create locations on Page 03 Locations.")
            else:
                loc_map = {l.id: l.name for l in locations}
                selected_loc_id = st.selectbox("Select Active Location", options=list(loc_map.keys()), format_func=lambda x: loc_map[x], key="loc_select_box")
                loc = LocationService.get_location(db, selected_loc_id)

                if loc:
                    # 1. LOCATION HEADER OVERVIEW & MASTER BANNER
                    with st.container(border=True):
                        lh_c1, lh_c2, lh_c3 = st.columns([1.5, 2.5, 1.5])
                        with lh_c1:
                            st.markdown(f"### {loc.name}")
                            st.caption(f"**Type:** {getattr(loc, 'environment_type', 'Interior')}")
                        with lh_c2:
                            st.markdown(f"**Architecture / Lighting:** {getattr(loc, 'lighting', 'N/A')}")
                            st.markdown(f"**Key Materials:** {getattr(loc, 'materials', getattr(loc, 'atmosphere', 'N/A'))}")
                        with lh_c3:
                            loc_master_asset = AssetService.get_asset(db, loc.master_reference_asset_id) if loc.master_reference_asset_id else None
                            if loc_master_asset and Path(loc_master_asset.file_path).exists():
                                st.success("⭐ **Master Environment Locked**")
                                st.image(loc_master_asset.file_path, width=120)
                            else:
                                st.warning("⚠️ No Master Environment Set")

                    st.markdown("---")

                    # 2. GENERATION STUDIO (Single Preset or Batch Core Suite)
                    st.markdown("#### 🏛️ Environment Staging Studio")
                    with st.container(border=True):
                        loc_presets = LocationSheetService.list_presets()
                        loc_preset_map = {p["key"]: f"{p['name']} ({p['aspect_ratio']})" for p in loc_presets}

                        lp_sel_col, lp_desc_col = st.columns([2, 2])
                        with lp_sel_col:
                            selected_loc_preset_key = st.selectbox(
                                "Select Staging View / Perspective",
                                options=list(loc_preset_map.keys()),
                                format_func=lambda x: loc_preset_map[x],
                                key=f"loc_preset_sel_{loc.id}"
                            )
                        with lp_desc_col:
                            lp_info = next((p for p in loc_presets if p["key"] == selected_loc_preset_key), {})
                            st.info(f"💡 {lp_info.get('description', '')}")

                        loc_compiled = LocationSheetService.compile_prompt(loc, selected_loc_preset_key, default_aspect_ratio=project.aspect_ratio or "16:9")

                        loc_prompt = st.text_area(
                            f"Prompt for {loc_compiled['preset_name']}",
                            value=loc_compiled["prompt"],
                            height=100,
                            key=f"loc_prompt_{loc.id}_{selected_loc_preset_key}"
                        )

                        l_ctrl1, l_ctrl2, l_ctrl3, l_ctrl4 = st.columns([1.2, 1.2, 1.2, 1.5])
                        with l_ctrl1:
                            loc_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=108, key=f"loc_seed_{loc.id}_{selected_loc_preset_key}")
                        with l_ctrl2:
                            loc_steps = st.slider("Inference Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"loc_steps_{loc.id}_{selected_loc_preset_key}")
                        with l_ctrl3:
                            st.text_input("Resolution", value=f"{loc_compiled['width']}x{loc_compiled['height']}", disabled=True, key=f"loc_res_{loc.id}_{selected_loc_preset_key}")
                        with l_ctrl4:
                            st.write("") # spacing
                            gen_loc_btn = st.button("✨ Render Environment Angle", type="primary", use_container_width=True, key=f"gen_loc_btn_{loc.id}_{selected_loc_preset_key}")

                        if gen_loc_btn:
                            with st.spinner(f"Rendering {loc_compiled['preset_name']} for {loc.name} on {provider_choice.upper()}..."):
                                provider = get_image_provider(provider_choice)
                                req = ImageGenerationRequest(
                                    prompt=loc_prompt,
                                    width=loc_compiled["width"],
                                    height=loc_compiled["height"],
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
                                    model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                    parameters={
                                        "location_id": loc.id,
                                        "location_name": loc.name,
                                        "preset_key": selected_loc_preset_key,
                                        "preset_name": loc_compiled["preset_name"]
                                    }
                                )
                                if selected_loc_preset_key == "MASTER_WIDE" and not loc.master_reference_asset_id:
                                    AssetService.set_location_master_reference(db, loc.id, saved_asset.id)
                                st.success(f"Generated & Saved `{saved_asset.id[:8]}` ({loc_compiled['preset_name']})!")
                                st.rerun()

                        # Batch suite expander
                        with st.expander("⚡ Batch Render: Core Location Suite (Master + Reverse + Blackout + CCTV)"):
                            st.caption("Automatically generates all 4 key staging perspectives sequentially for complete video world-building.")
                            if st.button("🚀 Render All 4 Staging Views in Sequence", key=f"batch_loc_suite_{loc.id}"):
                                core_loc_keys = ["MASTER_WIDE", "REVERSE_180", "EMERGENCY_BLACKOUT", "CCTV_SURVEILLANCE"]
                                progress_bar = st.progress(0)
                                provider = get_image_provider(provider_choice)
                                for idx, l_key in enumerate(core_loc_keys):
                                    l_spec = LocationSheetService.compile_prompt(loc, l_key, default_aspect_ratio=project.aspect_ratio or "16:9")
                                    with st.spinner(f"Generating {l_spec['preset_name']} ({idx+1}/{len(core_loc_keys)})..."):
                                        r = provider.generate(ImageGenerationRequest(
                                            prompt=l_spec["prompt"],
                                            width=l_spec["width"],
                                            height=l_spec["height"],
                                            num_inference_steps=loc_steps,
                                            seed=int(loc_seed) + idx * 10
                                        ))
                                        sa = AssetService.save_image_asset(
                                            db=db,
                                            project_id=project.id,
                                            asset_type=AssetType.LOCATION_REFERENCE.value,
                                            image_bytes=r.image_bytes,
                                            prompt=l_spec["prompt"],
                                            seed=int(loc_seed) + idx * 10,
                                            provider=provider_choice,
                                            model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                            parameters={
                                                "location_id": loc.id,
                                                "location_name": loc.name,
                                                "preset_key": l_key,
                                                "preset_name": l_spec["preset_name"]
                                            }
                                        )
                                        if l_key == "MASTER_WIDE" and not loc.master_reference_asset_id:
                                            AssetService.set_location_master_reference(db, loc.id, sa.id)
                                    progress_bar.progress((idx + 1) / len(core_loc_keys))
                                st.success(f"🎉 Generated full Environment Staging Suite for {loc.name}!")
                                st.rerun()

                    st.markdown("---")

                    # 3. LOCATION STAGING MATRIX & INDIVIDUAL ANGLE RE-GENERATION
                    all_loc_assets = db.query(Asset).filter(
                        Asset.project_id == project.id,
                        Asset.type == AssetType.LOCATION_REFERENCE.value
                    ).order_by(Asset.created_at.desc()).all() if locations else []

                    def is_for_location(a: Asset, l) -> bool:
                        params = a.parameters if isinstance(a.parameters, dict) else {}
                        if params.get("location_id") == l.id:
                            return True
                        if l.master_reference_asset_id == a.id:
                            return True
                        l_name_low = l.name.lower().strip()
                        param_name_low = str(params.get("location_name", "")).lower().strip()
                        if param_name_low and (l_name_low in param_name_low or param_name_low in l_name_low):
                            return True
                        prompt_low = (a.prompt or "").lower()
                        if l_name_low in prompt_low:
                            return True
                        l_tokens = [t for t in l_name_low.replace("(", " ").replace(")", " ").replace("-", " ").split() if len(t) > 2]
                        if any(t in prompt_low for t in l_tokens):
                            return True
                        return False

                    loc_assets = [a for a in all_loc_assets if is_for_location(a, loc)]

                    st.markdown(f"#### 🏛️ Generated Staging Angles & Stills for {loc.name} ({len(loc_assets)} Assets)")
                    st.caption(f"Review, set master environment, or click **'🔄 Edit Prompt & Regenerate'** on any image to re-render that specific perspective for {loc.name}.")

                    if not loc_assets:
                        st.info(f"No staging stills generated yet for {loc.name}. Use the studio above to generate presets.")
                    else:
                        cols = st.columns(3)
                        for idx, asset in enumerate(loc_assets):
                            col = cols[idx % 3]
                            with col:
                                with st.container(border=True):
                                    if Path(asset.file_path).exists():
                                        st.image(asset.file_path, use_container_width=True)
                                        
                                        p_label = (asset.parameters or {}).get("preset_name", asset.type) if isinstance(asset.parameters, dict) else asset.type
                                        is_master = (loc.master_reference_asset_id == asset.id)
                                        
                                        st.markdown(f"**{p_label}**" + (" `⭐ MASTER`" if is_master else ""))
                                        st.caption(f"ID: `{asset.id[:8]}` | Seed: `{asset.seed}` | {asset.width}x{asset.height}")

                                        # Action Row 1: Master, Download, Delete
                                        lb_col1, lb_col2, lb_col3 = st.columns([1.5, 1, 1])
                                        with lb_col1:
                                            if not is_master:
                                                if st.button("⭐ Set Master", key=f"set_ml_{asset.id}", use_container_width=True):
                                                    AssetService.set_location_master_reference(db, loc.id, asset.id)
                                                    st.success(f"Locked {loc.name}'s master environment to asset `{asset.id[:8]}`!")
                                                    st.rerun()
                                            else:
                                                st.button("✅ Active", key=f"active_ml_{asset.id}", disabled=True, use_container_width=True)
                                        with lb_col2:
                                            with open(asset.file_path, "rb") as laf:
                                                st.download_button("⬇️", data=laf, file_name=f"{loc.name}_{asset.id[:6]}.png", mime="image/png", key=f"dl_loc_{asset.id}", use_container_width=True)
                                        with lb_col3:
                                            if st.button("🗑️", key=f"del_loc_{asset.id}", help="Delete this angle", use_container_width=True):
                                                AssetService.delete_asset(db, asset.id)
                                                st.success(f"Deleted staging asset `{asset.id[:8]}`.")
                                                st.rerun()

                                        # Action Row 2: Prompt-based Individual Regeneration Expander
                                        with st.expander("🔄 Edit Prompt & Regenerate This Perspective"):
                                            custom_loc_regen_prompt = st.text_area(
                                                "Custom Prompt for this Perspective",
                                                value=asset.prompt or "",
                                                height=90,
                                                key=f"loc_regen_prompt_{asset.id}"
                                            )
                                            lrg_c1, lrg_c2 = st.columns(2)
                                            with lrg_c1:
                                                loc_regen_seed = st.number_input("New Seed", min_value=1, max_value=9999999, value=(asset.seed or 108) + 1, key=f"lrg_seed_{asset.id}")
                                            with lrg_c2:
                                                loc_regen_steps = st.slider("Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"lrg_steps_{asset.id}")

                                            if st.button("🚀 Re-Render This Perspective", type="primary", use_container_width=True, key=f"btn_loc_regen_{asset.id}"):
                                                with st.spinner(f"Regenerating environment angle on {provider_choice.upper()}..."):
                                                    provider = get_image_provider(provider_choice)
                                                    r_req = ImageGenerationRequest(
                                                        prompt=custom_loc_regen_prompt,
                                                        width=asset.width or 1024,
                                                        height=asset.height or 576,
                                                        num_inference_steps=loc_regen_steps,
                                                        seed=int(loc_regen_seed)
                                                    )
                                                    r_res = provider.generate(r_req)
                                                    # Save as new asset variation tagged to this location
                                                    lr_params = dict(asset.parameters or {})
                                                    lr_params["location_id"] = loc.id
                                                    lr_params["location_name"] = loc.name
                                                    new_loc_asset = AssetService.save_image_asset(
                                                        db=db,
                                                        project_id=project.id,
                                                        asset_type=asset.type,
                                                        image_bytes=r_res.image_bytes,
                                                        prompt=custom_loc_regen_prompt,
                                                        seed=int(loc_regen_seed),
                                                        provider=provider_choice,
                                                        model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                                        parameters=lr_params
                                                    )
                                                    if is_master:
                                                        AssetService.set_location_master_reference(db, loc.id, new_loc_asset.id)
                                                    st.success(f"Regenerated perspective as `{new_loc_asset.id[:8]}`!")
                                                    st.rerun()
                                    else:
                                        st.warning(f"File missing on disk: `{asset.id[:8]}`")
                                        if st.button("🗑️ Clean Record", key=f"del_orphan_l_{asset.id}"):
                                            AssetService.delete_asset(db, asset.id)
                                            st.rerun()

        # -------------------------------------------------------------
        # TAB 3: SHOT KEYFRAMES (INTERACTIVE FACE & LOCATION LOCKING)
        # -------------------------------------------------------------
        with tab_shots:
            st.subheader("🎞️ Shot Keyframe Generation & Interactive Reference Locking")
            st.caption("Select any previously generated Character Master portraits or Location Environment stills to condition and face-lock the shot keyframe.")

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

                            # 1. GATHER ALL PROJECT REFERENCE ASSETS
                            all_project_assets = AssetService.list_assets_by_project(db, project.id)
                            char_ref_assets = [
                                a for a in all_project_assets
                                if a.type in [AssetType.CHARACTER_REFERENCE.value, AssetType.CHARACTER_SHEET.value]
                                and Path(a.file_path).exists()
                            ]
                            loc_ref_assets = [
                                a for a in all_project_assets
                                if a.type == AssetType.LOCATION_REFERENCE.value
                                and Path(a.file_path).exists()
                            ]

                            # Character & Location Name Resolver
                            def resolve_character_match(raw_name: str, char_list: list):
                                if not raw_name or not char_list:
                                    return None
                                r_clean = str(raw_name).lower().strip()

                                def get_c_name(item):
                                    if hasattr(item, "name"):
                                        return str(item.name)
                                    if isinstance(item, dict) and "name" in item:
                                        return str(item["name"])
                                    return str(item)

                                for c in char_list:
                                    c_name = get_c_name(c).lower().strip()
                                    if c_name == r_clean:
                                        return c
                                for c in char_list:
                                    c_low = get_c_name(c).lower().strip()
                                    if r_clean in c_low or c_low in r_clean:
                                        return c
                                r_tokens = [t for t in r_clean.replace("(", " ").replace(")", " ").replace("-", " ").split() if len(t) > 1]
                                for c in char_list:
                                    c_tokens = [t for t in get_c_name(c).lower().replace("(", " ").replace(")", " ").replace("-", " ").split() if len(t) > 1]
                                    if any(t in c_tokens for t in r_tokens) or any(t in r_tokens for t in c_tokens):
                                        return c
                                return None

                            # Determine smart defaults for character references
                            default_char_ref_ids = []
                            missing_chars = []
                            for ch_name in (shot.characters or []):
                                matched_char = resolve_character_match(ch_name, characters)
                                if matched_char:
                                    # Check master reference first
                                    if matched_char.master_reference_asset_id:
                                        m_cand = next((a for a in char_ref_assets if a.id == matched_char.master_reference_asset_id), None)
                                        if m_cand and m_cand.id not in default_char_ref_ids:
                                            default_char_ref_ids.append(m_cand.id)
                                    else:
                                        # Fallback to latest asset for this character
                                        c_cand = next((a for a in char_ref_assets if is_for_character(a, matched_char)), None)
                                        if c_cand and c_cand.id not in default_char_ref_ids:
                                            default_char_ref_ids.append(c_cand.id)
                                            AssetService.set_character_master_reference(db, matched_char.id, c_cand.id)
                                        elif not any(is_for_character(a, matched_char) for a in char_ref_assets):
                                            missing_chars.append(matched_char)

                            # Determine smart defaults for location references
                            default_loc_ref_ids = []
                            matched_loc = None
                            if getattr(active_scene, "location_id", None):
                                matched_loc = LocationService.get_location(db, active_scene.location_id)
                            if not matched_loc and locations:
                                for loc_item in locations:
                                    l_low = loc_item.name.lower().strip()
                                    if (l_low in (active_scene.title or "").lower() or 
                                        l_low in (shot.image_prompt or "").lower() or 
                                        l_low in (shot.action or "").lower()):
                                        matched_loc = loc_item
                                        break
                                if not matched_loc:
                                    matched_loc = locations[0]

                            if matched_loc:
                                if matched_loc.master_reference_asset_id:
                                    l_cand = next((a for a in loc_ref_assets if a.id == matched_loc.master_reference_asset_id), None)
                                    if l_cand and l_cand.id not in default_loc_ref_ids:
                                        default_loc_ref_ids.append(l_cand.id)
                                else:
                                    l_cand = next((a for a in loc_ref_assets if is_for_location(a, matched_loc)), None)
                                    if l_cand and l_cand.id not in default_loc_ref_ids:
                                        default_loc_ref_ids.append(l_cand.id)
                                        AssetService.set_location_master_reference(db, matched_loc.id, l_cand.id)

                            # 2. INTERACTIVE REFERENCE IMAGE SELECTOR
                            st.markdown("---")
                            st.markdown("#### 🎭 Select Visual Reference Plates (Face & Location Lock)")
                            st.caption("Choose which character faces and location concepts to pass into the AI image conditioning pipeline.")

                            # Build friendly format functions
                            def get_char_asset_label(aid: str) -> str:
                                asset_obj = next((a for a in char_ref_assets if a.id == aid), None)
                                if not asset_obj:
                                    return aid[:8]
                                params = asset_obj.parameters if isinstance(asset_obj.parameters, dict) else {}
                                cname = params.get("character_name")
                                if not cname:
                                    # find character by matching
                                    for c in characters:
                                        if is_for_character(asset_obj, c):
                                            cname = c.name
                                            break
                                cname = cname or "Character"
                                preset = params.get("preset_name", asset_obj.type)
                                is_m = any(c.master_reference_asset_id == asset_obj.id for c in characters)
                                return f"👤 {cname} — {preset} (`{asset_obj.id[:8]}`)" + (" ⭐ MASTER" if is_m else "")

                            def get_loc_asset_label(aid: str) -> str:
                                asset_obj = next((a for a in loc_ref_assets if a.id == aid), None)
                                if not asset_obj:
                                    return aid[:8]
                                params = asset_obj.parameters if isinstance(asset_obj.parameters, dict) else {}
                                lname = params.get("location_name")
                                if not lname:
                                    for l in locations:
                                        if is_for_location(asset_obj, l):
                                            lname = l.name
                                            break
                                lname = lname or "Location"
                                preset = params.get("preset_name", asset_obj.type)
                                is_m = any(l.master_reference_asset_id == asset_obj.id for l in locations)
                                return f"📍 {lname} — {preset} (`{asset_obj.id[:8]}`)" + (" ⭐ MASTER" if is_m else "")

                            # Character References Multiselect
                            char_asset_ids = [a.id for a in char_ref_assets]
                            selected_char_ids = st.multiselect(
                                "👤 Character Reference Images (Face Lock)",
                                options=char_asset_ids,
                                default=[aid for aid in default_char_ref_ids if aid in char_asset_ids],
                                format_func=get_char_asset_label,
                                key=f"sel_char_refs_{shot.id}"
                            )

                            # Location References Multiselect
                            loc_asset_ids = [a.id for a in loc_ref_assets]
                            selected_loc_ids = st.multiselect(
                                "📍 Location Reference Images (Environment Lock)",
                                options=loc_asset_ids,
                                default=[aid for aid in default_loc_ref_ids if aid in loc_asset_ids],
                                format_func=get_loc_asset_label,
                                key=f"sel_loc_refs_{shot.id}"
                            )

                            all_selected_ref_ids = selected_char_ids + selected_loc_ids

                            # Render Visual Thumbnail Gallery of Selected References
                            if all_selected_ref_ids:
                                st.markdown("**Selected Reference Plates for this Shot:**")
                                thumb_cols = st.columns(min(len(all_selected_ref_ids), 4))
                                for t_idx, ref_aid in enumerate(all_selected_ref_ids):
                                    t_col = thumb_cols[t_idx % min(len(all_selected_ref_ids), 4)]
                                    ref_obj = next((a for a in all_project_assets if a.id == ref_aid), None)
                                    if ref_obj and Path(ref_obj.file_path).exists():
                                        with t_col:
                                            st.image(ref_obj.file_path, use_container_width=True)
                                            t_label = get_char_asset_label(ref_aid) if ref_obj.type in [AssetType.CHARACTER_REFERENCE.value, AssetType.CHARACTER_SHEET.value] else get_loc_asset_label(ref_aid)
                                            st.caption(t_label)
                            else:
                                st.warning("⚠️ No reference images selected. FLUX will generate from the text prompt alone without face conditioning.")

                            # Quick generator for missing characters
                            if missing_chars:
                                for mc in missing_chars:
                                    st.info(f"💡 `{mc.name}` has no generated poses yet.")
                                    if st.button(f"✨ Quick-Generate Master Portrait for {mc.name}", key=f"qgen_m_{mc.id}", use_container_width=True):
                                        with st.spinner(f"Generating Master Portrait for {mc.name} on {provider_choice.upper()}..."):
                                            c_spec = CharacterSheetService.compile_prompt(mc, "MASTER_PORTRAIT")
                                            provider = get_image_provider(provider_choice)
                                            q_req = ImageGenerationRequest(
                                                prompt=c_spec["prompt"],
                                                width=c_spec["width"],
                                                height=c_spec["height"],
                                                num_inference_steps=28 if provider_choice == "modal" else 4,
                                                seed=42
                                            )
                                            q_res = provider.generate(q_req)
                                            q_asset = AssetService.save_image_asset(
                                                db=db,
                                                project_id=project.id,
                                                asset_type=AssetType.CHARACTER_REFERENCE.value,
                                                image_bytes=q_res.image_bytes,
                                                prompt=c_spec["prompt"],
                                                seed=42,
                                                provider=provider_choice,
                                                model="FLUX.1 [dev]" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                                parameters={
                                                    "character_id": mc.id,
                                                    "character_name": mc.name,
                                                    "preset_key": "MASTER_PORTRAIT",
                                                    "preset_name": "Master Identity Portrait"
                                                }
                                            )
                                            AssetService.set_character_master_reference(db, mc.id, q_asset.id)
                                            st.success(f"Locked {mc.name}'s master face to asset `{q_asset.id[:8]}`!")
                                            st.rerun()

                            # 3. ASPECT RATIO & PROMPT CONTROLS
                            st.markdown("---")
                            aspect = project.aspect_ratio or "16:9"
                            if "9:16" in aspect:
                                def_w, def_h = 768, 1344
                            elif "2.39" in aspect or "21:9" in aspect:
                                def_w, def_h = 1344, 560
                            elif "1:1" in aspect:
                                def_w, def_h = 1024, 1024
                            elif "4:3" in aspect:
                                def_w, def_h = 1152, 864
                            else: # 16:9 standard cinematic landscape
                                def_w, def_h = 1344, 768

                            kf_prompt = st.text_area(
                                "Compiled Keyframe Image Prompt",
                                value=shot.image_prompt or "Cinematic shot...",
                                height=110,
                                key=f"kf_prompt_{shot.id}"
                            )

                            kc_col1, kc_col2, kc_col3 = st.columns([1.2, 1.2, 1.5])
                            with kc_col1:
                                kf_seed = st.number_input("Seed", min_value=1, max_value=9999999, value=42 + shot.shot_number, key=f"kf_seed_{shot.id}")
                            with kc_col2:
                                kf_steps = st.slider("Inference Steps", min_value=4, max_value=35, value=28 if provider_choice == "modal" else 4, key=f"kf_steps_{shot.id}")
                            with kc_col3:
                                st.text_input("Aspect Resolution", value=f"{def_w}x{def_h} ({aspect})", disabled=True)

                            if st.button("🚀 Generate Face-Locked Keyframe", type="primary", use_container_width=True, key=f"gen_kf_{shot.id}"):
                                with st.spinner(f"Generating Keyframe for Shot {shot.shot_number:02d} on {provider_choice.upper()} using {len(all_selected_ref_ids)} reference plates..."):
                                    # Load raw bytes of all selected references
                                    conditioning_bytes = []
                                    for aid in all_selected_ref_ids:
                                        a_obj = next((a for a in all_project_assets if a.id == aid), None)
                                        if a_obj and Path(a_obj.file_path).exists():
                                            with open(a_obj.file_path, "rb") as rf:
                                                conditioning_bytes.append(rf.read())

                                    provider = get_image_provider(provider_choice)
                                    req = ImageGenerationRequest(
                                        prompt=kf_prompt,
                                        width=def_w,
                                        height=def_h,
                                        num_inference_steps=kf_steps,
                                        seed=int(kf_seed),
                                        reference_images=conditioning_bytes
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
                                        model="FLUX.1 [dev] + IP-Adapter" if provider_choice == "modal" else "FLUX.1 [schnell]",
                                        parameters={
                                            "shot_id": shot.id,
                                            "shot_number": shot.shot_number,
                                            "scene_id": active_scene.id,
                                            "scene_number": active_scene.scene_number,
                                            "selected_reference_ids": all_selected_ref_ids
                                        }
                                    )
                                    AssetService.link_shot_keyframe(db, shot.id, saved_kf.id)
                                    st.success(f"Generated & Linked Keyframe `{saved_kf.id[:8]}` to Shot {shot.shot_number:02d}!")
                                    st.rerun()

                        with sh_col2:
                            st.markdown("#### Shot Keyframe Status")
                            linked_kf = None
                            if shot.reference_asset_ids:
                                for ref_id in reversed(shot.reference_asset_ids):
                                    candidate = AssetService.get_asset(db, ref_id)
                                    if candidate and candidate.type in ["KEYFRAME", "IMAGE", "CHARACTER_REF", "LOCATION_REF"]:
                                        linked_kf = candidate
                                        break

                            if linked_kf and Path(linked_kf.file_path).exists():
                                st.image(linked_kf.file_path, caption=f"Keyframe: Scene {active_scene.scene_number:02d} - Shot {shot.shot_number:02d} ({shot.status})", use_container_width=True)
                                st.success(f"✅ Shot status: **{shot.status}**")
                                if st.button("🗑️ Delete Shot Keyframe", key=f"del_shot_kf_{linked_kf.id}", use_container_width=True):
                                    AssetService.delete_asset(db, linked_kf.id)
                                    st.success(f"Deleted keyframe and reset Shot {shot.shot_number:02d} to Draft.")
                                    st.rerun()
                            else:
                                st.warning("No keyframe image generated for this shot yet.")

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
