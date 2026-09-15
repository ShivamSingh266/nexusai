"""Pydantic schemas for the canonical skill taxonomy search API.

These schemas are intentionally minimal — the search endpoint returns
read-only data from the M4-owned taxonomy.  Write operations on the
taxonomy are not exposed via this API.
"""
from pydantic import BaseModel


class CanonicalSkillSearchResult(BaseModel):
    """Single result item returned by the taxonomy search endpoint."""

    skill_id: str
    canonical_name: str
    category: str
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class TaxonomySearchResponse(BaseModel):
    """Paginated response envelope for taxonomy skill searches."""

    results: list[CanonicalSkillSearchResult]
    total: int
    limit: int
    offset: int

    model_config = {
        "from_attributes": True,
    }
