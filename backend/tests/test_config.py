from app.core.config import Settings


def test_member5_matching_weights_sum_to_one() -> None:
    settings = Settings(
        DATABASE_URL="sqlite://",
        JWT_SECRET_KEY="test-secret",
    )

    total = (
        settings.MATCH_SKILL_WEIGHT
        + settings.MATCH_SEMANTIC_WEIGHT
        + settings.MATCH_EXPERIENCE_WEIGHT
        + settings.MATCH_EDUCATION_WEIGHT
        + settings.MATCH_LOCATION_MODE_WEIGHT
    )

    assert total == 1.0


def test_member5_matching_weights_match_blueprint() -> None:
    settings = Settings(
        DATABASE_URL="sqlite://",
        JWT_SECRET_KEY="test-secret",
    )

    assert settings.MATCH_SKILL_WEIGHT == 0.60
    assert settings.MATCH_SEMANTIC_WEIGHT == 0.20
    assert settings.MATCH_EXPERIENCE_WEIGHT == 0.10
    assert settings.MATCH_EDUCATION_WEIGHT == 0.05
    assert settings.MATCH_LOCATION_MODE_WEIGHT == 0.05