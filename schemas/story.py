from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class StorySchema(BaseModel):
    """The strict schema for LLM-generated structured stories"""
    premise: str = Field(..., description="Core premise of the micro-drama")
    theme: str = Field(..., description="Central dramatic theme")
    tone: str = Field(..., description="Emotional and visual tone")
    synopsis: str = Field(..., description="Complete narrative synopsis (~10 min)")
    ending: str = Field(..., description="The climatic ending/resolution")
    story_rules: List[str] = Field(default_factory=list, description="World/narrative constraints and rules")
    acts: List[Dict[str, Any]] = Field(default_factory=list, description="3-Act structure breakdown")
    clues: List[str] = Field(default_factory=list, description="Narrative clues or motifs")
    continuity_rules: List[str] = Field(default_factory=list, description="Key continuity anchors across the film")

class StoryCreate(StorySchema):
    project_id: str

class StoryRead(StorySchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
