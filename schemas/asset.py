from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from ..core.enums import AssetType

class AssetCreate(BaseModel):
    project_id: str
    type: AssetType
    file_path: str
    mime_type: str
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    seed: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    duration: Optional[float] = None
    parent_asset_id: Optional[str] = None

class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    type: AssetType
    file_path: str
    mime_type: str
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    seed: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    duration: Optional[float] = None
    parent_asset_id: Optional[str] = None
    is_approved: bool
    rejection_reason: Optional[str] = None
    created_at: datetime
