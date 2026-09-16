import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from core.models import Project, Story, Character, Location, VisualStyle
from core.enums import ProjectStatus
from core.project_service import ProjectService
from core.character_service import CharacterService
from core.location_service import LocationService
from core.style_service import StyleService
from schemas.project import ProjectCreate
from schemas.character import CharacterCreate, CharacterUpdate
from schemas.location import LocationCreate, LocationUpdate
from schemas.style import VisualStyleSchema
from ai.character_engine import CharacterEngine
from ai.location_engine import LocationEngine
from ai.style_engine import StyleEngine

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

def test_character_lifecycle_and_approval(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )

    engine = CharacterEngine()
    characters = engine.generate_characters_from_story(project)
    assert len(characters) >= 2
    assert characters[0].name == "Lucy Vance"

    # Save to DB
    for c in characters:
        CharacterService.create_character(db_session, c)

    saved = CharacterService.list_project_characters(db_session, project.id)
    assert len(saved) == len(characters)
    assert all(not char.is_approved for char in saved)

    # Approve all characters
    approved = CharacterService.approve_all_characters(db_session, project.id)
    assert approved is True
    assert project.status == ProjectStatus.CHARACTERS_READY.value

def test_location_lifecycle_and_approval(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )

    engine = LocationEngine()
    locations = engine.generate_locations_from_story(project)
    assert len(locations) >= 3

    for loc in locations:
        LocationService.create_location(db_session, loc)

    saved_locs = LocationService.list_project_locations(db_session, project.id)
    assert len(saved_locs) == len(locations)

    # Approve all locations
    approved = LocationService.approve_all_locations(db_session, project.id)
    assert approved is True
    assert project.status == ProjectStatus.LOCATIONS_READY.value

def test_style_lifecycle_and_approval(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )

    engine = StyleEngine()
    style_schema = engine.generate_style_from_story(project)
    assert isinstance(style_schema, VisualStyleSchema)
    assert len(style_schema.visual_motifs) >= 2

    # Save and Approve Style
    style_record = StyleService.save_or_update_style(db_session, project.id, style_schema, approve=True)
    assert style_record.is_approved is True
    assert project.status == ProjectStatus.STYLE_READY.value
