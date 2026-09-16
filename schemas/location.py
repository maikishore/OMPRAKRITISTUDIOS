from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    architecture: Optional[str] = None
    materials: Optional[str] = None
    lighting: Optional[str] = None
    time_of_day: Optional[str] = None
    visual_identity: Optional[str] = None
    continuity_constraints: List[str] = Field(default_factory=list)
    master_reference_asset_id: Optional[str] = None

class LocationCreate(LocationBase):
    project_id: str

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    architecture: Optional[str] = None
    materials: Optional[str] = None
    lighting: Optional[str] = None
    time_of_day: Optional[str] = None
    visual_identity: Optional[str] = None
    continuity_constraints: Optional[List[str]] = None
    master_reference_asset_id: Optional[str] = None
    is_approved: Optional[bool] = None

class LocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
