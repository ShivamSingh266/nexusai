from datetime import date

from pydantic import BaseModel, Field


class ApplicantProfileBase(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    education: str | None = Field(default=None, max_length=255)
    experience_years: float | None = Field(default=None, ge=0)
    bio: str | None = None


class ApplicantProfileCreate(ApplicantProfileBase):
    pass


class ApplicantProfileUpdate(ApplicantProfileBase):
    pass


class ApplicantProfileResponse(ApplicantProfileBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True,
    }