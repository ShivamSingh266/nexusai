"""Tests for the canonical skill taxonomy search API.

Coverage:
  1.  GET endpoint exists (200 response from /api/v1/taxonomy/skills/search).
  2.  No q: returns active canonical skills.
  3.  category filtering.
  4.  is_active filtering.
  5.  limit parameter.
  6.  offset parameter.
  7.  Exact normalized_name search (tier 1).
  8.  Exact alias search (tier 2).
  9.  Alias normalisation: case differences / extra whitespace still match.
  10. Ambiguous alias: one normalized_alias -> multiple skills returns all.
  11. Substring search (tier 3 fallback).
  12. No-match query returns empty results.
  13. limit > 100 is rejected with 422.
  14. Negative offset is rejected with 422.
  15. Response shape is correct.
  16. /api/v1/skills namespace remains unaffected.

Architecture:
  - SQLite in-memory, StaticPool (same pattern as other test modules).
  - Base.metadata.create_all() creates all tables including canonical_skills
    and skill_aliases.
  - module-scoped autouse fixture seeds test data and overrides get_db.
  - CheckConstraint (skill_id ~ '^SKILL_[0-9]{4}$') uses PostgreSQL regex
    syntax; SQLite ignores it, so the constraint is not tested here.
    The constraint IS enforced on the live PostgreSQL DB.

Notes:
  - The normalisation function used in fixtures mirrors app/api/taxonomy.py.
  - Tests do NOT import normalisation logic from the API module to keep
    tests independent of implementation details.
"""
import re
import unicodedata

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api.deps import get_db
from app.models.canonical_skill import CanonicalSkill, SkillAlias

# ---------------------------------------------------------------------------
# Isolated test database
# ---------------------------------------------------------------------------

_TAX_TEST_DB_URL = "sqlite://"

_tax_engine = create_engine(
    _TAX_TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TaxTestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_tax_engine,
)


def _tax_override_get_db():
    db = _TaxTestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _norm(text: str) -> str:
    """Local normaliser — mirrors app/api/taxonomy._normalize."""
    text = unicodedata.normalize("NFKD", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Module-scoped seed fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def setup_taxonomy_database():
    """Create schema, seed representative test data, apply get_db override."""
    Base.metadata.create_all(bind=_tax_engine)

    db: Session = _TaxTestingSessionLocal()
    try:
        # ------------------------------------------------------------------ #
        # Canonical skills                                                     #
        # ------------------------------------------------------------------ #
        # skill_id values use the SKILL_XXXX format (SQLite won't enforce the
        # CHECK constraint but the values conform to the spec).
        skills = [
            CanonicalSkill(
                skill_id="SKILL_0001",
                canonical_name="Python",
                normalized_name="python",
                category="IT/Software - Programming",
                source="ESCO",
                taxonomy_version="v1.2.1",
                is_active=True,
            ),
            CanonicalSkill(
                skill_id="SKILL_0002",
                canonical_name="Machine Learning",
                normalized_name="machine learning",
                category="IT/Software - AI",
                source="ESCO",
                taxonomy_version="v1.2.1",
                is_active=True,
            ),
            CanonicalSkill(
                skill_id="SKILL_0003",
                canonical_name="Project Management",
                normalized_name="project management",
                category="Management",
                source="ESCO",
                taxonomy_version="v1.2.1",
                is_active=True,
            ),
            CanonicalSkill(
                skill_id="SKILL_0004",
                canonical_name="Deep Learning",
                normalized_name="deep learning",
                category="IT/Software - AI",
                source="ESCO",
                taxonomy_version="v1.2.1",
                is_active=False,  # inactive
            ),
            CanonicalSkill(
                skill_id="SKILL_0005",
                canonical_name="Data Analysis",
                normalized_name="data analysis",
                category="IT/Software - Data",
                source="ESCO",
                taxonomy_version="v1.2.1",
                is_active=True,
            ),
        ]
        db.add_all(skills)
        db.flush()

        # ------------------------------------------------------------------ #
        # Skill aliases                                                        #
        # ------------------------------------------------------------------ #
        # alias "ml" maps to both SKILL_0002 (Machine Learning) and
        # SKILL_0004 (Deep Learning) to test the ambiguous alias scenario.
        aliases = [
            SkillAlias(
                alias="Python programming",
                normalized_alias=_norm("Python programming"),
                skill_id="SKILL_0001",
                confidence=1.0,
            ),
            SkillAlias(
                alias="py",
                normalized_alias=_norm("py"),
                skill_id="SKILL_0001",
                confidence=0.90,
            ),
            SkillAlias(
                alias="ML",
                normalized_alias=_norm("ML"),
                skill_id="SKILL_0002",
                confidence=0.95,
            ),
            # Same normalised alias "ml" points to SKILL_0004 as well.
            SkillAlias(
                alias="ML",
                normalized_alias=_norm("ML"),
                skill_id="SKILL_0004",
                confidence=0.85,
            ),
            SkillAlias(
                alias="  Project   Mgmt  ",
                normalized_alias=_norm("  Project   Mgmt  "),
                skill_id="SKILL_0003",
                confidence=0.90,
            ),
            SkillAlias(
                alias="data analytics",
                normalized_alias=_norm("data analytics"),
                skill_id="SKILL_0005",
                confidence=0.90,
            ),
        ]
        db.add_all(aliases)
        db.commit()

    finally:
        db.close()

    _previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _tax_override_get_db

    yield

    app.dependency_overrides[get_db] = _previous
    Base.metadata.drop_all(bind=_tax_engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Endpoint exists
# ---------------------------------------------------------------------------


class TestEndpointExists:
    def test_endpoint_returns_200(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 2. No q: returns active skills
# ---------------------------------------------------------------------------


class TestNoQuery:
    def test_returns_active_skills_by_default(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        assert r.status_code == 200
        data = r.json()
        # 4 active skills seeded (SKILL_0004 is inactive)
        skill_ids = [s["skill_id"] for s in data["results"]]
        assert "SKILL_0004" not in skill_ids
        assert data["total"] == 4

    def test_all_active_skills_returned_without_limit_constraint(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        data = r.json()
        assert len(data["results"]) == 4


# ---------------------------------------------------------------------------
# 3. Category filtering
# ---------------------------------------------------------------------------


class TestCategoryFilter:
    def test_filter_by_category(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"category": "IT/Software - AI"},
        )
        data = r.json()
        # Only SKILL_0002 (Machine Learning) is active in this category.
        # SKILL_0004 (Deep Learning, same category) is inactive.
        assert data["total"] == 1
        assert data["results"][0]["skill_id"] == "SKILL_0002"

    def test_category_no_match_returns_empty(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"category": "NonExistentCategory"},
        )
        data = r.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_management_category(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"category": "Management"},
        )
        data = r.json()
        assert data["total"] == 1
        assert data["results"][0]["skill_id"] == "SKILL_0003"


# ---------------------------------------------------------------------------
# 4. is_active filtering
# ---------------------------------------------------------------------------


class TestIsActiveFilter:
    def test_is_active_false_returns_inactive_only(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"is_active": "false"},
        )
        data = r.json()
        assert data["total"] == 1
        assert data["results"][0]["skill_id"] == "SKILL_0004"

    def test_is_active_true_default(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"is_active": "true"},
        )
        data = r.json()
        skill_ids = [s["skill_id"] for s in data["results"]]
        assert "SKILL_0004" not in skill_ids


# ---------------------------------------------------------------------------
# 5. Limit
# ---------------------------------------------------------------------------


class TestLimit:
    def test_limit_1(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"limit": 1})
        data = r.json()
        assert len(data["results"]) == 1
        assert data["total"] == 4  # total unchanged
        assert data["limit"] == 1

    def test_limit_2(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"limit": 2})
        data = r.json()
        assert len(data["results"]) == 2

    def test_limit_100_accepted(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"limit": 100})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 6. Offset
# ---------------------------------------------------------------------------


class TestOffset:
    def test_offset_skips_first_n(self, client):
        r_full = client.get("/api/v1/taxonomy/skills/search")
        full_ids = [s["skill_id"] for s in r_full.json()["results"]]

        r_offset = client.get(
            "/api/v1/taxonomy/skills/search", params={"offset": 2}
        )
        offset_ids = [s["skill_id"] for s in r_offset.json()["results"]]

        assert offset_ids == full_ids[2:]

    def test_offset_beyond_total_returns_empty(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"offset": 100}
        )
        data = r.json()
        assert data["results"] == []
        assert data["total"] == 4
        assert data["offset"] == 100

    def test_offset_in_response(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"offset": 1})
        assert r.json()["offset"] == 1


# ---------------------------------------------------------------------------
# 7. Exact normalized_name search (tier 1)
# ---------------------------------------------------------------------------


class TestExactNormalizedNameSearch:
    def test_exact_normalized_name_match(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"q": "python"}
        )
        data = r.json()
        assert data["total"] >= 1
        ids = [s["skill_id"] for s in data["results"]]
        assert "SKILL_0001" in ids

    def test_exact_normalized_name_case_insensitive_query(self, client):
        """The query is normalised before comparison so case doesn't matter."""
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"q": "PYTHON"}
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0001" in ids

    def test_exact_normalized_name_machine_learning(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "machine learning"},
        )
        data = r.json()
        ids = [s["skill_id"] for s in data["results"]]
        assert "SKILL_0002" in ids


# ---------------------------------------------------------------------------
# 8. Exact alias search (tier 2)
# ---------------------------------------------------------------------------


class TestExactAliasSearch:
    def test_alias_py_returns_python(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"q": "py"})
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0001" in ids

    def test_alias_python_programming(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "Python programming"},
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0001" in ids

    def test_alias_data_analytics_returns_data_analysis(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "data analytics"},
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0005" in ids


# ---------------------------------------------------------------------------
# 9. Alias normalisation (case + whitespace)
# ---------------------------------------------------------------------------


class TestAliasNormalisation:
    def test_uppercase_alias_query_matches(self, client):
        """Query 'ML' normalises to 'ml', matching the stored normalized_alias."""
        r = client.get("/api/v1/taxonomy/skills/search", params={"q": "ML"})
        assert r.status_code == 200
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0002" in ids

    def test_lowercase_alias_query_matches(self, client):
        r = client.get("/api/v1/taxonomy/skills/search", params={"q": "ml"})
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0002" in ids

    def test_extra_whitespace_in_alias_query(self, client):
        """'  Project   Mgmt  ' is stored normalised; querying 'project mgmt' matches."""
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"q": "project mgmt"}
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0003" in ids

    def test_leading_trailing_whitespace_in_query_normalised(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "  python  "},
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0001" in ids


# ---------------------------------------------------------------------------
# 10. Ambiguous alias: one normalized_alias -> multiple skills
# ---------------------------------------------------------------------------


class TestAmbiguousAlias:
    def test_ambiguous_alias_returns_all_matching_skills(self, client):
        """'ML' alias points to both SKILL_0002 and SKILL_0004.
        Both should appear when is_active is not filtered to True-only."""
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "ML", "is_active": "false"},
        )
        # With is_active=false we only see inactive skills (SKILL_0004).
        ids_inactive = [s["skill_id"] for s in r.json()["results"]]

        r2 = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "ML", "is_active": "true"},
        )
        ids_active = [s["skill_id"] for s in r2.json()["results"]]

        # SKILL_0002 (active) returned when is_active=true
        assert "SKILL_0002" in ids_active
        # SKILL_0004 (inactive) returned when is_active=false
        assert "SKILL_0004" in ids_inactive

    def test_no_duplicate_results_for_ambiguous_alias(self, client):
        """A single canonical skill must not appear twice in results."""
        r = client.get("/api/v1/taxonomy/skills/search", params={"q": "ML"})
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert len(ids) == len(set(ids)), "Duplicate skill_ids in results"


# ---------------------------------------------------------------------------
# 11. Substring search (tier 3)
# ---------------------------------------------------------------------------


class TestSubstringSearch:
    def test_partial_name_matches_via_ilike(self, client):
        """'earn' is a substring of 'machine learning' and 'deep learning'."""
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "earn"},
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        # At least machine learning should appear (is_active=True default)
        assert "SKILL_0002" in ids

    def test_partial_category_word_not_matched_via_field(self, client):
        """Substring search operates on canonical_name / normalized_name only."""
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"q": "ython"}
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        # 'ython' is a substring of 'python'
        assert "SKILL_0001" in ids

    def test_case_insensitive_substring(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"q": "PROJECT"}
        )
        ids = [s["skill_id"] for s in r.json()["results"]]
        assert "SKILL_0003" in ids


# ---------------------------------------------------------------------------
# 12. No-match query
# ---------------------------------------------------------------------------


class TestNoMatch:
    def test_nonexistent_query_returns_empty(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"q": "zzz_no_such_skill_zzz"},
        )
        data = r.json()
        assert r.status_code == 200
        assert data["total"] == 0
        assert data["results"] == []


# ---------------------------------------------------------------------------
# 13. Invalid limit > 100
# ---------------------------------------------------------------------------


class TestInvalidLimit:
    def test_limit_over_100_returns_422(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"limit": 101}
        )
        assert r.status_code == 422

    def test_limit_0_returns_422(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"limit": 0}
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# 14. Negative offset
# ---------------------------------------------------------------------------


class TestNegativeOffset:
    def test_negative_offset_returns_422(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search", params={"offset": -1}
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# 15. Response shape
# ---------------------------------------------------------------------------


class TestResponseShape:
    def test_response_has_required_fields(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        data = r.json()
        assert "results" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_result_item_has_required_fields(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        data = r.json()
        assert len(data["results"]) > 0
        item = data["results"][0]
        assert "skill_id" in item
        assert "canonical_name" in item
        assert "category" in item
        assert "is_active" in item

    def test_limit_and_offset_echoed_in_response(self, client):
        r = client.get(
            "/api/v1/taxonomy/skills/search",
            params={"limit": 7, "offset": 2},
        )
        data = r.json()
        assert data["limit"] == 7
        assert data["offset"] == 2

    def test_is_active_field_is_bool(self, client):
        r = client.get("/api/v1/taxonomy/skills/search")
        item = r.json()["results"][0]
        assert isinstance(item["is_active"], bool)


# ---------------------------------------------------------------------------
# 16. /api/v1/skills namespace unaffected
# ---------------------------------------------------------------------------


class TestSkillsNamespaceIsolation:
    def test_applicant_skills_endpoint_still_requires_auth(self, client):
        """GET /api/v1/skills without a token must return 403 (not 404 or 200)."""
        r = client.get("/api/v1/skills")
        assert r.status_code == 403

    def test_taxonomy_and_applicant_paths_are_different(self, client):
        r_taxonomy = client.get("/api/v1/taxonomy/skills/search")
        assert r_taxonomy.status_code == 200

        r_skills = client.get("/api/v1/skills")
        assert r_skills.status_code != 200  # auth required
