import pytest

from app.core.semantic import cosine_similarity, skill_text_similarity, tokenize


def test_tokenize_is_lowercase_and_deterministic() -> None:
    assert tokenize("Python, SQL & AWS!") == ["python", "sql", "aws"]


def test_identical_text_has_similarity_one() -> None:
    assert cosine_similarity("Python SQL AWS", "Python SQL AWS") == pytest.approx(1.0)


def test_related_text_has_positive_similarity() -> None:
    score = cosine_similarity(
        "Python SQL database administration",
        "Python SQL data engineering",
    )

    assert 0.0 < score < 1.0


def test_unrelated_text_has_zero_similarity() -> None:
    assert cosine_similarity(
        "Python SQL database",
        "welding mechanical fabrication",
    ) == pytest.approx(0.0)


def test_empty_text_returns_zero() -> None:
    assert cosine_similarity("", "Python SQL") == pytest.approx(0.0)


def test_public_skill_similarity_contract_matches_baseline() -> None:
    score = skill_text_similarity("Python SQL", "Python SQL")

    assert score == pytest.approx(1.0)


def test_similarity_is_symmetric() -> None:
    left = "Python SQL data engineering"
    right = "Python database engineering"

    assert cosine_similarity(left, right) == pytest.approx(
        cosine_similarity(right, left)
    )