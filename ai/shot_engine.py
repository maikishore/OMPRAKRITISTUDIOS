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
            visual_style_summary=style_data.get("cinematic_realism", "") if style_data else "",
            scene_dialogue=scene_data.get("dialogue", "")
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

        # Pass each shot through Dialogue Enhancer & Deterministic Prompt Compiler
        for idx, shot in enumerate(shots, start=1):
            shot["shot_number"] = idx
            
            # Ensure character shots are not silent if characters are in frame
            shot_chars = shot.get("characters", [])
            if shot_chars and (not shot.get("dialogue") or shot.get("dialogue") in ["null", "None", ""]):
                primary_char = shot_chars[0]
                action_text = shot.get("action", "")
                emotion_text = shot.get("emotion", "Tense")
                if "whisper" in emotion_text.lower() or "fear" in emotion_text.lower():
                    shot["dialogue"] = f"{primary_char}: '(whispering) Quiet... don\'t make a sound.'"
                elif "panic" in emotion_text.lower() or "urgent" in emotion_text.lower():
                    shot["dialogue"] = f"{primary_char}: 'Hurry! We don\'t have much time!'"
                else:
                    shot["dialogue"] = f"{primary_char}: 'Did you see that? Stay close.'"

            # Filter character data for characters actually in this shot
            shot_char_names = shot.get("characters", [])
            shot_chars_data = (
                [c for c in characters_data if c.get("name") in shot_char_names]
                if characters_data else None
            )

            # Auto-compile deterministic image and video prompts
            shot["image_prompt"] = self.compiler.compile_image_prompt(
                style_data=style_data,
                location_data=location_data,
                characters_data=shot_chars_data or characters_data,
                scene_data=scene_data,
                shot_data=shot
            )

            shot["video_prompt"] = self.compiler.compile_video_prompt(
                style_data=style_data,
                location_data=location_data,
                characters_data=shot_chars_data or characters_data,
                scene_data=scene_data,
                shot_data=shot
            )

        return shots

    @staticmethod
    def get_seed_shots_for_scene(scene_number: int = 1) -> List[Dict[str, Any]]:
        """Provides high-quality seed shots with full cinematic direction and character dialogue."""
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
                    "dialogue": "Lucy: '(whispering) What was that chime...?'",
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
                    "dialogue": "Automated PA: 'Attention shoppers. The complex is now permanently locked. Please prepare for tonight\'s exhibition.'",
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
        elif scene_number == 2:
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 5.0,
                    "shot_type": "Wide Shot",
                    "camera_angle": "Low angle",
                    "camera_movement": "Fast tracking push-in",
                    "lens": "24mm wide",
                    "framing": "Looking up from polished mall floor toward towering steel security shutters crashing down.",
                    "characters": ["Lucy", "David"],
                    "action": "Lucy and David sprint to the main glass entrance just as the heavy ribbed steel shutters slam into the floor.",
                    "emotion": "Frantic panic, breathless shock.",
                    "dialogue": "Lucy: 'The doors! Pull the emergency latch, hurry!'",
                    "environment": "Main entrance vestibule, cold night darkness visible outside through glass gaps.",
                    "lighting": "Stark contrast from overhead emergency floodlights casting long bars across the floor.",
                    "sound": "Violent metallic screeching, deafening pneumatic thud as gates impact floor.",
                    "visual_effects": "Sparks and dust puff as bottom seal hits ground.",
                    "continuity_constraints": ["Lucy in red dress", "David in sports coat"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 5.5,
                    "shot_type": "Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Handheld jitter",
                    "lens": "50mm prime",
                    "framing": "Tight focus on David's hands pulling violently at the red emergency release lever.",
                    "characters": ["David"],
                    "action": "David yanks the magnetic lever with all his weight; a digital keypad beeps red and denies access.",
                    "emotion": "Desperation, physical exertion.",
                    "dialogue": "David: 'It\'s no use... the magnetic locks are engaged from the inside.'",
                    "environment": "Entrance wall beside massive shutter track.",
                    "lighting": "Red LED alarm light pulsing over David's face.",
                    "sound": "Three rapid error buzzers, straining metal.",
                    "visual_effects": "Pulsing red ambient glow.",
                    "continuity_constraints": ["David's watch visible", "Emergency lever in down position"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.0,
                    "shot_type": "Medium Shot",
                    "camera_angle": "High angle",
                    "camera_movement": "Slow Dolly back",
                    "lens": "35mm anamorphic",
                    "framing": "Looking down at Lucy and David trapped against the towering steel wall.",
                    "characters": ["Lucy", "David"],
                    "action": "Lucy pulls out her phone, staring at the screen showing 'No Service' with 2% battery.",
                    "emotion": "Claustrophobic dread, mounting panic.",
                    "dialogue": "Lucy: 'No signal... not even for emergency services.'",
                    "environment": "Atrium exit area, vast empty darkness behind them.",
                    "lighting": "Cold green exit sign glow reflecting on phone glass.",
                    "sound": "Distant mechanical latching echoes through ventilation shafts.",
                    "visual_effects": "Phone screen blue reflection.",
                    "continuity_constraints": ["Phone in Lucy's trembling hand"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 5.5,
                    "shot_type": "Over-the-Shoulder",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Pan right",
                    "lens": "50mm prime",
                    "framing": "Over Lucy's shoulder looking toward the dark service hallway leading to security.",
                    "characters": ["Lucy", "David"],
                    "action": "David points a beam of his phone light down the dark corridor toward the CCTV office.",
                    "emotion": "Grim resolve, nervous caution.",
                    "dialogue": "David: 'There has to be a master override in the security office. Follow me.'",
                    "environment": "Concourse opening to narrow service corridor.",
                    "lighting": "Single narrow beam cutting pitch-black corridor.",
                    "sound": "Low air conditioning rumble, heavy breathing.",
                    "visual_effects": "Volumetric dust beam.",
                    "continuity_constraints": ["David leading the way"]
                }
            ]
        elif scene_number == 3:
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 5.5,
                    "shot_type": "Medium Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow Dolly in",
                    "lens": "35mm anamorphic",
                    "framing": "Framing Lucy and David stepping into the green-lit CCTV control room.",
                    "characters": ["Lucy", "David"],
                    "action": "David pushes the unlocked door open; rows of vintage CRT monitors cast an eerie green glow.",
                    "emotion": "Tense vigilance, creeping dread.",
                    "dialogue": "Lucy: '(whispering) The door was unlocked... like they wanted us to come in here.'",
                    "environment": "Security CCTV Station, swivel chairs, wall of cathode-ray tube screens.",
                    "lighting": "Green phosphor tube glow from dozens of monitors.",
                    "sound": "High-frequency CRT flyback whine, cooling fan hum.",
                    "visual_effects": "Phosphor screen reflections across room surfaces.",
                    "continuity_constraints": ["Security room desk cluttered with logbooks"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 6.0,
                    "shot_type": "Close-up",
                    "camera_angle": "Low angle",
                    "camera_movement": "Static",
                    "lens": "85mm portrait",
                    "framing": "Tight focus on David's face as he inspects the security monitor matrix.",
                    "characters": ["David"],
                    "action": "David taps on the keyboard, realizing all screens show grey static except Monitor Four.",
                    "emotion": "Shock, creeping horror.",
                    "dialogue": "David: 'Look at monitor four... that camera angle is inside this room right now.'",
                    "environment": "Security console workstation.",
                    "lighting": "Harsh flicker from green screen.",
                    "sound": "Keyboard clacking, soft static hiss.",
                    "visual_effects": "Screen flicker lines on skin.",
                    "continuity_constraints": ["David leaning over keyboard"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.5,
                    "shot_type": "Point-of-View",
                    "camera_angle": "High angle",
                    "camera_movement": "Slight mechanical pan",
                    "lens": "24mm wide",
                    "framing": "CCTV camera perspective from corner ceiling looking down at Lucy and David.",
                    "characters": ["Lucy", "David"],
                    "action": "The ceiling camera lens audibly autofocuses with a motorized click, tracking Lucy's movement.",
                    "emotion": "Paranoia, feeling watched and hunted.",
                    "dialogue": "Lucy: 'David, look up... it just moved. It\'s tracking us.'",
                    "environment": "CCTV room from high vantage point.",
                    "lighting": "Security overlay timestamp '00:45:12' in corner.",
                    "sound": "Tiny stepper motor servo clicking.",
                    "visual_effects": "Grainy security camera raster lines.",
                    "continuity_constraints": ["Timestamp ticking in sync"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 5.5,
                    "shot_type": "Medium Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Handheld slight drift",
                    "lens": "50mm prime",
                    "framing": "Lucy and David exchanging a frantic glance.",
                    "characters": ["Lucy", "David"],
                    "action": "David grabs Lucy's hand, backing away from the camera's gaze toward the doorway.",
                    "emotion": "Urgent realization, panic.",
                    "dialogue": "David: 'Whoever is operating this system is in the building. We need to keep moving.'",
                    "environment": "Security office doorway.",
                    "lighting": "Dark shadow backdrop behind doorway.",
                    "sound": "Distant faint nursery music box melody echoing down hallway.",
                    "visual_effects": "Shallow depth of field.",
                    "continuity_constraints": ["Lucy looking over shoulder"]
                }
            ]
        elif scene_number == 4:
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 6.0,
                    "shot_type": "Wide Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow Dolly in",
                    "lens": "35mm anamorphic",
                    "framing": "Deep wide view of antique vintage toy store with porcelain doll shelves.",
                    "characters": ["Lucy"],
                    "action": "Lucy steps into the toy store, flashlight illuminating rows of vintage dolls and wooden toys.",
                    "emotion": "Hesitant curiosity, high alert.",
                    "dialogue": "Lucy: 'Is anyone in here? Hello...?'",
                    "environment": "Toy Store, wooden shelves, glass display cases.",
                    "lighting": "Single warm amber spotlight pool amidst dark shadows.",
                    "sound": "Tinny detuned music box melody playing in rhythmic loops.",
                    "visual_effects": "Volumetric beam reflecting off glass cases.",
                    "continuity_constraints": ["Lucy holding flashlight"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 5.5,
                    "shot_type": "Medium Shot",
                    "camera_angle": "Low angle",
                    "camera_movement": "Slow tracking",
                    "lens": "50mm prime",
                    "framing": "Framing Emma sitting calmly on a vintage wooden bench holding an ornate music box.",
                    "characters": ["Emma"],
                    "action": "Emma winds the brass key of the music box with perfectly rhythmic, slow finger motions.",
                    "emotion": "Serene, eerie innocence, unblinking focus.",
                    "dialogue": "Emma: 'If you want the door to open, you must listen to the music box.'",
                    "environment": "Central aisle of toy store.",
                    "lighting": "Clean white overhead key light illuminating Emma's vintage lace dress.",
                    "sound": "Metallic spring winding clicks, music box melody.",
                    "visual_effects": "Subtle waxy sheen on Emma's skin.",
                    "continuity_constraints": ["Emma in pale lace dress"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.0,
                    "shot_type": "Over-the-Shoulder",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Static",
                    "lens": "50mm prime",
                    "framing": "Over Lucy's shoulder facing Emma.",
                    "characters": ["Lucy", "Emma"],
                    "action": "Lucy kneels slightly to get closer to Emma, extending a trembling hand.",
                    "emotion": "Maternal concern blended with instinctual fear.",
                    "dialogue": "Lucy: 'Where are your parents? Who locked these doors?'",
                    "environment": "Toy store aisle surrounded by dolls.",
                    "lighting": "Cross-key lighting between Lucy's face and Emma's serene expression.",
                    "sound": "Music box tempo beginning to accelerate slightly.",
                    "visual_effects": "Doll eyes in background seeming to catch specular light.",
                    "continuity_constraints": ["Lucy kneeling position"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 5.5,
                    "shot_type": "Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow push-in",
                    "lens": "85mm portrait",
                    "framing": "Tight shot on Emma's unblinking, smiling face.",
                    "characters": ["Emma"],
                    "action": "Emma places a single finger over her lips in a hush gesture.",
                    "emotion": "Chilling certainty, dark playfulness.",
                    "dialogue": "Emma: 'Shh... when the melody stops, nobody can move.'",
                    "environment": "Toy store background blurred into golden bokeh.",
                    "lighting": "Eerie edge glow on Emma's porcelain-smooth cheek.",
                    "sound": "Final high chime of the music box melody.",
                    "visual_effects": "Macro depth of field.",
                    "continuity_constraints": ["Emma's finger on lips"]
                }
            ]
        else:
            # Universal high-quality seed breakdown for Scenes 5-10 and any scene
            return [
                {
                    "shot_number": 1,
                    "duration_seconds": 5.5,
                    "shot_type": "Wide Shot",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow Dolly in",
                    "lens": "35mm anamorphic",
                    "framing": "Wide framing establishing character positioning and environmental tension.",
                    "characters": ["Lucy"],
                    "action": "Lucy moves forward with cautious steps, scanning the ominous surroundings with acute focus.",
                    "emotion": "High alertness, mounting fear.",
                    "dialogue": "Lucy: '(whispering) Is anyone in here? Stay focused, Lucy.'",
                    "environment": "Dramatic interior environment with deep shadow pockets.",
                    "lighting": "Low key directional lighting with sharp rim highlights.",
                    "sound": "Atmospheric drone, rhythmic breathing, distant mechanical rumble.",
                    "visual_effects": "Atmospheric haze cutting through light shafts.",
                    "continuity_constraints": ["Costume and props intact"]
                },
                {
                    "shot_number": 2,
                    "duration_seconds": 6.0,
                    "shot_type": "Medium Shot",
                    "camera_angle": "Low angle",
                    "camera_movement": "Tracking sideways",
                    "lens": "50mm prime",
                    "framing": "Medium framing capturing character reaction to sudden environmental change.",
                    "characters": ["Lucy"],
                    "action": "Lucy halts in her tracks, eyes fixing on a chilling transformation clue in the room.",
                    "emotion": "Shock, realized danger.",
                    "dialogue": "Lucy: 'Look at how they\'re positioned... they weren\'t standing like this before.'",
                    "environment": "Display pedestals and props.",
                    "lighting": "Flickering overhead sodium light.",
                    "sound": "Sharp metallic click, sudden drop in background sound.",
                    "visual_effects": "Subtle lens flare.",
                    "continuity_constraints": ["Flashlight pointed forward"]
                },
                {
                    "shot_number": 3,
                    "duration_seconds": 6.5,
                    "shot_type": "Close-up",
                    "camera_angle": "Eye-level",
                    "camera_movement": "Slow tilt up",
                    "lens": "85mm portrait",
                    "framing": "Intense close-up on protagonist facial strain and vocal delivery.",
                    "characters": ["Lucy"],
                    "action": "Lucy speaks with urgent conviction, heart pounding as she prepares for the next challenge.",
                    "emotion": "Desperation, fierce survival instinct.",
                    "dialogue": "Lucy: 'I refuse to end up like the rest of them. We are getting out!'",
                    "environment": "Tight background bokeh with mannequin silhouettes.",
                    "lighting": "Dramatic side Rembrandt lighting.",
                    "sound": "Heavy heartbeat thump, accelerating timer cue.",
                    "visual_effects": "Crisp specular highlights in eyes.",
                    "continuity_constraints": ["Tension around jawline"]
                },
                {
                    "shot_number": 4,
                    "duration_seconds": 5.0,
                    "shot_type": "Wide Shot",
                    "camera_angle": "High angle",
                    "camera_movement": "Slow Dolly back",
                    "lens": "24mm wide",
                    "framing": "High angle perspective showing the protagonist confronting the scene's climax.",
                    "characters": ["Lucy"],
                    "action": "Lucy turns swiftly toward the exit corridor as the countdown buzzer sounds.",
                    "emotion": "Urgent adrenaline surge.",
                    "dialogue": "Lucy: 'The gate is cycling down... move now!'",
                    "environment": "Vast commercial space with long shadows.",
                    "lighting": "Strobe pulses cutting across the marble floor.",
                    "sound": "Deafening mechanical lock release, pulsing alarm tone.",
                    "visual_effects": "Motion blur emphasizing speed.",
                    "continuity_constraints": ["Exiting toward frame left"]
                }
            ]
