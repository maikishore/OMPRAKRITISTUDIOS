from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from core.enums import ShotStatus

class ShotBase(BaseModel):
    shot_number: int = Field(..., ge=1)
    duration_seconds: float = Field(default=5.0, ge=1.0, le=20.0)

    shot_type: Optional[str] = "Medium Shot"
    camera_angle: Optional[str] = "Eye-level"
    camera_movement: Optional[str] = "Slow Dolly"
    lens: Optional[str] = "50mm"
    framing: Optional[str] = None

    characters: List[str] = Field(default_factory=list)
    location_id: Optional[str] = None
    action: Optional[str] = None
    emotion: Optional[str] = None
    dialogue: Optional[str] = None
    environment: Optional[str] = None
    lighting: Optional[str] = None
    sound: Optional[str] = None
    visual_effects: Optional[str] = None

    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None

    reference_asset_ids: List[str] = Field(default_factory=list)
    previous_shot_id: Optional[str] = None
    continuity_constraints: List[str] = Field(default_factory=list)

class ShotCreate(ShotBase):
    scene_id: str

class ShotRead(ShotBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scene_id: str
    status: ShotStatus
    created_at: datetime
    updated_at: datetime
