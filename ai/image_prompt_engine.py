"""Deterministic Prompt Compiler for MicroDrama Studio.

Constructs rock-solid, production-grade image prompts (for FLUX / Qwen)
and motion video prompts (for LTX-2.3) by deterministically synthesizing:
  Style Bible + Location Bible + Character Bibles + Scene Context + Shot Parameters
"""

from typing import Optional, List, Dict, Any

class PromptCompiler:
    """Deterministic prompt assembler ensuring 100% visual consistency and action-aligned prompts."""

    @staticmethod
    def compile_image_prompt(
        style_data: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        characters_data: Optional[List[Dict[str, Any]]] = None,
        scene_data: Optional[Dict[str, Any]] = None,
        shot_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assembles a concise, action-driven keyframe image prompt optimized for FLUX & Qwen."""
        shot_data = shot_data or {}
        scene_data = scene_data or {}
        style_data = style_data or {}

        # 1. Shot Framing & Camera Lens
        shot_type = shot_data.get("shot_type") or "Medium Shot"
        camera_angle = shot_data.get("camera_angle")
        lens = shot_data.get("lens")
        framing = shot_data.get("framing")

        cam_parts = [shot_type]
        if camera_angle and camera_angle.lower() not in ["eye-level", "eye level", "none", ""]:
            cam_parts.append(camera_angle)
        if lens and lens.lower() not in ["none", ""]:
            cam_parts.append(lens)

        camera_str = f"Cinematic {', '.join(cam_parts)}"
        if framing and len(framing) < 80 and framing.lower() not in [shot_type.lower(), camera_angle.lower() if camera_angle else ""]:
            camera_str += f", {framing.rstrip('.')}"

        # 2. Characters in Frame with Costume Anchors
        shot_char_names = shot_data.get("characters") or []
        if isinstance(shot_char_names, str):
            shot_char_names = [c.strip() for c in shot_char_names.split(",") if c.strip()]

        active_chars_data = []
        if characters_data:
            if shot_char_names:
                for c in characters_data:
                    c_name = c.get("name", "")
                    if any(c_name.lower() == sc.lower() or sc.lower() in c_name.lower() for sc in shot_char_names):
                        active_chars_data.append(c)
            else:
                active_chars_data = characters_data

        char_strs = []
        if active_chars_data:
            for char in active_chars_data:
                name = char.get("name", "Subject")
                costume = char.get("signature_costume") or char.get("clothing")
                traits = char.get("physical_traits") or char.get("appearance")
                
                if costume:
                    char_strs.append(f"{name} in {costume}")
                elif traits:
                    short_trait = traits.split(",")[0].strip()
                    char_strs.append(f"{name} ({short_trait})")
                else:
                    char_strs.append(name)
        elif shot_char_names:
            char_strs = shot_char_names

        char_line = ", ".join(char_strs) if char_strs else "Subject"

        # 3. Physical Action & Movement (Core Dramatic Centerpiece)
        action = (shot_data.get("action") or "").strip().rstrip(".")
        emotion = (shot_data.get("emotion") or "").strip().rstrip(".")

        if action:
            action_phrase = action
            for char in active_chars_data:
                c_name = char.get("name", "")
                costume = char.get("signature_costume") or char.get("clothing")
                if c_name and costume and c_name.lower() in action_phrase.lower():
                    if costume.lower() not in action_phrase.lower():
                        import re
                        pattern = re.compile(re.escape(c_name), re.IGNORECASE)
                        action_phrase = pattern.sub(f"{c_name} in {costume}", action_phrase, count=1)

            has_name = any(c.get("name", "").lower() in action.lower() for c in (active_chars_data or [])) or any(sc.lower() in action.lower() for sc in shot_char_names)
            if not has_name:
                action_phrase = f"{char_line} {action}"
        else:
            action_phrase = f"{char_line} positioned in frame"

        if emotion and emotion.lower() not in action_phrase.lower():
            action_phrase += f", expression of {emotion}"

        # 4. Location & Lighting Atmosphere
        loc_name = (location_data.get("name") if location_data else shot_data.get("environment")) or "Interior"
        lighting = shot_data.get("lighting") or (location_data.get("lighting") if location_data else "") or scene_data.get("visual_direction") or ""

        env_parts = [f"Location: {loc_name}"]
        if lighting:
            env_parts.append(f"Lighting: {lighting.rstrip('.')}")

        env_str = ". ".join(env_parts)

        # 5. Cinematic Style & Texture
        realism = style_data.get("cinematic_realism") or "Ultra-realistic 35mm film capture"
        dof = style_data.get("depth_of_field")
        contrast = style_data.get("contrast")

        style_parts = [realism.rstrip('.')]
        if dof:
            style_parts.append(f"{dof} depth of field")
        if contrast:
            style_parts.append(f"{contrast} contrast")

        style_str = ", ".join(style_parts) + ", 35mm film still"

        # Build clean cohesive output
        return f"{camera_str}: {action_phrase}. {env_str}. {style_str}."

    @staticmethod
    def compile_video_prompt(
        style_data: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        characters_data: Optional[List[Dict[str, Any]]] = None,
        scene_data: Optional[Dict[str, Any]] = None,
        shot_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assembles a motion-focused video generation prompt for LTX-2.3."""
        shot_data = shot_data or {}
        scene_data = scene_data or {}

        shot_type = shot_data.get("shot_type", "Medium Shot")
        movement = shot_data.get("camera_movement", "Slow dolly in")
        duration = shot_data.get("duration_seconds", 5.0)
        action = (shot_data.get("action") or "").strip().rstrip(".")
        emotion = (shot_data.get("emotion") or "").strip().rstrip(".")

        # 1. Camera Movement
        cam_motion = f"{shot_type}, camera executes {movement} over {duration}s duration."

        # 2. Character Action & Performance
        action_motion = f"Action & Movement: {action}." if action else ""
        emotion_motion = f"Character performance: {emotion}." if emotion else ""

        # 3. Environment Dynamics
        lighting = shot_data.get("lighting") or scene_data.get("visual_direction")
        lighting_motion = f"Atmosphere: {lighting.rstrip('.')}." if lighting else ""

        # Combine
        parts = [p for p in [cam_motion, action_motion, emotion_motion, lighting_motion, "Fluid cinematic motion, photorealistic physics, seamless temporal consistency."] if p]
        return " ".join(parts)

    @staticmethod
    def get_negative_prompt(style_data: Optional[Dict[str, Any]] = None) -> str:
        """Generates standard negative prompt to prevent CGI, anime, artifacts, and distortion."""
        base_negative = (
            "cartoon, 3D render, CGI, anime, illustration, painting, drawing, distorted anatomy, "
            "extra limbs, missing fingers, floating objects, plastic skin, oversaturated colors, "
            "jpeg compression artifacts, watermark, logo, text overlay, blur, low resolution, bad hands"
        )
        return base_negative

