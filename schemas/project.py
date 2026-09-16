from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from ..core.enums import ProjectStatus

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    logline: Optional[str] = None
    genre: str = Field(default="Drama", max_length=100)
    target_duration_seconds: int = Field(default=600, ge=60, le=1800)  # 1 to 30 mins
    language: str = Field(default="English", max_length=50)
    aspect_ratio: str = Field(default="16:9", max_length=20)
    image_model: str = Field(default="flux-1-schnell", max_length=100)
    video_model: str = Field(default="ltx-2.3", max_length=100)
    default_video_duration: float = Field(default=5.0, ge=1.0, le=20.0)
    default_resolution: str = Field(default="1080p", max_length=50)
    default_fps: int = Field(default=24, ge=12, le=60)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    logline: Optional[str] = None
    genre: Optional[str] = None
    target_duration_seconds: Optional[int] = None
    language: Optional[str] = None
    aspect_ratio: Optional[str] = None
    status: Optional[ProjectStatus] = None
    image_model: Optional[str] = None
    video_model: Optional[str] = None
    default_video_duration: Optional[float] = None
    default_resolution: Optional[str] = None
    default_fps: Optional[int] = None

class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
