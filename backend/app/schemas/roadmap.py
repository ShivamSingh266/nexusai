from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, model_validator


class RoadmapStatus(str, Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class RoadmapItemStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class RoadmapItemCreate(BaseModel):
    skill_id: str = Field(pattern=r"^SKILL_[0-9]{4}$")
    taxonomy_version: str = Field(min_length=1, max_length=32)
    position: int = Field(ge=0)
    status: RoadmapItemStatus = RoadmapItemStatus.pending
    course_id: str | None = Field(default=None, min_length=1, max_length=64)
    resource_url: HttpUrl | None = None
    resource_title: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class RoadmapCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    taxonomy_version: str = Field(min_length=1, max_length=32)
    status: RoadmapStatus = RoadmapStatus.active
    items: list[RoadmapItemCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_item_versions_and_positions(self) -> "RoadmapCreate":
        if any(item.taxonomy_version != self.taxonomy_version for item in self.items):
            raise ValueError("Roadmap item taxonomy versions must match the roadmap")
        positions = [item.position for item in self.items]
        if len(positions) != len(set(positions)):
            raise ValueError("Roadmap item positions must be unique")
        return self


class RoadmapItemUpdate(BaseModel):
    position: int | None = Field(default=None, ge=0)
    status: RoadmapItemStatus | None = None
    course_id: str | None = Field(default=None, min_length=1, max_length=64)
    resource_url: HttpUrl | None = None
    resource_title: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class RoadmapItemResponse(BaseModel):
    id: int
    roadmap_id: int
    skill_id: str
    taxonomy_version: str
    position: int
    status: RoadmapItemStatus
    course_id: str | None
    resource_url: str | None
    resource_title: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: int
    applicant_id: int
    title: str
    taxonomy_version: str
    status: RoadmapStatus
    items: list[RoadmapItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
