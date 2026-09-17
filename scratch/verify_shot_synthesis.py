from core.database import get_db_session
from core.models import Project, Character, Shot
from core.voice_service import VoiceService

with get_db_session() as db:
    project = db.query(Project).first()
    char = db.query(Character).filter(Character.project_id == project.id).first()
    shot = db.query(Shot).first()
    print(f"Directing Shot {shot.shot_number} with Character {char.name} ({char.voice_description})...")

    asset = VoiceService.synthesize_shot_dialogue(
        db=db,
        project_id=project.id,
        shot_id=shot.id,
        character=char,
        dialogue_text="Someone is watching us from the shadows... please, don't open that door!",
        emotion="Whispering & Terrified",
        custom_instruct="Speak in a terrified, trembling whisper with rising dread",
        provider_name="modal"
    )

    print(f"✅ Generated Audio Asset: ID={asset.id}, File={asset.file_path}, Duration={asset.duration}s")
