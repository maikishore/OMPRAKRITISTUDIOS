from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class VisualStyleSchema(BaseModel):
    cinematic_realism: Optional[str] = "Ultra-cinematic 35mm film look"
    camera_language: Optional[str] = "Intentional camera choreography with slow dolly and stable tracking"
    lens_preferences: Optional[str] = "Anamorphic primes (35mm, 50mm, 85mm)"
    lighting_language: Optional[str] = "Moody volumetric lighting with high natural contrast"
    color_progression: Optional[str] = "Progression from warm atmospheric hues to cold desaturated tension"
    contrast: Optional[str] = "Medium-high contrast with deep blacks"
    depth_of_field: Optional[str] = "Shallow depth of field with soft bokeh"
    film_grain: Optional[str] = "Subtle organic 35mm grain"
    production_design: Optional[str] = "Grounded realistic environments with textured surfaces"
    visual_motifs: List[str] = Field(default_factory=list)

class VisualStyleCreate(VisualStyleSchema):
    project_id: str

class VisualStyleRead(VisualStyleSchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
