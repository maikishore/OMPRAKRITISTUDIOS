import json
import logging
from typing import List, Dict, Any, Optional
from ai.llm_client import LLMClient
from ai.image_prompt_engine import PromptCompiler
from prompts.shots.shot_prompt import (
    SHOT_GENERATION_SYSTEM_PROMPT,
    build_shot_generation_user_prompt
)

logger = logging.getLogger(__name__)

class ShotEngine:
    """Decomposes a Scene into granular shots and compiles deterministic AI prompts."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.compiler = PromptCompiler()

    def generate_shots_for_scene(
        self,
        scene_data: Dict[str, Any],
        style_data: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        characters_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generates 4-8 granular shots for a scene and compiles prompts with the deterministic compiler."""
        user_prompt = build_shot_generation_user_prompt(
            scene_number=scene_data.get("scene_number", 1),
            scene_title=scene_data.get("title", "Scene"),
            scene_summary=scene_data.get("summary", ""),
            scene_purpose=scene_data.get("purpose", ""),
            scene_duration_seconds=scene_data.get("duration_seconds", 60),
            location_name=location_data.get("name") if location_data else scene_data.get("location_name", ""),
            characters=scene_data.get("characters", []),
            time_of_day=scene_data.get("time_of_day", "Night"),
            emotional_state=scene_data.get("emotional_state", "Tense"),
            visual_direction=scene_data.get("visual_direction", ""),
            sound_design=scene_data.get("sound_design", ""),
            visual_style_summary=style_data.get("cinematic_realism", "") if style_data else ""
        )

        shots = []
        try:
            response_json = self.llm.generate_json(
                system_prompt=SHOT_GENERATION_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )
            raw_shots = response_json.get("shots", [])
            if raw_shots and len(raw_shots) >= 2:
                shots = raw_shots
            else:
                logger.warning("LLM returned incomplete shot list; using seed fallback.")
                shots = self.get_seed_shots_for_scene(scene_data.get("scene_number", 1))
        except Exception as e:
            logger.error(f"Error during AI shot breakdown: {e}. Using seed fallback.")
            shots = self.get_seed_shots_for_scene(scene_data.get("scene_number", 1))

        # Pass each shot through the Deterministic Prompt Compiler
        for idx, shot in enumerate(shots, start=1):
            shot["shot_number"] = idx
            
            # Filter character data for characters actually in this shot
            shot_char_names = shot.get("characters", [])
            shot_chars = (
                [c for c in characters_data if c.get("name") in shot_char_names]
                if characters_data else None
            )

            # Auto-compile deterministic image and video prompts
            shot["image_prompt"] = self.compiler.compile_image_prompt(
                style_data=style_data,
                location_data=location_data,
                characters_data=shot_chars or characters_data,
                scene_data=scene_data,
                shot_data=shot
            )

            shot["video_prompt"] = self.compiler.compile_video_prompt(
                style_data=style_data,
                location_data=location_data,
                characters_data=shot_chars or characters_data,
                scene_data=scene_data,
                shot_data=shot
            )

        return shots

    @staticmethod
    def get_seed_shots_for_scene(scene_number: int = 1) -> List[Dict[str, Any]]:
        """Provides high-quality seed shots for Scene 1 (or generic scene breakdown)."""
        if scene_number == 1:
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 6.0,
                    "shot_type": "Wide Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow Dolly in",
                    "lens": "35mm anamorphic",
                    "framing": "Wide framing of high-end mall atrium with marble floors and polished brass accents.",
                    "characters": ["Lucy", "David"],
                    "action": "Lucy stands near a champagne table, holding a half-empty glass while talking with David amidst laughing partygoers.",
                    "emotion": "Carefree, smiling, relaxed evening mood.",
                    "dialogue": "Lucy: 'Can you believe they rented the entire mall for this?'",
                    "environment": "Central Mall Atrium, warm golden string lights, glass elevators in background.",
                    "lighting": "Warm commercial amber party spotlights with soft bokeh from distant festive fairy lights.",
                    "sound": "Muffled lounge electronic music, chatter, clinking glassware.",
                    "visual_effects": "Subtle anamorphic lens flare from overhead hanging pendant lights.",
                    "continuity_constraints": ["Lucy wears crimson silk dress", "David in charcoal sports coat"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 5.0,
                    "shot_type": "Medium Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Static",
                    "lens": "50mm prime",
                    "framing": "Over-the-shoulder framing from behind David facing Lucy.",
                    "characters": ["Lucy", "David"],
                    "action": "Lucy looks toward the ceiling as a sudden electrical flicker cuts the background music abruptly.",
                    "emotion": "Curious, slightly startled, head tilted upward.",
                    "dialogue": "David: 'Did the music just cut out?'",
                    "environment": "Near central glass fountain, partygoers freezing in mid-sentence.",
                    "lighting": "Warm lights flicker sharply once, shifting to slightly harsher sodium glow.",
                    "sound": "Sudden audio cut, amplifier feedback pop, followed by absolute silence.",
                    "visual_effects": "Micro light stutter frame.",
                    "continuity_constraints": ["Lucy's glass in right hand", "Smartphone in left hand"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.0,
                    "shot_type": "Close-up",
                    "camera_angle": "Low angle",
                    "camera_movement": "Slow tilt up",
                    "lens": "85mm portrait",
                    "framing": "Tight focus on Lucy's expressive face looking upward toward the ceiling PA speakers.",
                    "characters": ["Lucy"],
                    "action": "Lucy freezes as a loud 4-tone melodic electronic chime echoes through the mall rafters.",
                    "emotion": "Hesitation, instinctive unease tightening around the eyes.",
                    "dialogue": None,
                    "environment": "Atrium ceiling, huge vaulted skylight showing pitch-black night sky above.",
                    "lighting": "Cold harsh downlight illuminating the bridge of Lucy's nose, deep shadows under eyes.",
                    "sound": "Deafening reverberant 4-tone department store chime.",
                    "visual_effects": "Soft shallow depth of field, background completely blurred.",
                    "continuity_constraints": ["Crimson dress neckline visible", "Gold earrings"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 7.0,
                    "shot_type": "Wide Shot",
                    "camera_angle": "High angle",
                    "camera_movement": "Tracking sideways",
                    "lens": "24mm wide",
                    "framing": "Expansive overhead perspective looking down from 2nd floor balcony at the emptying atrium floor.",
                    "characters": ["Lucy", "David"],
                    "action": "Party guests rapidly exit through side corridors. Lucy and David stand alone in the cavernous central space.",
                    "emotion": "Isolation, feeling suddenly exposed.",
                    "dialogue": "Automated PA: 'Attention shoppers. The complex is now permanently locked. Please prepare for tonight's exhibition.'",
                    "environment": "Floor littered with abandoned cups and flyer confetti.",
                    "lighting": "Main chandelier lights shut off one by one in sequence, leaving only cold green emergency exit signs.",
                    "sound": "Distant sound of doors latching shut, automated robotic broadcast voice.",
                    "visual_effects": "Deep depth of field, crisp marble floor reflections.",
                    "continuity_constraints": ["Empty party tables", "Darkening corridors"]
                },
                {
                    "shot_number": 5,
                    "duration_seconds": 5.5,
                    "shot_type": "Medium Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Handheld slight drift",
                    "lens": "50mm prime",
                    "framing": "Two-shot of Lucy and David looking toward the main entrance with mounting panic.",
                    "characters": ["Lucy", "David"],
                    "action": "David grabs Lucy's arm; both turn swiftly to sprint toward the main exit doors.",
                    "emotion": "Urgency, panic, realized danger.",
                    "dialogue": "Lucy: 'David, we have to get out right now!'",
                    "environment": "Atrium concourse leading to glass revolving doors.",
                    "lighting": "Cold fluorescent emergency tube lighting casting eerie green cast on skin.",
                    "sound": "Heavy running footsteps echoing on polished marble, heavy mechanical shutter motor starting.",
                    "visual_effects": "Dynamic subtle camera shake emphasizing urgency.",
                    "continuity_constraints": ["Lucy's running motion", "Hand grip on forearm"]
                }
            ]
        else:
            # Generic seed shots for other scenes
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 5.0,
                    "shot_type": "Wide Establishing Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow Dolly in",
                    "lens": "35mm anamorphic",
                    "framing": "Wide perspective establishing character placement in environment.",
                    "characters": ["Lucy"],
                    "action": "Lucy enters the room cautiously, scanning the perimeter with a trembling flashlight.",
                    "emotion": "High alertness, mounting fear.",
                    "dialogue": None,
                    "environment": "Interior location setting with eerie props and deep shadows.",
                    "lighting": "Low key directional lighting with high contrast.",
                    "sound": "Atmospheric drone, soft footsteps on floor.",
                    "visual_effects": "Flashlight volumetric beam cutting through dust particles.",
                    "continuity_constraints": ["Flashlight in hand", "Costume intact"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 6.0,
                    "shot_type": "Close-up",
                    "camera_angle": "Low angle",
                    "camera_movement": "Static",
                    "lens": "85mm portrait",
                    "framing": "Tight focus on protagonist reaction.",
                    "characters": ["Lucy"],
                    "action": "Lucy notices something unexpected, eyes widening as she holds her breath.",
                    "emotion": "Shock, creeping horror.",
                    "dialogue": None,
                    "environment": "Close background with out-of-focus mannequin silhouettes.",
                    "lighting": "Harsh edge rim lighting highlighting cheekbone and eyes.",
                    "sound": "Sudden sharp metallic scrape in distance.",
                    "visual_effects": "Subtle lens flare.",
                    "continuity_constraints": ["Sweat on brow", "Steady gaze"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.5,
                    "shot_type": "Over-the-Shoulder",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow tracking",
                    "lens": "50mm prime",
                    "framing": "Framed over Lucy's shoulder toward the focal subject in the room.",
                    "characters": ["Lucy"],
                    "action": "Lucy approaches the key story element with hesitant slow steps.",
                    "emotion": "Compelled yet terrified.",
                    "dialogue": None,
                    "environment": "Central focal display with props and enigmatic clues.",
                    "lighting": "Spotlight pool on the subject amidst surrounding pitch darkness.",
                    "sound": "Clock ticking tempo, rhythmic breathing.",
                    "visual_effects": "Deep shadows framing the border of the shot.",
                    "continuity_constraints": ["Distance to target ~3 meters"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 5.0,
                    "shot_type": "Extreme Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Static",
                    "lens": "100mm macro",
                    "framing": "Macro detail on key clue or transformation detail.",
                    "characters": ["Lucy"],
                    "action": "Fingers tap against glossy polished porcelain surface; the skin texture looks unnaturally rigid.",
                    "emotion": "Chilling realization.",
                    "dialogue": None,
                    "environment": "Key prop detail.",
                    "lighting": "Clean specular highlights showing high gloss reflection.",
                    "sound": "Hollow ceramic ping sound.",
                    "visual_effects": "Hyper-detailed macro texture.",
                    "continuity_constraints": ["Mannequin gloss texture"]
                }
            ]
