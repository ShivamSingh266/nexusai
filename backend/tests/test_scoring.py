import pytest

from app.core.scoring import ScoreComponents, calculate_weighted_score


def test_full_weighted_score() -> None:
    score = calculate_weighted_score(
        ScoreComponents(
            skill=1.0,
            semantic=1.0,
            experience=1.0,
            education=1.0,
            location_mode=1.0,
        )
    )

    assert score == pytest.approx(1.0)


def test_weighted_score_uses_frozen_weights() -> None:
    score = calculate_weighted_score(
        ScoreComponents(
            skill=1.0,
            semantic=0.0,
            experience=0.0,
            education=0.0,
            location_mode=0.0,
        )
    )

    assert score == pytest.approx(0.60)


def test_missing_optional_components_are_renormalized() -> None:
    score = calculate_weighted_score(
        ScoreComponents(
            skill=1.0,
            semantic=None,
            experience=None,
            education=None,
            location_mode=None,
        )
    )

    # Only skill is available, so it becomes 100% of the final score.
    assert score == pytest.approx(1.0)


def test_partial_components_are_renormalized() -> None:
    score = calculate_weighted_score(
        ScoreComponents(
            skill=1.0,
            semantic=None,
            experience=0.0,
            education=None,
            location_mode=None,
        )
    )

    # Available weights are 0.60 + 0.10 = 0.70.
    # Final = (1.0*0.60 + 0.0*0.10) / 0.70
    assert score == pytest.approx(0.60 / 0.70)


def test_score_outside_range_raises() -> None:
    with pytest.raises(ValueError):
        calculate_weighted_score(
            ScoreComponents(
                skill=1.2,
            )
        )


def test_all_missing_components_raise() -> None:
    with pytest.raises(ValueError):
        calculate_weighted_score(ScoreComponents())