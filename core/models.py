from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base, generate_uuid
from .enums import ProjectStatus, AssetType, JobStatus, JobType, ShotStatus

def utc_now():
    return datetime.now(timezone.utc)

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    logline = Column(Text, nullable=True)
    genre = Column(String(100), nullable=False, default="Drama")
    target_duration_seconds = Column(Integer, nullable=False, default=600)  # ~10 min
    language = Column(String(50), nullable=False, default="English")
    aspect_ratio = Column(String(20), nullable=False, default="16:9")
    status = Column(String(50), nullable=False, default=ProjectStatus.IDEA.value)

    # Project settings
    image_model = Column(String(100), nullable=False, default="flux-1-schnell")
    video_model = Column(String(100), nullable=False, default="ltx-2.3")
    default_video_duration = Column(Float, nullable=False, default=5.0)
    default_resolution = Column(String(50), nullable=False, default="1080p")
    default_fps = Column(Integer, nullable=False, default=24)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    story = relationship("Story", back_populates="project", uselist=False, cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    visual_style = relationship("VisualStyle", back_populates="project", uselist=False, cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")


class Story(Base):
    __tablename__ = "stories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    premise = Column(Text, nullable=True)
    theme = Column(String(255), nullable=True)
    tone = Column(String(255), nullable=True)
    synopsis = Column(Text, nullable=True)
    ending = Column(Text, nullable=True)

    # Structured lists stored as JSON
    story_rules = Column(JSON, default=list)
    acts = Column(JSON, default=list)
    clues = Column(JSON, default=list)
    continuity_rules = Column(JSON, default=list)

    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="story")


class Character(Base):
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)  # Protagonist, Antagonist, Supporting
    gender = Column(String(50), nullable=True)
    age = Column(String(50), nullable=True)

    # Appearance & Bible breakdown
    appearance = Column(Text, nullable=True)
    hair = Column(String(255), nullable=True)
    face = Column(String(255), nullable=True)
    body = Column(String(255), nullable=True)
    skin = Column(String(255), nullable=True)
    clothing = Column(Text, nullable=True)
    accessories = Column(Text, nullable=True)

    personality = Column(Text, nullable=True)
    behavior = Column(Text, nullable=True)
    voice_description = Column(Text, nullable=True)
    character_arc = Column(Text, nullable=True)
    continuity_constraints = Column(JSON, default=list)

    # Reference Asset Link
    master_reference_asset_id = Column(String(36), nullable=True)
    identity_prompt = Column(Text, nullable=True)
    negative_constraints = Column(Text, nullable=True)

    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="characters")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    architecture = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)
    lighting = Column(Text, nullable=True)
    time_of_day = Column(String(100), nullable=True)
    visual_identity = Column(Text, nullable=True)
    continuity_constraints = Column(JSON, default=list)

    master_reference_asset_id = Column(String(36), nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="locations")


class VisualStyle(Base):
    __tablename__ = "visual_styles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)

    cinematic_realism = Column(String(255), nullable=True)
    camera_language = Column(Text, nullable=True)
    lens_preferences = Column(String(255), nullable=True)
    lighting_language = Column(Text, nullable=True)
    color_progression = Column(Text, nullable=True)
    contrast = Column(String(100), nullable=True)
    depth_of_field = Column(String(100), nullable=True)
    film_grain = Column(String(100), nullable=True)
    production_design = Column(Text, nullable=True)
    visual_motifs = Column(JSON, default=list)

    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="visual_style")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    scene_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=False, default=45)

    location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    time_of_day = Column(String(100), nullable=True)
    emotional_state = Column(String(255), nullable=True)
    story_beat = Column(String(255), nullable=True)
    dialogue = Column(Text, nullable=True)
    sound_design = Column(Text, nullable=True)
    visual_direction = Column(Text, nullable=True)
    continuity_notes = Column(Text, nullable=True)

    characters = Column(JSON, default=list)  # list of character names/IDs
    is_approved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="scenes")
    shots = relationship("Shot", back_populates="scene", cascade="all, delete-orphan", order_by="Shot.shot_number")


class Shot(Base):
    __tablename__ = "shots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)

    shot_number = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=False, default=5.0)

    shot_type = Column(String(100), nullable=True)       # Wide, Medium, Close-up, Extreme Close-up
    camera_angle = Column(String(100), nullable=True)    # Eye-level, Low angle, High angle, Dutch
    camera_movement = Column(String(100), nullable=True) # Static, Pan, Dolly, Tracking, Crane
    lens = Column(String(100), nullable=True)            # 35mm, 50mm, 85mm Anamorphic
    framing = Column(String(255), nullable=True)

    characters = Column(JSON, default=list)
    location_id = Column(String(36), nullable=True)
    action = Column(Text, nullable=True)
    emotion = Column(String(255), nullable=True)
    dialogue = Column(Text, nullable=True)
    environment = Column(Text, nullable=True)
    lighting = Column(Text, nullable=True)
    sound = Column(Text, nullable=True)
    visual_effects = Column(Text, nullable=True)

    # Compiled deterministic prompts
    image_prompt = Column(Text, nullable=True)
    video_prompt = Column(Text, nullable=True)

    # Reference asset links
    reference_asset_ids = Column(JSON, default=list)
    previous_shot_id = Column(String(36), nullable=True)
    continuity_constraints = Column(JSON, default=list)

    status = Column(String(50), nullable=False, default=ShotStatus.DRAFT.value)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    scene = relationship("Scene", back_populates="shots")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    target_type = Column(String(50), nullable=False)  # "shot_image", "shot_video", "character_ref", etc.
    target_id = Column(String(36), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    parameters = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # AssetType enum
    file_path = Column(String(1024), nullable=False)
    mime_type = Column(String(100), nullable=False)

    provider = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    prompt = Column(Text, nullable=True)
    seed = Column(Integer, nullable=True)
    parameters = Column(JSON, default=dict)

    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)

    parent_asset_id = Column(String(36), nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    rejection_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    project = relationship("Project", back_populates="assets")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # JobType enum
    provider = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict)

    status = Column(String(50), nullable=False, default=JobStatus.QUEUED.value)
    progress = Column(Float, nullable=False, default=0.0)
    result_asset_ids = Column(JSON, default=list)
    error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="jobs")
