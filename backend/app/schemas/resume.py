from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: int
    storage_reference: str
    original_filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
