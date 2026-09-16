"""Typed metadata contracts exposed to frontend clients."""

from datetime import datetime

from pydantic import BaseModel


class MatchingMetadata(BaseModel):
    implemented: bool
    version: str | None
    weights: dict[str, float] | None


class VersionMetadataData(BaseModel):
    backend_version: str
    taxonomy_version: str
    gap_scoring_version: str
    matching: MatchingMetadata


class VersionMetadataResponse(BaseModel):
    data: VersionMetadataData
    meta: dict[str, str]
    model_version: str | None
    source_version: str
    generated_at: datetime
    warnings: list[str]