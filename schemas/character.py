from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=50)
    age: Optional[str] = Field(None, max_length=50)

    appearance: Optional[str] = None
    hair: Optional[str] = None
    face: Optional[str] = None
    body: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None

    personality: Optional[str] = None
    behavior: Optional[str] = None
    voice_description: Optional[str] = None
    character_arc: Optional[str] = None
    continuity_constraints: List[str] = Field(default_factory=list)

    master_reference_asset_id: Optional[str] = None
    identity_prompt: Optional[str] = None
    negative_constraints: Optional[str] = None

class CharacterCreate(CharacterBase):
    project_id: str

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    appearance: Optional[str] = None
    hair: Optional[str] = None
    face: Optional[str] = None
    body: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    personality: Optional[str] = None
    behavior: Optional[str] = None
    voice_description: Optional[str] = None
    character_arc: Optional[str] = None
    continuity_constraints: Optional[List[str]] = None
    master_reference_asset_id: Optional[str] = None
    identity_prompt: Optional[str] = None
    negative_constraints: Optional[str] = None
    is_approved: Optional[bool] = None

class CharacterRead(CharacterBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
