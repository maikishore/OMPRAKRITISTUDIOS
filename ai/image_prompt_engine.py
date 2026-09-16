"""Deterministic Prompt Compiler for MicroDrama Studio.

Constructs rock-solid, production-grade image prompts (for FLUX / Qwen)
and motion video prompts (for LTX-2.3) by deterministically synthesizing:
  Style Bible + Location Bible + Character Bibles + Scene Context + Shot Parameters
"""

from typing import Optional, List, Dict, Any

class PromptCompiler:
    """Deterministic prompt assembler ensuring 100% visual consistency."""

    @staticmethod
    def compile_image_prompt(
        style_data: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        characters_data: Optional[List[Dict[str, Any]]] = None,
        scene_data: Optional[Dict[str, Any]] = None,
        shot_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assembles a keyframe image prompt from production bible and shot data."""
        parts = []

        # 1. Shot Type, Camera Angle & Lens
        camera_specs = []
        if shot_data:
            if shot_data.get("shot_type"):
                camera_specs.append(shot_data["shot_type"])
            if shot_data.get("camera_angle") and shot_data["camera_angle"] != "Eye-level":
                camera_specs.append(f"{shot_data['camera_angle']} perspective")
            if shot_data.get("lens"):
                camera_specs.append(f"shot on {shot_data['lens']}")
            if shot_data.get("framing"):
                camera_specs.append(f"composition: {shot_data['framing']}")

        if camera_specs:
            parts.append(f"Cinematic {', '.join(camera_specs)}.")

        # 2. Characters and Physical Visual Anchors
        char_prompts = []
        if characters_data:
            for char in characters_data:
                char_name = char.get("name", "Character")
                char_anchor = char.get("visual_anchor_prompt")
                costume = char.get("signature_costume")
                traits = char.get("physical_traits")

                desc_parts = [char_name]
                if traits:
                    desc_parts.append(traits)
                if costume:
                    desc_parts.append(f"wearing {costume}")
                if char_anchor and not traits and not costume:
                    desc_parts.append(char_anchor)

                char_prompts.append(", ".join(desc_parts))

        if char_prompts:
            parts.append(f"Featuring: {'; '.join(char_prompts)}.")

        # 3. Shot Action & Character Emotion
        if shot_data:
            action = shot_data.get("action")
            emotion = shot_data.get("emotion")
            if action:
                action_str = f"Action: {action}"
                if emotion:
                    action_str += f" with expression of {emotion}"
                parts.append(action_str + ".")

        # 4. Location & Environmental Setting
        if location_data:
            loc_name = location_data.get("name", "Interior")
            loc_anchor = location_data.get("visual_anchor_prompt")
            loc_arch = location_data.get("architecture")
            loc_mats = location_data.get("materials")

            loc_parts = [f"Environment: {loc_name}"]
            if loc_arch:
                loc_parts.append(loc_arch)
            if loc_mats:
                loc_parts.append(f"with {loc_mats}")
            if loc_anchor and not loc_arch:
                loc_parts.append(loc_anchor)

            parts.append(", ".join(loc_parts) + ".")
        elif shot_data and shot_data.get("environment"):
            parts.append(f"Environment: {shot_data['environment']}.")

        # 5. Lighting & Atmosphere
        lighting_elements = []
        if shot_data and shot_data.get("lighting"):
            lighting_elements.append(shot_data["lighting"])
        elif scene_data and scene_data.get("visual_direction"):
            lighting_elements.append(scene_data["visual_direction"])
        elif location_data and location_data.get("lighting"):
            lighting_elements.append(location_data["lighting"])

        if lighting_elements:
            parts.append(f"Lighting: {', '.join(lighting_elements)}.")

        # 6. Project Visual Style & Aesthetic Anchors
        if style_data:
            style_parts = []
            if style_data.get("cinematic_realism"):
                style_parts.append(style_data["cinematic_realism"])
            if style_data.get("contrast"):
                style_parts.append(f"{style_data['contrast']} contrast")
            if style_data.get("film_grain"):
                style_parts.append(f"{style_data['film_grain']} film grain")
            if style_data.get("depth_of_field"):
                style_parts.append(f"{style_data['depth_of_field']} depth of field")

            if style_parts:
                parts.append(f"Visual Quality: {', '.join(style_parts)}, 8k UHD, masterpiece raw cinematic film capture.")
        else:
            parts.append("Visual Quality: Photorealistic 35mm motion picture still, 8k resolution, hyper-detailed textures.")

        # 7. Optical and visual effects
        if shot_data and shot_data.get("visual_effects"):
            parts.append(f"Optical effects: {shot_data['visual_effects']}.")

        return " ".join(parts)

    @staticmethod
    def compile_video_prompt(
        style_data: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        characters_data: Optional[List[Dict[str, Any]]] = None,
        scene_data: Optional[Dict[str, Any]] = None,
        shot_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assembles a motion-focused video generation prompt for LTX-2.3."""
        parts = []

        # 1. Temporal Camera Dynamics
        movement = shot_data.get("camera_movement", "Slow subtle push-in") if shot_data else "Slow dolly"
        shot_type = shot_data.get("shot_type", "Cinematic Medium Shot") if shot_data else "Medium Shot"
        duration = shot_data.get("duration_seconds", 5.0) if shot_data else 5.0

        parts.append(f"{shot_type}, camera executes continuous {movement} over {duration}s duration.")

        # 2. Subject Dynamics and Physical Movement
        if shot_data and shot_data.get("action"):
            parts.append(f"Movement: {shot_data['action']}.")

        # 3. Micro-expressions & Character Tension
        if shot_data and shot_data.get("emotion"):
            parts.append(f"Character performance: subtle facial twitch, {shot_data['emotion']}, micro-movements of eyes and breathing.")

        # 4. Environmental Motion & Lighting Shifts
        env_motion = []
        if shot_data and shot_data.get("lighting"):
            env_motion.append(f"lighting reflects {shot_data['lighting']}")
        if scene_data and scene_data.get("sound_design"):
            env_motion.append(f"atmospheric rhythm matching {scene_data['sound_design']}")

        if env_motion:
            parts.append(f"Atmospheric dynamics: {', '.join(env_motion)}.")

        # 5. Motion Fidelity & Physics Constraints
        parts.append("Motion Quality: Smooth fluid cinematic motion, natural human physics, zero morphing artifacts, stable anatomical geometry.")

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
