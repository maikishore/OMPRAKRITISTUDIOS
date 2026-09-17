import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.database import ScopedSession
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.voice_service import VoiceService
from core.enums import ProjectStatus
from ai.character_engine import CharacterEngine
from schemas.character import CharacterCreate, CharacterUpdate

st.set_page_config(page_title="02 Characters | MicroDrama Studio", page_icon="👤", layout="wide")

st.title("👤 02. Character Bible & Visual Profiles")
st.caption("AI Character Extraction, Wardrobe Specs, Continuity Anchors & Master Reference Prompts")

project_id = st.session_state.get("current_project_id")
if not project_id:
    st.warning("⚠️ Please select a project from the sidebar first.")
    st.stop()

db = ScopedSession()
engine = CharacterEngine()

try:
    project = ProjectService.get_project(db, project_id)
    if not project:
        st.error("Project not found.")
        st.stop()

    characters = CharacterService.list_project_characters(db, project_id)

    # Top Control Bar
    top_col1, top_col2, top_col3 = st.columns([2, 1, 1])
    with top_col1:
        st.subheader(f"🎬 Project: {project.title}")
        st.caption(f"Story Status: **{project.status}** | Characters: **{len(characters)} Defined**")
    with top_col2:
        all_approved = len(characters) > 0 and all(c.is_approved for c in characters)
        st.metric("Characters Status", "✅ APPROVED" if all_approved else "📝 IN PROGRESS")
    with top_col3:
        if all_approved:
            st.success("All Character Bibles Approved.")
        else:
            st.info("Review characters & click 'Approve All' when ready.")

    st.markdown("---")

    # Generation Trigger Bar
    gen_col1, gen_col2, gen_col3 = st.columns([2, 1, 1])
    with gen_col1:
        st.write("**AI Extraction:** Generate or refresh character profiles from your approved story using Gemma 4 (26B).")
    with gen_col2:
        generate_clicked = st.button("✨ Generate with Gemma 4", type="primary", use_container_width=True)
    with gen_col3:
        seed_clicked = st.button("🌱 Load 'After Closing' Cast", use_container_width=True)

    if generate_clicked:
        with st.spinner("Analyzing Story and designing characters with Gemma 4..."):
            extracted = engine.generate_characters_from_story(project)
            for char_data in extracted:
                CharacterService.create_character(db, char_data)
            st.success(f"Generated {len(extracted)} characters from story!")
            st.rerun()

    if seed_clicked:
        seed_chars = engine._get_fallback_characters(project.id, project.title)
        for char_data in seed_chars:
            CharacterService.create_character(db, char_data)
        st.success("Loaded 'After Closing' cast (Lucy, David, Emma)!")
        st.rerun()

    # Character Card Displays
    if characters:
        st.markdown("### 🎭 Character Roster")

        for idx, char in enumerate(characters):
            with st.expander(f"👤 {char.name} ({char.role or 'Character'}) {'✅ Approved' if char.is_approved else '⏳ Draft'}", expanded=(idx==0)):
                # Voice Casting & Audition Section
                st.markdown("##### 🎙️ Voice Casting & Acoustic Profile")
                v_col1, v_col2, v_col3 = st.columns([2, 2, 1])
                
                v_presets = VoiceService.list_presets()
                v_map = {p["key"]: f"{p['name']} [{p['tone']}]" for p in v_presets}
                default_voice = char.voice_description if char.voice_description in v_map else VoiceService.suggest_voice_for_character(char)
                v_keys = list(v_map.keys())
                v_idx = v_keys.index(default_voice) if default_voice in v_keys else 0

                with v_col1:
                    sel_voice_id = st.selectbox(
                        "Casting Voice Profile",
                        options=v_keys,
                        index=v_idx,
                        format_func=lambda x: v_map[x],
                        key=f"voice_sel_{char.id}"
                    )
                with v_col2:
                    audition_text = st.text_input(
                        "Audition Sample Line",
                        value=VoiceService.VOICE_PRESETS[sel_voice_id]["sample_line"],
                        key=f"aud_text_{char.id}"
                    )
                with v_col3:
                    st.write("") # spacing
                    audition_btn = st.button("🔊 Audition Voice", key=f"btn_aud_{char.id}", use_container_width=True)

                if audition_btn:
                    with st.spinner(f"Synthesizing voice audition for {char.name}..."):
                        aud_bytes = VoiceService.generate_audition(sel_voice_id, audition_text, provider_name="modal")
                        st.audio(aud_bytes, format="audio/wav")
                        st.success(f"Casting preview for **{char.name}** ({VoiceService.VOICE_PRESETS[sel_voice_id]['name']})")

                st.markdown("---")

                with st.form(f"char_form_{char.id}"):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        c_name = st.text_input("Name", value=char.name, key=f"name_{char.id}")
                        c_role = st.selectbox("Role", ["Protagonist", "Co-Protagonist", "Antagonist", "Supporting", "Mysterious Catalyst"], index=0 if not char.role else ["Protagonist", "Co-Protagonist", "Antagonist", "Supporting", "Mysterious Catalyst"].index(char.role) if char.role in ["Protagonist", "Co-Protagonist", "Antagonist", "Supporting", "Mysterious Catalyst"] else 0, key=f"role_{char.id}")
                    with c2:
                        c_gender = st.text_input("Gender", value=char.gender or "Female", key=f"gender_{char.id}")
                        c_age = st.text_input("Age", value=char.age or "24", key=f"age_{char.id}")
                    with c3:
                        c_hair = st.text_input("Hair", value=char.hair or "", key=f"hair_{char.id}")
                        c_face = st.text_input("Face / Eyes", value=char.face or "", key=f"face_{char.id}")
                    with c4:
                        c_skin = st.text_input("Skin Tone", value=char.skin or "", key=f"skin_{char.id}")
                        c_body = st.text_input("Body / Build", value=char.body or "", key=f"body_{char.id}")

                    c_clothing = st.text_area("Clothing / Wardrobe", value=char.clothing or "", height=70, key=f"cloth_{char.id}")
                    c_access = st.text_input("Accessories / Distinctive Props", value=char.accessories or "", key=f"access_{char.id}")

                    c_pers = st.text_area("Personality & Behavior", value=f"Personality: {char.personality or ''}\nBehavior: {char.behavior or ''}", height=70, key=f"pers_{char.id}")
                    c_prompt = st.text_area("Master Image Identity Prompt", value=char.identity_prompt or "", height=80, key=f"prompt_{char.id}")
                    c_continuity = st.text_area("Continuity Constraints (one per line)", value="\n".join(char.continuity_constraints or []), height=70, key=f"cont_{char.id}")

                    b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
                    with b_col1:
                        save_char = st.form_submit_button("💾 Save Character & Lock Voice Profile")
                    with b_col2:
                        delete_char = st.form_submit_button("🗑️ Delete Character")

                    if save_char:
                        CharacterService.update_character(
                            db,
                            char.id,
                            CharacterUpdate(
                                name=c_name,
                                role=c_role,
                                gender=c_gender,
                                age=c_age,
                                hair=c_hair,
                                face=c_face,
                                skin=c_skin,
                                body=c_body,
                                clothing=c_clothing,
                                accessories=c_access,
                                identity_prompt=c_prompt,
                                voice_description=sel_voice_id,
                                continuity_constraints=[c.strip() for c in c_continuity.split("\n") if c.strip()]
                            )
                        )
                        st.success(f"Updated {c_name} and locked voice profile to `{sel_voice_id}`!")
                        st.rerun()

                    if delete_char:
                        CharacterService.delete_character(db, char.id)
                        st.warning(f"Deleted {char.name}")
                        st.rerun()

        # Approval Gate
        st.markdown("---")
        app_col1, app_col2 = st.columns([2, 1])
        with app_col1:
            st.write("Ready to finalize character bibles? Approving locks in these character descriptions across all subsequent scene and shot prompts.")
        with app_col2:
            if st.button("✅ APPROVE All Characters", type="primary", use_container_width=True):
                CharacterService.approve_all_characters(db, project.id)
                st.success("🎉 All characters approved! Project status updated to CHARACTERS_READY.")
                st.rerun()

    else:
        st.info("No characters generated yet. Click **'Generate with Gemma 4'** or **'Load Cast'** to create your character bible.")

    # Manual Character Addition Form
    with st.expander("➕ Manually Add Character"):
        with st.form("add_char_form"):
            new_name = st.text_input("Name", placeholder="e.g. Lucy Vance")
            new_role = st.text_input("Role", placeholder="e.g. Protagonist")
            new_clothing = st.text_area("Clothing / Wardrobe", placeholder="e.g. Olive green canvas parka...")
            new_prompt = st.text_area("Identity Prompt", placeholder="e.g. Cinematic portrait of Lucy Vance...")
            add_submitted = st.form_submit_button("Add Character")

            if add_submitted and new_name.strip():
                CharacterService.create_character(
                    db,
                    CharacterCreate(
                        project_id=project.id,
                        name=new_name.strip(),
                        role=new_role.strip() if new_role else "Supporting",
                        clothing=new_clothing.strip() if new_clothing else None,
                        identity_prompt=new_prompt.strip() if new_prompt else None
                    )
                )
                st.success(f"Added {new_name}!")
                st.rerun()

finally:
    db.close()
