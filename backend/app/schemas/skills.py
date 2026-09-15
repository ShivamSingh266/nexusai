from datetime import datetime

from pydantic import BaseModel, Field


class ApplicantSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    proficiency_level: str = Field(
        default="beginner",
        min_length=1,
        max_length=50,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
    )


class ApplicantSkillCreate(ApplicantSkillBase):
    pass


class ApplicantSkillUpdate(BaseModel):
    skill_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    proficiency_level: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
    )


class ApplicantSkillResponse(ApplicantSkillBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }