import pytest
import uuid
from core.database import get_db_session
from core.models import Project, Character, Shot
from core.voice_service import VoiceService
from providers.audio.factory import get_audio_provider
from providers.audio.base import AudioGenerationRequest

def test_voice_presets_catalog():
    presets = VoiceService.list_presets()
    assert len(presets) >= 10
    keys = [p["key"] for p in presets]
    assert "qwen_vivian" in keys
    assert "qwen_eric" in keys
    assert "qwen_emma_child" in keys
    assert "qwen_timmy_child" in keys
    assert "qwen_grandma_martha" in keys
    assert "qwen_grandpa_arthur" in keys
    assert "qwen_uncle_martin" in keys

def test_voice_suggestion_logic():
    char_female = Character(id="c1", name="Lucy Vance", gender="Female", role="Protagonist", age="26")
    char_male = Character(id="c2", name="David Cruz", gender="Male", role="Co-Protagonist", age="28")
    char_child_f = Character(id="c3", name="Emma", gender="Female", role="Mysterious Child", age="8")
    char_child_m = Character(id="c4", name="Timmy", gender="Male", role="Young Kid", age="10")
    char_elder_f = Character(id="c5", name="Martha", gender="Female", role="Elderly Grandmother", age="75")
    char_elder_m = Character(id="c6", name="Arthur", gender="Male", role="Old Veteran / Grandfather", age="80")

    assert VoiceService.suggest_voice_for_character(char_female) == "qwen_vivian"
    assert VoiceService.suggest_voice_for_character(char_male) == "qwen_eric"
    assert VoiceService.suggest_voice_for_character(char_child_f) == "qwen_emma_child"
    assert VoiceService.suggest_voice_for_character(char_child_m) == "qwen_timmy_child"
    assert VoiceService.suggest_voice_for_character(char_elder_f) == "qwen_grandma_martha"
    assert VoiceService.suggest_voice_for_character(char_elder_m) == "qwen_grandpa_arthur"

def test_emotion_instruct_compilation():
    whisper_inst = VoiceService.compile_emotion_instruct("Whispering & Terrified")
    assert "whisper" in whisper_inst.lower()
    assert "fear" in whisper_inst.lower() or "terrified" in whisper_inst.lower()

    # Test with voice profile base instruct
    child_inst = VoiceService.compile_emotion_instruct("Whispering & Terrified", voice_id="qwen_emma_child")
    assert "child" in child_inst.lower() or "8-year-old" in child_inst.lower()
    assert "whisper" in child_inst.lower()

    custom_inst = VoiceService.compile_emotion_instruct(custom_instruct="Crying and shouting in sheer panic")
    assert custom_inst == "Crying and shouting in sheer panic"

def test_mock_audio_generation():
    provider = get_audio_provider("mock")
    req = AudioGenerationRequest(
        text="The doors are completely locked from the outside!",
        voice="qwen_vivian",
        instruct="Speak in a terrified whisper"
    )
    res = provider.generate_speech(req)
    assert isinstance(res.audio_bytes, bytes)
    assert len(res.audio_bytes) > 100
    assert res.mime_type == "audio/wav"
    assert res.duration_seconds > 1.0

def test_synthesize_shot_dialogue_with_qwen():
    with get_db_session() as db:
        p_id = f"proj-audio-{uuid.uuid4().hex[:8]}"
        c_id = f"char-audio-{uuid.uuid4().hex[:8]}"
        s_id = f"shot-audio-{uuid.uuid4().hex[:8]}"

        project = Project(id=p_id, title="Audio Test Movie", genre="Horror")
        char = Character(id=c_id, project_id=project.id, name="Lucy Vance", gender="Female", role="Protagonist", voice_description="qwen_vivian")
        shot = Shot(id=s_id, scene_id="sc-dummy", shot_number=1, dialogue="Someone is watching us.", duration_seconds=2.0)

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
            emotion="Whispering & Terrified",
            provider_name="mock"
        )

        assert saved_asset is not None
        assert saved_asset.type == "AUDIO"
        assert saved_asset.parameters["character_name"] == "Lucy Vance"
        assert saved_asset.parameters["voice_id"] == "qwen_vivian"
        assert "instruct" in saved_asset.parameters

        # Check retrieval
        retrieved_audio = VoiceService.get_audio_for_shot(db, shot.id)
        assert retrieved_audio is not None
        assert retrieved_audio.id == saved_asset.id

def test_speaker_and_style_auto_detection():
    # 1. Speaker & text auto-detection
    spk1, text1 = VoiceService.auto_detect_speaker_and_text("David: 'The emergency latch is jammed!'", ["Lucy", "David"])
    assert spk1 == "David"
    assert text1 == "The emergency latch is jammed!"

    spk2, text2 = VoiceService.auto_detect_speaker_and_text('Lucy: "Can you hear that?"', ["Lucy", "David"])
    assert spk2 == "Lucy"
    assert text2 == "Can you hear that?"

    spk3, text3 = VoiceService.auto_detect_speaker_and_text("Look out!", ["Lucy", "David"])
    assert spk3 == "Lucy"
    assert text3 == "Look out!"

    # 2. Acting style auto-suggestion
    assert VoiceService.suggest_acting_style("Terrified dread", "(whispering) Don't look back") == "Whispering & Terrified"
    assert VoiceService.suggest_acting_style("Panic and urgency", "Run, the gates are closing down now!") == "Urgent & Shouting"
    assert VoiceService.suggest_acting_style("Breathless tension", "I can't breathe...") == "Tense & Breathless"
    assert VoiceService.suggest_acting_style("Eerie calmness", "All obedient models are allowed to greet the morning.") == "Cold & Controlled"
    assert VoiceService.suggest_acting_style("Focused resolve", "Let's inspect the CCTV terminal.") == "Grounded & Analytical"
    assert VoiceService.suggest_acting_style("Grief and heartbreak", "He's gone... I'm so sorry...") == "Sorrowful & Weeping"

