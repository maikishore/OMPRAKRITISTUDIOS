import json
import logging
from typing import List, Dict, Any, Optional
from ai.llm_client import LLMClient
from prompts.scenes.scene_prompt import (
    SCENE_GENERATION_SYSTEM_PROMPT,
    build_scene_generation_user_prompt
)

logger = logging.getLogger(__name__)

class SceneEngine:
    """Decomposes 3-Act Story and Production Bible into sequential scenes."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_scenes(
        self,
        title: str,
        genre: str,
        target_duration_seconds: int,
        story_context: dict,
        character_names: list,
        location_names: list,
        visual_style_summary: str = ""
    ) -> List[Dict[str, Any]]:
        """Generates 8-12 structured scenes totaling target runtime using Gemma 4 26B."""
        user_prompt = build_scene_generation_user_prompt(
            title=title,
            genre=genre,
            target_duration_seconds=target_duration_seconds,
            story_context=story_context,
            character_names=character_names,
            location_names=location_names,
            visual_style_summary=visual_style_summary
        )

        try:
            response_json = self.llm.generate_json(
                system_prompt=SCENE_GENERATION_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )
            raw_scenes = response_json.get("scenes", [])
            if raw_scenes and len(raw_scenes) >= 3:
                # Sanitize and normalize scene numbers
                for idx, sc in enumerate(raw_scenes, start=1):
                    sc["scene_number"] = idx
                    if "duration_seconds" not in sc or not isinstance(sc["duration_seconds"], int):
                        sc["duration_seconds"] = 50
                return raw_scenes
            else:
                logger.warning("LLM returned incomplete scene list; using fallback generator.")
                return self.get_seed_scenes_for_after_closing(target_duration_seconds)
        except Exception as e:
            logger.error(f"Error during AI scene generation: {e}. Using seed fallback.")
            return self.get_seed_scenes_for_after_closing(target_duration_seconds)

    @staticmethod
    def get_seed_scenes_for_after_closing(target_duration_seconds: int = 600) -> List[Dict[str, Any]]:
        """Returns 10 canonical seed scenes for 'After Closing' horror micro-drama totaling ~600s."""
        return [
            {
                "scene_number": 1,
                "title": "The Last Shoppers & Closing Chime",
                "summary": "Lucy attends a bustling party inside the mall atrium. The lights flicker and an eerie automated chime announces the mall is officially closed.",
                "purpose": "Establish protagonist, upbeat false safety, and abrupt shift to vulnerability.",
                "duration_seconds": 55,
                "location_name": "Central Mall Atrium",
                "time_of_day": "Night - Closing Time (10:00 PM)",
                "characters": ["Lucy", "David"],
                "emotional_state": "Carefree turning to mild confusion and hesitation.",
                "story_beat": "Act 1 - Inciting Incident",
                "sound_design": "Chic synth party track cut short by booming reverberant 4-tone PA chime.",
                "visual_direction": "Warm golden party lights cut violently to cold overhead sodium-vapor hum.",
                "continuity_notes": "Lucy wears crimson silk cocktail dress, holding phone with dying battery."
            },
            {
                "scene_number": 2,
                "title": "Heavy Steel Shutters",
                "summary": "Lucy and David run toward the main entrance only to see colossal security roller shutters slam shut and lock magnetically.",
                "purpose": "Confirm entrapment; eliminate external rescue hope.",
                "duration_seconds": 50,
                "location_name": "Central Mall Atrium",
                "time_of_day": "Night - 10:15 PM",
                "characters": ["Lucy", "David"],
                "emotional_state": "Mounting claustrophobic dread and panic.",
                "story_beat": "Act 1 - Lock-in Reversal",
                "sound_design": "Heavy metallic grinding, pneumatic piston locking clanks, dead silence following.",
                "visual_direction": "Low angle looking up at the towering shutter; harsh shadows casting prison-bar silhouettes.",
                "continuity_notes": "Glass doors reflect pitch-black outside; streetlights outside mysteriously dark."
            },
            {
                "scene_number": 3,
                "title": "The Security Monitor Room",
                "summary": "Lucy and David break into the CCTV control center seeking a backdoor release, but discover all monitors showing static except one pointing at them.",
                "purpose": "Establish an active watching presence and psychological surveillance.",
                "duration_seconds": 65,
                "location_name": "Security CCTV Station",
                "time_of_day": "Night - 10:45 PM",
                "characters": ["Lucy", "David"],
                "emotional_state": "Paranoia, feeling watched and hunted.",
                "story_beat": "Act 1 to Act 2 Transition",
                "sound_design": "High-pitched CRT tube coil whine, cooling fans, intermittent radio static.",
                "visual_direction": "Green phosphor monitor glow washing over Lucy's face; deep black shadows in corners.",
                "continuity_notes": "One monitor feed shows the fashion store mannequins standing in a new pose."
            },
            {
                "scene_number": 4,
                "title": "The Whispering Toy Store",
                "summary": "Lucy follows the faint sound of a child crying into the vintage toy store, encountering Emma holding an antique brass wind-up music box.",
                "purpose": "Introduce Emma, establish eerie innocent lore, and present Game 1.",
                "duration_seconds": 65,
                "location_name": "Toy Store",
                "time_of_day": "Midnight",
                "characters": ["Lucy", "Emma"],
                "emotional_state": "Cautious maternal empathy masking deep instinctual dread.",
                "story_beat": "Act 2 - Game 1: The Music Box",
                "sound_design": "Tinny detuned lullaby from the music box; porcelain doll eyes clicking as eyes blink.",
                "visual_direction": "Creepy overhead spotlights illuminating toy shelves; shadows stretching long across aisles.",
                "continuity_notes": "Emma wears pale vintage lace party dress; skin appears faintly waxy under light."
            },
            {
                "scene_number": 5,
                "title": "Game 1: The Mirror Maze of Mannequins",
                "summary": "The toy store doors lock. Lucy must navigate a narrow corridor of mannequins without touching any porcelain surface while the music plays.",
                "purpose": "First active test/game; high visceral suspense.",
                "duration_seconds": 60,
                "location_name": "Toy Store",
                "time_of_day": "Night - 12:30 AM",
                "characters": ["Lucy", "Emma"],
                "emotional_state": "High adrenaline, intense physical concentration.",
                "story_beat": "Act 2 - Rising Action",
                "sound_design": "Accelerating ticking tempo; faint sound of porcelain grinding whenever Lucy turns her back.",
                "visual_direction": "Tight tracking camera on Lucy's trembling feet avoiding painted chalk lines.",
                "continuity_notes": "Lucy grazes nothing; successfully reaches exit door."
            },
            {
                "scene_number": 6,
                "title": "The Luxury Fashion Hall & The Pose Game",
                "summary": "David and Lucy reunite inside the high-end apparel store. The mall voice broadcasts: 'Assume your poses before the strobe stops.'",
                "purpose": "Escalate game stakes; introduce psychological coercion.",
                "duration_seconds": 60,
                "location_name": "Fashion Store",
                "time_of_day": "Night - 1:45 AM",
                "characters": ["Lucy", "David"],
                "emotional_state": "Desperation, frantic compliance with bizarre surreal rules.",
                "story_beat": "Act 2 - Game 2: The Strobe Test",
                "sound_design": "Blinding strobe clicks with intense audio dropouts between flashes; synthetic mall voice.",
                "visual_direction": "Stroboscopic lighting freezing characters in rigid fashion editorial postures.",
                "continuity_notes": "David's hands begin to show unnatural stiffening at knuckles."
            },
            {
                "scene_number": 7,
                "title": "David's Hesitation & The Penalty",
                "summary": "During the final strobe flash, David fails to maintain perfect stillness. The store lights go black; when they return, David is frozen in position with glossed skin.",
                "purpose": "Midpoint tragedy; demonstrate consequence of failure and preview the transformation fate.",
                "duration_seconds": 65,
                "location_name": "Fashion Store",
                "time_of_day": "Night - 2:30 AM",
                "characters": ["Lucy", "David"],
                "emotional_state": "Horror, devastation, grief, and pure survival instinct.",
                "story_beat": "Act 2 - Midpoint Reversal / Loss of Ally",
                "sound_design": "Loud snap sound, followed by hollow fiberglass tap sound when Lucy touches David's arm.",
                "visual_direction": "Extreme close up on David's vacant, glass-marble eye; tear frozen solid on waxy cheek.",
                "continuity_notes": "David is now an immovable store fixture; Lucy takes his flashlight."
            },
            {
                "scene_number": 8,
                "title": "The Final Trial: Window Display Setup",
                "summary": "Lucy is summoned to the central main display window overlooking the dark avenue. The automated voice commands her to step onto the revolving pedestal.",
                "purpose": "Climactic challenge; protagonist believes passing this guarantees release.",
                "duration_seconds": 60,
                "location_name": "Window Display",
                "time_of_day": "Night - 4:15 AM (Pre-dawn)",
                "characters": ["Lucy", "Emma"],
                "emotional_state": "Grim determination, exhausted triumph, false hope.",
                "story_beat": "Act 3 - Climax: The Final Game",
                "sound_design": "Deep hydraulic motor hum revolving the circular pedestal; celestial department store music.",
                "visual_direction": "Spotlight beaming from above like a theater stage; street outside beginning to show faint indigo dawn.",
                "continuity_notes": "Lucy mounts the stage, assumes the final required graceful pose."
            },
            {
                "scene_number": 9,
                "title": "The Transformation Revealed",
                "summary": "Lucy realizes she cannot move her fingers. A smooth glossy sheen spreads across her skin. Emma smiles knowingly from below as morning light floods the window.",
                "purpose": "Horror twist: winning the game was the ritual all along.",
                "duration_seconds": 65,
                "location_name": "Window Display",
                "time_of_day": "Dawn - 6:00 AM",
                "characters": ["Lucy", "Emma"],
                "emotional_state": "Paralyzing shock turning to eternal silent stillness.",
                "story_beat": "Act 3 - The Terrible Truth",
                "sound_design": "Sound of breath crystallizing, high melodic bell chime, absolute dead quiet.",
                "visual_direction": "Slow 360-degree rotation showing Lucy transformed into an exquisite porcelain mannequin.",
                "continuity_notes": "Lucy's crimson dress is pinned with a designer price tag: 'NEW ARRIVAL'."
            },
            {
                "scene_number": 10,
                "title": "Grand Opening & Next Player",
                "summary": "The heavy front shutters roll open to bright morning sunlight. Commuters walk past the window display admiring the new display. The PA speaker clicks on.",
                "purpose": "Haunting thematic conclusion and cyclicity of the horror.",
                "duration_seconds": 55,
                "location_name": "Central Mall Atrium",
                "time_of_day": "Morning - 8:00 AM",
                "characters": ["Emma"],
                "emotional_state": "Chilling corporate normalcy and eerie dread.",
                "story_beat": "Act 3 - Resolution / Haunting Epilogue",
                "sound_design": "Warm daytime mall chime, cheerful ambient chatter, automated voice: 'Welcome shoppers... Next player.'",
                "visual_direction": "Wide pulling back shot from Lucy's serene mannequin face out through glass into busy sunlight.",
                "continuity_notes": "Emma standing in the crowd of morning shoppers, holding a new flyer for tonight's party."
            }
        ]
