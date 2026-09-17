import pytest
from core.database import get_db_session
from core.models import Project, Character, Shot
from core.voice_service import VoiceService
from providers.audio.factory import get_audio_provider
from providers.audio.base import AudioGenerationRequest

def test_voice_presets_catalog():
    presets = VoiceService.list_presets()
    assert len(presets) >= 5
    keys = [p["key"] for p in presets]
    assert "af_sarah" in keys
    assert "am_adam" in keys
    assert "am_michael" in keys

def test_voice_suggestion_logic():
    char_female = Character(id="c1", name="Lucy Vance", gender="Female", role="Protagonist")
    char_male = Character(id="c2", name="David Cruz", gender="Male", role="Co-Protagonist")
    char_boss = Character(id="c3", name="Marcus Kane", gender="Male", role="Antagonist")

    assert VoiceService.suggest_voice_for_character(char_female) == "af_sarah"
    assert VoiceService.suggest_voice_for_character(char_male) == "am_adam"
    assert VoiceService.suggest_voice_for_character(char_boss) == "am_michael"

def test_mock_audio_generation():
    provider = get_audio_provider("mock")
    req = AudioGenerationRequest(
        text="The doors are completely locked from the outside!",
        voice="af_sarah"
    )
    res = provider.generate_speech(req)
    assert isinstance(res.audio_bytes, bytes)
    assert len(res.audio_bytes) > 100
    assert res.mime_type == "audio/wav"
    assert res.duration_seconds > 1.0

def test_synthesize_shot_dialogue():
    with get_db_session() as db:
        # Create test project, character, and shot
        project = Project(id="proj-audio-test", title="Audio Test Movie", genre="Horror")
        char = Character(id="char-audio-1", project_id=project.id, name="Lucy Vance", gender="Female", role="Protagonist", voice_description="af_sarah")
        shot = Shot(id="shot-audio-1", scene_id="sc-dummy", shot_number=1, dialogue="Someone is watching us.", duration_seconds=2.0)

        db.add(project)
        db.add(char)
        db.add(shot)
        db.commit()

        # Synthesize shot dialogue with mock
        saved_asset = VoiceService.synthesize_shot_dialogue(
            db=db,
            project_id=project.id,
            shot_id=shot.id,
            character=char,
            dialogue_text=shot.dialogue,
            emotion="terrified",
            provider_name="mock"
        )

        assert saved_asset is not None
        assert saved_asset.type == "AUDIO"
        assert saved_asset.parameters["character_name"] == "Lucy Vance"
        assert saved_asset.parameters["voice_id"] == "af_sarah"
