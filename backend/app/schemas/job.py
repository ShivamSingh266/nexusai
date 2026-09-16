from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# Valid vocabulary constants — mirrored from the model for schema validation.
# Using Literal rather than Enum keeps JSON serialisation as plain strings.
JobStatusLiteral = Literal["draft", "published", "closed"]
EmploymentTypeLiteral = Literal[
    "full_time", "part_time", "contract", "internship", "freelance"
]
WorkModeLiteral = Literal["onsite", "remote", "hybrid"]


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    employment_type: EmploymentTypeLiteral | None = None
    work_mode: WorkModeLiteral | None = None
    experience_min: float | None = Field(default=None, ge=0)
    experience_max: float | None = Field(default=None, ge=0)
    education_requirement: str | None = Field(default=None, max_length=255)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_experience_range(self) -> "JobBase":
        if (
            self.experience_min is not None
            and self.experience_max is not None
            and self.experience_min > self.experience_max
        ):
            raise ValueError("experience_min must be <= experience_max")
        return self

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobBase":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must be <= salary_max")
        return self


class JobCreate(JobBase):
    """Request body for POST /jobs. Status defaults to 'draft'."""
    status: JobStatusLiteral = "draft"


class JobUpdate(BaseModel):
    """All fields optional for PATCH semantics."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, max_length=255)
    employment_type: EmploymentTypeLiteral | None = None
    work_mode: WorkModeLiteral | None = None
    experience_min: float | None = Field(default=None, ge=0)
    experience_max: float | None = Field(default=None, ge=0)
    education_requirement: str | None = Field(default=None, max_length=255)
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    status: JobStatusLiteral | None = None

    @model_validator(mode="after")
    def validate_experience_range(self) -> "JobUpdate":
        if (
            self.experience_min is not None
            and self.experience_max is not None
            and self.experience_min > self.experience_max
        ):
            raise ValueError("experience_min must be <= experience_max")
        return self

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobUpdate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must be <= salary_max")
        return self


class JobResponse(JobBase):
    id: int
    company_id: int
    source_job_id: str | None = None
    source: str | None = None
    sector: str | None = None
    status: JobStatusLiteral
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class JobListResponse(BaseModel):
    """Paginated wrapper for job listings."""
    data: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {
        "from_attributes": True,
    }
