"""Pydantic schemas for Shortlist API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShortlistCandidateResponse(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class ShortlistCreate(BaseModel):
    job_id: int = Field(..., description="Internal integer ID of the job")
    candidate_id: int = Field(..., description="Internal integer ID of the candidate user")
    notes: str | None = Field(default=None, max_length=2000, description="Optional recruiter notes")
    match_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional snapshot match score between 0.0 and 1.0",
    )


class ShortlistUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=2000, description="Optional recruiter notes")


class ShortlistResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    notes: str | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime
    candidate: ShortlistCandidateResponse | None = None

    model_config = ConfigDict(from_attributes=True)
