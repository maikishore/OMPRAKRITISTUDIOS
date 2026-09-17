"""Voice Casting & Dialogue Synthesis Service.

Manages character voice profiles, audition previews, and shot-level dialogue audio generation.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from core.models import Character, Shot, Asset
from core.enums import AssetType
from core.asset_service import AssetService
from providers.audio.factory import get_audio_provider
from providers.audio.base import AudioGenerationRequest

class VoiceService:
    """Manages voice presets, audition previews, and dialogue audio generation."""

    VOICE_PRESETS: Dict[str, Dict[str, Any]] = {
        "af_sarah": {
            "name": "Sarah (American Female - Tense / Dramatic)",
            "gender": "Female",
            "accent": "American",
            "tone": "Tense, emotional, youthful",
            "sample_line": "Did you hear that? I'm telling you, someone else is in this building with us!"
        },
        "am_adam": {
            "name": "Adam (American Male - Gritty / Grounded)",
            "gender": "Male",
            "accent": "American",
            "tone": "Grounded, deep, cautious",
            "sample_line": "Stay behind me. The exit gate is jammed, but there's a service stairwell in the back."
        },
        "am_michael": {
            "name": "Michael (American Male - Authoritative / Deep)",
            "gender": "Male",
            "accent": "American",
            "tone": "Resonant, stern, controlled",
            "sample_line": "All retail staff must report to the security dispatch immediately. Do not open the doors."
        },
        "af_nicole": {
            "name": "Nicole (American Female - Whispering / Eerie)",
            "gender": "Female",
            "accent": "American",
            "tone": "Soft, whispering, suspenseful",
            "sample_line": "Quiet... look at the mirrors in the atrium. The reflections aren't moving with us."
        },
        "af_bella": {
            "name": "Bella (American Female - Warm / Expressive)",
            "gender": "Female",
            "accent": "American",
            "tone": "Clear, dynamic, conversational",
            "sample_line": "I managed to bypass the security console, but the backup generators are failing fast."
        },
        "am_george": {
            "name": "George (British Male - Sophisticated)",
            "gender": "Male",
            "accent": "British",
            "tone": "Composed, analytical, sharp",
            "sample_line": "Curious. The electrical surge originated from deep inside the ventilation sub-level."
        },
        "bf_emma": {
            "name": "Emma (British Female - Crisp / Analytical)",
            "gender": "Female",
            "accent": "British",
            "tone": "Precise, alert, clear",
            "sample_line": "The security camera feeds are looping every twenty seconds. We're completely blind."
        }
    }

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """Returns list of all available voice presets."""
        res = []
        for k, v in cls.VOICE_PRESETS.items():
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
        """Suggests an appropriate voice preset based on character role/gender."""
        gender = (character.gender or "").lower()
        role = (character.role or "").lower()

        if "female" in gender or "woman" in gender:
            if "protagonist" in role or "lead" in role:
                return "af_sarah"
            elif "mysterious" in role or "antagonist" in role:
                return "af_nicole"
            return "af_bella"
        else:
            if "protagonist" in role or "co-pro" in role:
                return "am_adam"
            elif "antagonist" in role or "authority" in role or "catalyst" in role:
                return "am_michael"
            return "am_george"

    @classmethod
    def generate_audition(
        cls,
        voice_id: str,
        sample_text: Optional[str] = None,
        provider_name: str = "modal"
    ) -> bytes:
        """Generates a live voice audition preview audio clip."""
        preset = cls.VOICE_PRESETS.get(voice_id, cls.VOICE_PRESETS["af_sarah"])
        text = sample_text or preset["sample_line"]

        provider = get_audio_provider(provider_name)
        req = AudioGenerationRequest(
            text=text,
            voice=voice_id,
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
        provider_name: str = "modal"
    ) -> Optional[Asset]:
        """Synthesizes dialogue for a shot, saves audio asset, and updates shot audio timing."""
        if not dialogue_text or not dialogue_text.strip():
            return None

        voice_id = character.voice_description if character.voice_description in cls.VOICE_PRESETS else cls.suggest_voice_for_character(character)
        
        # Prepare spoken text (can prepend emotional pacing if needed)
        provider = get_audio_provider(provider_name)
        req = AudioGenerationRequest(
            text=dialogue_text.strip(),
            voice=voice_id,
            speed=0.95 if emotion and "whisper" in emotion.lower() else 1.05 if emotion and "urgent" in emotion.lower() else 1.0
        )
        res = provider.generate_speech(req)

        # Save audio asset to project storage
        saved_asset = AssetService.save_audio_asset(
            db=db,
            project_id=project_id,
            audio_bytes=res.audio_bytes,
            prompt=dialogue_text,
            provider=provider_name,
            model="Kokoro-82M",
            duration=res.duration_seconds,
            parameters={
                "shot_id": shot_id,
                "character_id": character.id,
                "character_name": character.name,
                "voice_id": voice_id,
                "emotion": emotion or "neutral",
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
        # Check assets where parameters JSON contains shot_id
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
