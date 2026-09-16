import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from OMVERSION.core.database import Base
from OMVERSION.core.models import Project, Story
from OMVERSION.core.enums import ProjectStatus
from OMVERSION.core.project_service import ProjectService
from OMVERSION.schemas.project import ProjectCreate
from OMVERSION.schemas.story import StorySchema
from OMVERSION.ai.llm_client import LLMClient
from OMVERSION.ai.story_engine import StoryEngine

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

def test_llm_client_json_extraction():
    # 1. Clean markdown fences
    raw_markdown = "```json\n{\"title\": \"After Closing\", \"count\": 3}\n```"
    extracted = LLMClient._extract_json(raw_markdown)
    assert extracted["title"] == "After Closing"
    assert extracted["count"] == 3

    # 2. Conversational wrapping
    noisy_text = "Sure, here is the structured data:\n{\"premise\": \"Locked in mall\"}\nHope this helps!"
    extracted_noisy = LLMClient._extract_json(noisy_text)
    assert extracted_noisy["premise"] == "Locked in mall"

def test_story_engine_generation_and_approval(db_session):
    project = ProjectService.create_project(
        db_session,
        ProjectCreate(title="After Closing", genre="Horror", target_duration_seconds=600)
    )
    assert project.status == ProjectStatus.IDEA.value

    engine = StoryEngine()
    # Generate story
    story_schema = engine.generate_story(
        title=project.title,
        genre=project.genre,
        idea="Trapped in a mall after closing with mannequins.",
        target_duration_seconds=600
    )
    assert isinstance(story_schema, StorySchema)
    assert len(story_schema.acts) == 3
    assert len(story_schema.story_rules) >= 2

    # Save as Draft
    draft_story = engine.save_story(db_session, project.id, story_schema, approve=False)
    assert draft_story.is_approved is False
    assert project.status == ProjectStatus.STORY_DRAFT.value

    # Approve Story Gate
    approved_story = engine.save_story(db_session, project.id, story_schema, approve=True)
    assert approved_story.is_approved is True
    assert project.status == ProjectStatus.STORY_APPROVED.value
