"""Pydantic contracts for job-to-canonical-skill requirements."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class JobSkillCreate(BaseModel):
    skill_id: str = Field(pattern=r"^SKILL_[0-9]{4}$")
    taxonomy_version: str = Field(min_length=1, max_length=32)
    role_importance: float = Field(default=1.0, ge=0, le=1)
    is_mandatory: bool = True


class JobSkillBulkCreate(BaseModel):
    skills: list[JobSkillCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_skills(self) -> "JobSkillBulkCreate":
        skill_ids = [skill.skill_id for skill in self.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Bulk job skills must not contain duplicate skill IDs")
        return self


class JobSkillUpdate(BaseModel):
    role_importance: float | None = Field(default=None, ge=0, le=1)
    is_mandatory: bool | None = None


class JobSkillResponse(BaseModel):
    id: int
    job_id: int
    skill_id: str
    taxonomy_version: str
    role_importance: float
    is_mandatory: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }