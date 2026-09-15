"""Canonical skill taxonomy search API.

Namespace:
  /api/v1/taxonomy/skills/search  — canonical taxonomy (read-only, public)
  /api/v1/skills/*                — ApplicantSkill personal CRUD (unchanged)

This router is PUBLIC — no authentication is required.  The taxonomy is a
shared read-only reference dataset.

Search priority when `q` is provided:
  1. Exact normalized_name match.
  2. Exact normalized_alias match (via SkillAlias JOIN).
  3. Substring fallback (ILIKE on canonical_name and normalized_name).

Results are deduplicated so that the same CanonicalSkill is not returned
more than once even if it matches via multiple aliases.  Ordering is
deterministic: exact matches first, then substring matches, both ordered
by skill_id ascending within their tier.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.canonical_skill import CanonicalSkill, SkillAlias
from app.schemas.taxonomy import CanonicalSkillSearchResult, TaxonomySearchResponse

router = APIRouter(
    prefix="/taxonomy",
    tags=["Taxonomy"],
)

_MAX_LIMIT = 100


# ---------------------------------------------------------------------------
# Normalisation helper — mirrors the normalisation applied at ingestion time.
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalise a query string the same way the taxonomy data is normalised.

    Steps (in order):
    1. Unicode NFKD decomposition.
    2. Strip surrounding whitespace.
    3. Lowercase.
    4. Collapse runs of internal whitespace to a single space.
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# GET /taxonomy/skills/search
# ---------------------------------------------------------------------------


@router.get(
    "/skills/search",
    response_model=TaxonomySearchResponse,
    summary="Search canonical skill taxonomy (public)",
)
def search_taxonomy_skills(
    q: str | None = Query(default=None, description="Search query"),
    category: str | None = Query(default=None, description="Filter by category"),
    is_active: bool = Query(default=True, description="Filter by active status"),
    limit: int = Query(default=20, ge=1, le=_MAX_LIMIT, description="Page size (max 100)"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
) -> TaxonomySearchResponse:
    """Search the canonical skill taxonomy.

    When ``q`` is omitted, all skills matching ``category`` and ``is_active``
    are returned (paginated).

    When ``q`` is provided, results are returned in priority order:
      1. Skills whose ``normalized_name`` exactly equals the normalised query.
      2. Skills linked via a ``SkillAlias`` whose ``normalized_alias`` exactly
         equals the normalised query.
      3. Skills whose ``canonical_name`` or ``normalized_name`` contains the
         raw query as a substring (ILIKE / case-insensitive LIKE).

    Duplicate canonical skills are suppressed: a skill matched by multiple
    aliases appears only once in the result list.
    """
    # Base filter applied to every query branch.
    def _base_filters(qry):
        qry = qry.filter(CanonicalSkill.is_active == is_active)
        if category:
            qry = qry.filter(CanonicalSkill.category == category)
        return qry

    if not q:
        # ------------------------------------------------------------------ #
        # No query — return all matching skills, paginated.                  #
        # ------------------------------------------------------------------ #
        base_q = _base_filters(db.query(CanonicalSkill))
        total = base_q.count()
        skills = (
            base_q
            .order_by(CanonicalSkill.skill_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return TaxonomySearchResponse(
            results=[_to_result(s) for s in skills],
            total=total,
            limit=limit,
            offset=offset,
        )

    # ---------------------------------------------------------------------- #
    # Query supplied — three-tier priority search.                            #
    # ---------------------------------------------------------------------- #
    normalized_q = _normalize(q)

    # Tier 1: exact normalized_name match.
    exact_name_q = _base_filters(
        db.query(CanonicalSkill).filter(
            CanonicalSkill.normalized_name == normalized_q
        )
    )
    exact_name_skills: list[CanonicalSkill] = exact_name_q.order_by(CanonicalSkill.skill_id).all()

    # Tier 2: exact normalized_alias match.
    exact_alias_q = _base_filters(
        db.query(CanonicalSkill).join(
            SkillAlias,
            SkillAlias.skill_id == CanonicalSkill.skill_id,
        ).filter(
            SkillAlias.normalized_alias == normalized_q
        )
    )
    exact_alias_skills: list[CanonicalSkill] = exact_alias_q.order_by(CanonicalSkill.skill_id).all()

    # Tier 3: substring / ILIKE fallback on canonical_name and normalized_name.
    ilike_pattern = f"%{q}%"
    substring_q = _base_filters(
        db.query(CanonicalSkill).filter(
            CanonicalSkill.canonical_name.ilike(ilike_pattern)
            | CanonicalSkill.normalized_name.ilike(ilike_pattern)
        )
    )
    substring_skills: list[CanonicalSkill] = substring_q.order_by(CanonicalSkill.skill_id).all()

    # Merge tiers, deduplicating while preserving priority order.
    seen: set[str] = set()
    ordered: list[CanonicalSkill] = []
    for skill in exact_name_skills + exact_alias_skills + substring_skills:
        if skill.skill_id not in seen:
            seen.add(skill.skill_id)
            ordered.append(skill)

    total = len(ordered)
    page = ordered[offset: offset + limit]

    return TaxonomySearchResponse(
        results=[_to_result(s) for s in page],
        total=total,
        limit=limit,
        offset=offset,
    )


def _to_result(skill: CanonicalSkill) -> CanonicalSkillSearchResult:
    return CanonicalSkillSearchResult(
        skill_id=skill.skill_id,
        canonical_name=skill.canonical_name,
        category=skill.category,
        is_active=skill.is_active,
    )
