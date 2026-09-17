"""Voice Casting & Dialogue Synthesis Service (Powered by Qwen3-TTS 1.7B).

Manages character voice profiles, audition previews, natural language emotion instruct steering,
and shot-level dialogue audio generation.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from core.models import Character, Shot, Asset
from core.enums import AssetType
from core.asset_service import AssetService
from providers.audio.factory import get_audio_provider
from providers.audio.base import AudioGenerationRequest

class VoiceService:
    """Manages Qwen3-TTS voice presets, audition previews, and emotional dialogue synthesis."""

    VOICE_PRESETS: Dict[str, Dict[str, Any]] = {
        "qwen_vivian": {
            "name": "Vivian (Young American Female - Emotional / Expressive)",
            "speaker": "Vivian",
            "gender": "Female",
            "accent": "American",
            "tone": "Youthful, expressive, tense, dynamic",
            "sample_line": "Did you hear that? I'm telling you, someone else is in this building with us!"
        },
        "qwen_eric": {
            "name": "Eric (Grounded American Male - Deep / Gritty)",
            "speaker": "Eric",
            "gender": "Male",
            "accent": "American",
            "tone": "Grounded, deep, cautious, intense",
            "sample_line": "Stay behind me. The exit gate is jammed, but there's a service stairwell in the back."
        },
        "qwen_uncle_martin": {
            "name": "Uncle Martin (Authoritative Mature Male - Menacing / Deep)",
            "speaker": "Uncle_Martin",
            "gender": "Male",
            "accent": "American",
            "tone": "Resonant, stern, commanding, intimidating",
            "sample_line": "All retail staff must report to the security dispatch immediately. Do not open the doors."
        },
        "qwen_serena": {
            "name": "Serena (Warm American Female - Empathetic / Clear)",
            "speaker": "Serena",
            "gender": "Female",
            "accent": "American",
            "tone": "Warm, emotional, sensitive, clear",
            "sample_line": "I managed to bypass the security console, but the backup generators are failing fast."
        },
        "qwen_ryan": {
            "name": "Ryan (Energetic Young Male - Fast / Tense)",
            "speaker": "Ryan",
            "gender": "Male",
            "accent": "American",
            "tone": "Fast-paced, nervous, urgent, youthful",
            "sample_line": "The security camera feeds are looping every twenty seconds. We're completely blind!"
        },
        "qwen_elena": {
            "name": "Elena (Sophisticated Dramatic Female - Intimidating / Cool)",
            "speaker": "Elena",
            "gender": "Female",
            "accent": "American",
            "tone": "Composed, mysterious, cold, calculating",
            "sample_line": "Quiet... look at the mirrors in the atrium. The reflections aren't moving with us."
        },
        "qwen_dylan": {
            "name": "Dylan (Steady Analytical Male - Focused)",
            "speaker": "Dylan",
            "gender": "Male",
            "accent": "American",
            "tone": "Analytical, precise, composed",
            "sample_line": "Curious. The electrical surge originated from deep inside the ventilation sub-level."
        },
        # Legacy aliases for smooth backward compatibility
        "af_sarah": {
            "name": "Sarah / Vivian (American Female - Tense / Dramatic)",
            "speaker": "Vivian",
            "gender": "Female",
            "accent": "American",
            "tone": "Tense, emotional, youthful",
            "sample_line": "Did you hear that? I'm telling you, someone else is in this building with us!"
        },
        "am_adam": {
            "name": "Adam / Eric (American Male - Gritty / Grounded)",
            "speaker": "Eric",
            "gender": "Male",
            "accent": "American",
            "tone": "Grounded, deep, cautious",
            "sample_line": "Stay behind me. The exit gate is jammed, but there's a service stairwell in the back."
        },
        "am_michael": {
            "name": "Michael / Uncle Martin (American Male - Authoritative)",
            "speaker": "Uncle_Martin",
            "gender": "Male",
            "accent": "American",
            "tone": "Resonant, stern, controlled",
            "sample_line": "All retail staff must report to the security dispatch immediately. Do not open the doors."
        }
    }

    EMOTION_INSTRUCT_MAP: Dict[str, str] = {
        "Whispering & Terrified": "Speak in a terrified, breathless whisper, shaking with fear and dread",
        "Urgent & Shouting": "Speak in an urgent, fast-paced voice, shouting with rising panic and intense vocal strain",
        "Tense & Breathless": "Speak in a tense, breathless whisper with high anxiety, struggling to stay quiet",
        "Cold & Controlled": "Speak in a low, cold, calculated, menacing tone without remorse",
        "Grounded & Analytical": "Speak in a steady, focused, cautious tone, assessing the situation calmly",
        "Sarcastic & Dismissive": "Speak with a sharp, sarcastic, sneering cadence and cynical edge",
        "Sorrowful & Weeping": "Speak with a broken, tearful voice, voice cracking with grief and despair",
        "Neutral / Conversational": "Speak in a natural, conversational, dramatic acting cadence"
    }

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """Returns list of all available voice presets."""
        res = []
        # Filter primary Qwen presets first
        for k, v in cls.VOICE_PRESETS.items():
            if k.startswith("qwen_"):
                res.append({
                    "key": k,
                    "name": v["name"],
                    "gender": v["gender"],
                    "accent": v["accent"],
                    "tone": v["tone"],
                    "sample_line": v["sample_line"]
                })
        return res

    @classmethod
    def suggest_voice_for_character(cls, character: Character) -> str:
        """Suggests an appropriate Qwen3-TTS voice preset based on character role/gender."""
        gender = (character.gender or "").lower()
        role = (character.role or "").lower()

        if "female" in gender or "woman" in gender:
            if "protagonist" in role or "lead" in role:
                return "qwen_vivian"
            elif "mysterious" in role or "antagonist" in role:
                return "qwen_elena"
            return "qwen_serena"
        else:
            if "protagonist" in role or "co-pro" in role:
                return "qwen_eric"
            elif "antagonist" in role or "authority" in role or "catalyst" in role:
                return "qwen_uncle_martin"
            elif "young" in role or "nervous" in role:
                return "qwen_ryan"
            return "qwen_dylan"

    @classmethod
    def compile_emotion_instruct(cls, emotion_tag: Optional[str] = None, custom_instruct: Optional[str] = None) -> str:
        """Compiles a natural language acting instruct prompt for Qwen3-TTS."""
        if custom_instruct and custom_instruct.strip():
            return custom_instruct.strip()
        
        if not emotion_tag:
            return "Speak naturally with dramatic presence"

        # Check preset dictionary
        for k, v in cls.EMOTION_INSTRUCT_MAP.items():
            if k.lower() in emotion_tag.lower():
                return v

        # Fallback dynamic conversion
        clean_tag = emotion_tag.replace("Current Shot Emotion:", "").strip()
        return f"Speak in a {clean_tag.lower()} tone with authentic emotional acting and dramatic intensity"

    @classmethod
    def generate_audition(
        cls,
        voice_id: str,
        sample_text: Optional[str] = None,
        instruct: Optional[str] = None,
        provider_name: str = "modal"
    ) -> bytes:
        """Generates a live voice audition preview audio clip using Qwen3-TTS."""
        preset = cls.VOICE_PRESETS.get(voice_id, cls.VOICE_PRESETS["qwen_vivian"])
        text = sample_text or preset["sample_line"]
        speaker = preset.get("speaker", "Vivian")

        provider = get_audio_provider(provider_name)
        req = AudioGenerationRequest(
            text=text,
            voice=speaker,
            instruct=instruct or "Speak clearly and expressively with dramatic tone",
            speed=1.0
        )
        res = provider.generate_speech(req)
        return res.audio_bytes

    @classmethod
    def suggest_acting_style(cls, emotion: Optional[str] = None, dialogue_text: str = "") -> str:
        """Classifies shot emotion and dialogue text into the most fitting acting style preset."""
        combined = f"{emotion or ''} {dialogue_text or ''}".lower()
        
        if any(w in combined for w in ["whisper", "quiet", "hush", "terrified", "dread", "shaking", "creeping"]):
            return "Whispering & Terrified"
        elif any(w in combined for w in ["shout", "scream", "urgent", "panic", "hurry", "run", "fast", "adrenaline", "danger", "now!"]):
            return "Urgent & Shouting"
        elif any(w in combined for w in ["breathless", "gasp", "tense", "anxiety", "tight", "hesitation", "strain", "fear"]):
            return "Tense & Breathless"
        elif any(w in combined for w in ["cold", "controlled", "eerie", "calculated", "sinister", "serene", "unblinking", "waxy", "porcelain", "smile"]):
            return "Cold & Controlled"
        elif any(w in combined for w in ["analytical", "grounded", "cautious", "focused", "inspect", "check", "steady", "resolve"]):
            return "Grounded & Analytical"
        elif any(w in combined for w in ["sarcastic", "dismissive", "laugh", "party", "carefree", "smirk", "mock"]):
            return "Sarcastic & Dismissive"
        elif any(w in combined for w in ["grief", "sorrow", "weep", "cry", "sob", "tears", "loss", "despair"]):
            return "Sorrowful & Weeping"
        else:
            return "Tense & Breathless" if "tense" in combined else "Neutral / Conversational"

    @classmethod
    def auto_detect_speaker_and_text(cls, dialogue_text: str, available_characters: List[str]) -> tuple[str, str]:
        """Auto-detects the speaking character name and returns the clean spoken line.
        
        Example:
            'David: "Pull the latch!"' -> ('David', 'Pull the latch!')
            '"Don\'t move!"' with available_characters=['Lucy'] -> ('Lucy', 'Don\'t move!')
        """
        speaker_prefix, clean_line = cls.clean_dialogue_text(dialogue_text)
        if speaker_prefix:
            for char_name in available_characters:
                if char_name.lower() in speaker_prefix.lower() or speaker_prefix.lower() in char_name.lower():
                    return char_name, clean_line
            return speaker_prefix, clean_line
        
        default_speaker = available_characters[0] if available_characters else "Narrator"
        return default_speaker, clean_line or (dialogue_text or "")

    @classmethod
    def clean_dialogue_text(cls, raw_dialogue: str) -> tuple[str, str]:
        """Extracts speaker prefix (if any) and cleans spoken text for TTS synthesis.
        
        Example:
            'Lucy: "Did you hear that?"' -> ('Lucy', 'Did you hear that?')
            'David: Stay close to me.'   -> ('David', 'Stay close to me.')
            'Look out!'                 -> ('', 'Look out!')
        """
        if not raw_dialogue:
            return "", ""
        
        text = raw_dialogue.strip()
        speaker = ""

        # Check for Speaker: Prefix
        if ":" in text:
            parts = text.split(":", 1)
            prefix = parts[0].strip()
            # If prefix is short and looks like a character name
            if len(prefix) <= 30 and not any(p in prefix for p in [".", ",", "?", "!"]):
                speaker = prefix
                text = parts[1].strip()

        # Strip surrounding quotes and whitespace
        text = text.strip("\"' ")
        return speaker, text

    @classmethod
    def synthesize_shot_dialogue(
        cls,
        db: Session,
        project_id: str,
        shot_id: str,
        character: Character,
        dialogue_text: str,
        emotion: Optional[str] = None,
        custom_instruct: Optional[str] = None,
        provider_name: str = "modal"
    ) -> Optional[Asset]:
        """Synthesizes dialogue for a shot using Qwen3-TTS 1.7B with emotion instruct."""
        if not dialogue_text or not dialogue_text.strip():
            return None

        # Clean dialogue text and auto-resolve speaker character if formatted as 'Name: ...'
        detected_speaker, clean_text = cls.clean_dialogue_text(dialogue_text)
        speech_text = clean_text if clean_text else dialogue_text.strip()

        # If detected speaker matches another project character, switch to that character's voice
        active_character = character
        if detected_speaker:
            matched_char = cls.get_dialogue_character(db, project_id, detected_speaker)
            if matched_char:
                active_character = matched_char

        voice_id = active_character.voice_description if getattr(active_character, "voice_description", None) in cls.VOICE_PRESETS else cls.suggest_voice_for_character(active_character)
        preset = cls.VOICE_PRESETS.get(voice_id, cls.VOICE_PRESETS["qwen_vivian"])
        speaker = preset.get("speaker", "Vivian")

        # Compile acting instruct prompt
        compiled_instruct = cls.compile_emotion_instruct(emotion_tag=emotion, custom_instruct=custom_instruct)

        provider = get_audio_provider(provider_name)
        req = AudioGenerationRequest(
            text=speech_text,
            voice=speaker,
            instruct=compiled_instruct,
            speed=0.95 if "whisper" in compiled_instruct.lower() else 1.05 if "urgent" in compiled_instruct.lower() else 1.0
        )
        res = provider.generate_speech(req)

        # Save audio asset to project storage
        saved_asset = AssetService.save_audio_asset(
            db=db,
            project_id=project_id,
            audio_bytes=res.audio_bytes,
            prompt=dialogue_text,
            provider=provider_name,
            model="Qwen3-TTS-12Hz-1.7B",
            duration=res.duration_seconds,
            parameters={
                "shot_id": shot_id,
                "character_id": active_character.id,
                "character_name": active_character.name,
                "voice_id": voice_id,
                "speaker": speaker,
                "emotion": emotion or "neutral",
                "instruct": compiled_instruct,
                "duration_seconds": res.duration_seconds,
                "clean_text": speech_text
            }
        )

        # Update Shot audio reference and duration if necessary
        shot = db.query(Shot).filter(Shot.id == shot_id).first()
        if shot:
            refs = list(shot.reference_asset_ids or [])
            if saved_asset.id not in refs:
                refs.append(saved_asset.id)
                shot.reference_asset_ids = refs
            # Sync shot duration to dialogue if dialogue exceeds current shot duration
            if res.duration_seconds > (shot.duration_seconds or 2.0):
                shot.duration_seconds = round(res.duration_seconds + 0.5, 1)  # add 0.5s padding
            db.commit()

        return saved_asset

    @classmethod
    def get_audio_for_shot(cls, db: Session, shot_id: str) -> Optional[Asset]:
        """Retrieves the latest synthesized audio asset for a given shot."""
        assets = db.query(Asset).filter(Asset.type == AssetType.AUDIO.value).order_by(Asset.created_at.desc()).all()
        for a in assets:
            if a.parameters and a.parameters.get("shot_id") == shot_id:
                return a
        return None

    @classmethod
    def get_dialogue_character(cls, db: Session, project_id: str, character_name: str) -> Optional[Character]:
        """Finds character by name within project for dialogue assignment."""
        if not character_name:
            return None
        return db.query(Character).filter(
            Character.project_id == project_id,
            Character.name.ilike(f"%{character_name.strip()}%")
        ).first()

