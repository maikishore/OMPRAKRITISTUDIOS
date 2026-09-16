import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from core.models import Project, Scene, Shot, PromptVersion
from core.enums import ProjectStatus, ShotStatus
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.location_service import LocationService
from core.style_service import StyleService
from core.scene_service import SceneService
from core.shot_service import ShotService
from schemas.project import ProjectCreate
from schemas.scene import SceneCreate
from schemas.shot import ShotCreate
from schemas.character import CharacterCreate
from schemas.location import LocationCreate
from schemas.style import VisualStyleCreate
from ai.image_prompt_engine import PromptCompiler
from ai.scene_engine import SceneEngine
from ai.shot_engine import ShotEngine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_scene_lifecycle_and_duration_budget(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )

    # 1. Create Scenes
    s1 = SceneService.create_scene(
        db_session,
        SceneCreate(
            project_id=project.id,
            scene_number=1,
            title="Party Closing",
            duration_seconds=55,
            summary="Party lights flicker out.",
            purpose="Inciting incident",
            characters=["Lucy", "David"]
        )
    )
    s2 = SceneService.create_scene(
        db_session,
        SceneCreate(
            project_id=project.id,
            scene_number=2,
            title="Shutters Lock",
            duration_seconds=50,
            summary="Steel doors slam shut.",
            purpose="Lock in reversal",
            characters=["Lucy", "David"]
        )
    )

    scenes = SceneService.list_scenes_by_project(db_session, project.id)
    assert len(scenes) == 2
    assert scenes[0].scene_number == 1
    assert scenes[1].scene_number == 2

    # 2. Runtime duration calculation
    budget = SceneService.calculate_total_runtime(db_session, project.id)
    assert budget["total_seconds"] == 105
    assert budget["target_seconds"] == 600
    assert budget["delta_seconds"] == -495

    # 3. Approve all scenes
    approved = SceneService.approve_all_scenes(db_session, project.id)
    assert approved is True
    updated_proj = ProjectService.get_project(db_session, project.id)
    assert updated_proj.status == ProjectStatus.SCENES_READY.value

def test_shot_lifecycle_and_prompt_versioning(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )
    scene = SceneService.create_scene(
        db_session,
        SceneCreate(
            project_id=project.id,
            scene_number=1,
            title="Opening Atrium",
            duration_seconds=60
        )
    )

    # 1. Create Shot
    shot = ShotService.create_shot(
        db_session,
        ShotCreate(
            scene_id=scene.id,
            shot_number=1,
            duration_seconds=5.5,
            shot_type="Wide Shot",
            camera_movement="Slow Dolly in",
            lens="35mm anamorphic",
            action="Lucy stands in atrium.",
            image_prompt="Initial prompt v1",
            video_prompt="Initial video prompt v1"
        )
    )
    assert shot.id is not None
    assert shot.duration_seconds == 5.5

    # 2. Verify PromptVersion was automatically created
    v_img = ShotService.list_prompt_versions(db_session, "shot_image", shot.id)
    assert len(v_img) == 1
    assert v_img[0].version == 1
    assert v_img[0].prompt == "Initial prompt v1"

    # 3. Update shot prompt and verify non-destructive versioning
    ShotService.update_shot(db_session, shot.id, {"image_prompt": "Revised prompt v2 with new lighting"})
    v_img_updated = ShotService.list_prompt_versions(db_session, "shot_image", shot.id)
    assert len(v_img_updated) == 2
    assert v_img_updated[0].version == 2
    assert v_img_updated[0].prompt == "Revised prompt v2 with new lighting"
    assert v_img_updated[1].version == 1
    assert v_img_updated[1].prompt == "Initial prompt v1"

def test_deterministic_prompt_compiler():
    style = {
        "cinematic_realism": "Ultra-realistic 35mm film capture",
        "contrast": "Deep shadowy",
        "film_grain": "Subtle organic",
        "depth_of_field": "Shallow"
    }
    location = {
        "name": "Toy Store",
        "architecture": "Retro wooden toy shelves with dusty marble floor",
        "materials": "Vintage lacquered wood and brass fittings",
        "lighting": "Flickering amber pendant lamp"
    }
    characters = [
        {
            "name": "Lucy",
            "signature_costume": "Crimson silk cocktail dress",
            "physical_traits": "Athletic build, shoulder-length brunette hair",
            "visual_anchor_prompt": "Brunette woman in crimson cocktail dress"
        }
    ]
    scene = {
        "visual_direction": "Cold overhead spotlights casting long diagonal shadows",
        "sound_design": "Detuned music box lullaby"
    }
    shot = {
        "shot_type": "Close-up",
        "camera_angle": "Low angle",
        "camera_movement": "Slow push-in",
        "lens": "85mm portrait",
        "framing": "Tight focus on facial tension",
        "action": "Lucy reaches toward the porcelain music box",
        "emotion": "Paralyzing dread",
        "lighting": "Edge rim light highlighting high cheekbones",
        "duration_seconds": 6.0
    }

    # 1. Compile Keyframe Image Prompt
    img_prompt = PromptCompiler.compile_image_prompt(
        style_data=style,
        location_data=location,
        characters_data=characters,
        scene_data=scene,
        shot_data=shot
    )

    assert "Close-up" in img_prompt
    assert "85mm portrait" in img_prompt
    assert "Lucy" in img_prompt
    assert "Crimson silk cocktail dress" in img_prompt
    assert "Toy Store" in img_prompt
    assert "Paralyzing dread" in img_prompt
    assert "Ultra-realistic 35mm film capture" in img_prompt

    # 2. Compile Video Prompt
    vid_prompt = PromptCompiler.compile_video_prompt(
        style_data=style,
        location_data=location,
        characters_data=characters,
        scene_data=scene,
        shot_data=shot
    )

    assert "Slow push-in" in vid_prompt
    assert "6.0s duration" in vid_prompt
    assert "Lucy reaches toward the porcelain music box" in vid_prompt
    assert "Paralyzing dread" in vid_prompt

    # 3. Negative Prompt
    neg = PromptCompiler.get_negative_prompt(style)
    assert "cartoon" in neg
    assert "CGI" in neg

def test_scene_and_shot_ai_engines(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )

    # 1. Test SceneEngine seed generation
    scene_engine = SceneEngine()
    scenes = scene_engine.get_seed_scenes_for_after_closing(600)
    assert len(scenes) == 10
    total_dur = sum(s["duration_seconds"] for s in scenes)
    assert 500 <= total_dur <= 700

    # 2. Test ShotEngine seed generation
    shot_engine = ShotEngine()
    shots = shot_engine.get_seed_shots_for_scene(1)
    assert len(shots) == 5
    assert shots[0]["shot_type"] == "Wide Shot"
    assert "Lucy" in shots[0]["characters"]
