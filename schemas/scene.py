from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class SceneBase(BaseModel):
    scene_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = None
    purpose: Optional[str] = None
    duration_seconds: int = Field(default=45, ge=5, le=300)

    location_id: Optional[str] = None
    time_of_day: Optional[str] = None
    emotional_state: Optional[str] = None
    story_beat: Optional[str] = None
    dialogue: Optional[str] = None
    sound_design: Optional[str] = None
    visual_direction: Optional[str] = None
    continuity_notes: Optional[str] = None
    characters: List[str] = Field(default_factory=list)

class SceneCreate(SceneBase):
    project_id: str

class SceneRead(SceneBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
