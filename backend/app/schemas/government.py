from datetime import datetime

from pydantic import BaseModel


class GovernmentResponse(BaseModel):
    data: list[dict]
    meta: dict
    model_version: str | None
    source_version: str
    generated_at: datetime
    warnings: list[str]
