from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from ..core.enums import JobStatus, JobType

class JobCreate(BaseModel):
    project_id: str
    type: JobType
    provider: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    type: JobType
    provider: str
    payload: Dict[str, Any]
    status: JobStatus
    progress: float
    result_asset_ids: List[str]
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
