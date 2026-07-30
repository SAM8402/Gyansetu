from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobCreate(BaseModel):
    file_name: str
    config: dict = {}


class JobResponse(BaseModel):
    id: str
    status: str
    current_stage: int
    file_name: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    tkp_url: Optional[str] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
