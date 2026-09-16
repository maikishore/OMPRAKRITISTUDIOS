import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from core.models import Project, Character, Location, Scene, Shot, Asset
from core.enums import ProjectStatus, ShotStatus, AssetType
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.location_service import LocationService
from core.scene_service import SceneService
from core.shot_service import ShotService
from core.asset_service import AssetService
from schemas.project import ProjectCreate
from schemas.character import CharacterCreate
from schemas.location import LocationCreate
from schemas.scene import SceneCreate
from schemas.shot import ShotCreate
from providers.image.base import ImageGenerationRequest
from providers.image.mock_provider import MockImageProvider
from providers.image.factory import get_image_provider

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

def test_mock_image_provider():
    provider = MockImageProvider()
    assert provider.capabilities["text_to_image"] is True
    assert provider.capabilities["face_lock"] is True

    req = ImageGenerationRequest(
        prompt="Cinematic portrait of Lucy in crimson silk dress",
        width=768,
        height=1344,
        seed=42
    )
    res = provider.generate(req)
    assert res.image_bytes is not None
    assert len(res.image_bytes) > 100
    assert res.mime_type == "image/png"
    assert res.seed == 42

def test_asset_storage_and_character_master_linking(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )
    char = CharacterService.create_character(
        db_session,
        CharacterCreate(
            project_id=project.id,
            name="Lucy",
            appearance="Brunette, shoulder length hair",
            clothing="Crimson silk cocktail dress"
        )
    )
    assert char.master_reference_asset_id is None
    assert char.is_approved is False

    # 1. Generate image using provider
    provider = MockImageProvider()
    req = ImageGenerationRequest(prompt="Portrait of Lucy", width=768, height=1344)
    res = provider.generate(req)

    # 2. Save image asset to disk and db
    asset = AssetService.save_image_asset(
        db=db_session,
        project_id=project.id,
        asset_type=AssetType.CHARACTER_REFERENCE.value,
        image_bytes=res.image_bytes,
        prompt="Portrait of Lucy",
        seed=42,
        provider="mock",
        model="FLUX.1 [dev]"
    )
    assert asset.id is not None
    assert Path(asset.file_path).exists()

    # 3. Set as master visual identity reference
    success = AssetService.set_character_master_reference(db_session, char.id, asset.id)
    assert success is True

    updated_char = CharacterService.get_character(db_session, char.id)
    assert updated_char.master_reference_asset_id == asset.id
    assert updated_char.is_approved is True
    assert asset.is_approved is True

def test_location_master_linking(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )
    loc = LocationService.create_location(
        db_session,
        LocationCreate(
            project_id=project.id,
            name="Toy Store",
            architecture="Vintage wooden shelves",
            lighting="Flickering amber"
        )
    )

    provider = MockImageProvider()
    res = provider.generate(ImageGenerationRequest(prompt="Toy Store concept", width=1024, height=576))

    asset = AssetService.save_image_asset(
        db=db_session,
        project_id=project.id,
        asset_type=AssetType.LOCATION_REFERENCE.value,
        image_bytes=res.image_bytes,
        prompt="Toy Store concept",
        provider="mock"
    )

    success = AssetService.set_location_master_reference(db_session, loc.id, asset.id)
    assert success is True
    updated_loc = LocationService.get_location(db_session, loc.id)
    assert updated_loc.master_reference_asset_id == asset.id
    assert updated_loc.is_approved is True

def test_shot_keyframe_linking(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )
    scene = SceneService.create_scene(
        db_session,
        SceneCreate(project_id=project.id, scene_number=1, title="Atrium Opening", duration_seconds=55)
    )
    shot = ShotService.create_shot(
        db_session,
        ShotCreate(scene_id=scene.id, shot_number=1, duration_seconds=5.0, action="Lucy looks around")
    )
    assert shot.status == ShotStatus.DRAFT.value

    # Save and link keyframe
    provider = MockImageProvider()
    res = provider.generate(ImageGenerationRequest(prompt="Keyframe shot 1", width=768, height=1344))
    kf_asset = AssetService.save_image_asset(
        db=db_session,
        project_id=project.id,
        asset_type=AssetType.KEYFRAME.value,
        image_bytes=res.image_bytes,
        prompt="Keyframe shot 1",
        provider="modal"
    )

    linked = AssetService.link_shot_keyframe(db_session, shot.id, kf_asset.id)
    assert linked is True

    updated_shot = ShotService.get_shot(db_session, shot.id)
    assert kf_asset.id in updated_shot.reference_asset_ids
    assert updated_shot.status == ShotStatus.KEYFRAME_READY.value

def test_image_provider_factory():
    modal_p = get_image_provider("modal")
    assert modal_p is not None

    cf_p = get_image_provider("cloudflare")
    assert cf_p is not None

    mock_p = get_image_provider("mock")
    assert mock_p is not None
