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

        voice_id = character.voice_description if character.voice_description in cls.VOICE_PRESETS else cls.suggest_voice_for_character(character)
        preset = cls.VOICE_PRESETS.get(voice_id, cls.VOICE_PRESETS["qwen_vivian"])
        speaker = preset.get("speaker", "Vivian")

        # Compile acting instruct prompt
        compiled_instruct = cls.compile_emotion_instruct(emotion_tag=emotion, custom_instruct=custom_instruct)

        provider = get_audio_provider(provider_name)
        req = AudioGenerationRequest(
            text=dialogue_text.strip(),
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
                "character_id": character.id,
                "character_name": character.name,
                "voice_id": voice_id,
                "speaker": speaker,
                "emotion": emotion or "neutral",
                "instruct": compiled_instruct,
                "duration_seconds": res.duration_seconds
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
