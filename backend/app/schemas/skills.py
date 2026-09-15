from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class ApplicantSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    skill_id: str | None = Field(
        default=None,
        pattern=r"^SKILL_[0-9]{4}$",
    )
    taxonomy_version: str | None = Field(default=None, max_length=32)
    proficiency_level: str = Field(
        default="beginner",
        min_length=1,
        max_length=50,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_taxonomy_reference(self) -> "ApplicantSkillBase":
        if (self.skill_id is None) != (self.taxonomy_version is None):
            raise ValueError(
                "skill_id and taxonomy_version must be provided together"
            )
        return self


class ApplicantSkillCreate(ApplicantSkillBase):
    pass


class ApplicantSkillUpdate(BaseModel):
    skill_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    skill_id: str | None = Field(
        default=None,
        pattern=r"^SKILL_[0-9]{4}$",
    )
    taxonomy_version: str | None = Field(default=None, max_length=32)
    proficiency_level: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    years_experience: int | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_taxonomy_reference(self) -> "ApplicantSkillUpdate":
        if (self.skill_id is None) != (self.taxonomy_version is None):
            raise ValueError(
                "skill_id and taxonomy_version must be provided together"
            )
        return self


class ApplicantSkillResponse(ApplicantSkillBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }