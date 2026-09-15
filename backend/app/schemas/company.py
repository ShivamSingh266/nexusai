from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CompanyBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    industry: str | None = Field(default=None, max_length=150)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    company_size: str | None = Field(default=None, max_length=50)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    """All fields are optional for PATCH semantics."""

    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    industry: str | None = Field(default=None, max_length=150)
    website: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    company_size: str | None = Field(default=None, max_length=50)


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
