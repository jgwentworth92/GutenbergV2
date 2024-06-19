from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Dict, Any


class ResourceModel(BaseModel):
    id: UUID4
    job_id: UUID4
    resource_type: str
    resource_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
