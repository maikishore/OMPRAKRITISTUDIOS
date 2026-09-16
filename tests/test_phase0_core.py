import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from core.models import Project, Story, Character, Location, Scene, Shot, Asset, GenerationJob
from core.enums import ProjectStatus, AssetType, JobStatus, JobType
from core.project_service import ProjectService
from core.asset_service import AssetService
from core.job_service import JobService
from schemas.project import ProjectCreate, ProjectUpdate
from schemas.story import StorySchema
from schemas.character import CharacterBase
from schemas.asset import AssetCreate
from schemas.job import JobCreate
from storage.paths import StoragePaths
from storage.object_store import LocalObjectStore

@pytest.fixture
def db_session():
    # Use in-memory SQLite for high-speed test isolation
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_project_crud_lifecycle(db_session):
    # 1. Create Project
    data = ProjectCreate(
        title="After Closing",
        genre="Horror",
        target_duration_seconds=600,
        logline="Trapped in a mall after closing with mannequins."
    )
    project = ProjectService.create_project(db_session, data)
    assert project.id is not None
    assert project.title == "After Closing"
    assert project.status == ProjectStatus.IDEA.value

    # 2. Get Project
    fetched = ProjectService.get_project(db_session, project.id)
    assert fetched is not None
    assert fetched.genre == "Horror"

    # 3. Update Project Status
    updated = ProjectService.update_project(
        db_session,
        project.id,
        ProjectUpdate(status=ProjectStatus.STORY_DRAFT)
    )
    assert updated.status == ProjectStatus.STORY_DRAFT.value

    # 4. List Projects
    all_projects = ProjectService.list_projects(db_session)
    assert len(all_projects) == 1

def test_story_schema_validation():
    story_dict = {
        "premise": "Lucy is locked in a dark shopping mall.",
        "theme": "Inevitable transformation",
        "tone": "Cold dread and surreal horror",
        "synopsis": "Lucy must solve games in the closed mall, only to realize the games transform her into a mannequin.",
        "ending": "Lucy turns into a mannequin alongside David and Emma as the morning announcer says 'Next Player'.",
        "story_rules": ["Games cannot be forfeited", "Lights turn off per completed stage"],
        "acts": [{"act": 1, "description": "Arrival and lockdown"}],
        "clues": ["Flickering mannequins", "Distant announcements"],
        "continuity_rules": ["Lucy wears red jacket and silver pendant"]
    }
    story = StorySchema.model_validate(story_dict)
    assert story.premise.startswith("Lucy is locked")
    assert len(story.story_rules) == 2

def test_asset_and_job_lifecycle(db_session):
    # Create parent project
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="Test Asset Project", genre="Sci-Fi")
    )

    # 1. Job Lifecycle
    job = JobService.create_job(
        db_session,
        JobCreate(
            project_id=project.id,
            type=JobType.KEYFRAME_IMAGE,
            provider="modal-flux",
            payload={"prompt": "Cinematic wide shot of mall atrium"}
        )
    )
    assert job.status == JobStatus.QUEUED.value
    assert job.progress == 0.0

    updated_job = JobService.update_job_status(
        db_session,
        job.id,
        JobStatus.RUNNING,
        progress=0.5
    )
    assert updated_job.status == JobStatus.RUNNING.value
    assert updated_job.started_at is not None

    # 2. Asset Lifecycle
    asset = AssetService.create_asset(
        db_session,
        AssetCreate(
            project_id=project.id,
            type=AssetType.KEYFRAME,
            file_path="projects/test/keyframes/shot_001.png",
            mime_type="image/png",
            provider="modal-flux",
            prompt="Cinematic wide shot of mall atrium",
            seed=42
        )
    )
    assert asset.id is not None
    assert asset.is_approved is False

    approved_asset = AssetService.approve_asset(db_session, asset.id, approved=True)
    assert approved_asset.is_approved is True

    # Complete job
    completed_job = JobService.update_job_status(
        db_session,
        job.id,
        JobStatus.SUCCEEDED,
        progress=1.0,
        result_asset_ids=[asset.id]
    )
    assert completed_job.status == JobStatus.SUCCEEDED.value
    assert completed_job.completed_at is not None

def test_storage_path_and_object_store(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"HELLO MICRODRAMA STUDIO")
    
    saved = LocalObjectStore.save_file(b"BINARY TEST ASSET", tmp_path / "output.bin")
    assert saved.exists()
    assert LocalObjectStore.read_file(saved) == b"BINARY TEST ASSET"
