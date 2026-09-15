import pytest

from app import models
from app.core import representations as reps
from app.core.gap import analyze_gap
from app.core.roadmap import generate_roadmap, RoadmapCycleError

from tests.conftest import CAND, ROLE, COURSE_ML, COURSE_DL


def test_prerequisite_ordering_respected(db):
    candidate = reps.candidate_profile(db, CAND)
    target = reps.role_target_profile(db, ROLE)
    gaps = analyze_gap(db, candidate, target)

    steps = generate_roadmap(db, gaps)
    course_order = [s.course_id for s in steps if s.course_id]

    assert course_order.index(COURSE_ML) < course_order.index(COURSE_DL)


def test_cycle_fails_safely(db):
    """Negative case: introduce a genuine cycle (ML Fundamentals now also
    requires Deep Learning, which already requires ML Fundamentals) and
    confirm the generator raises instead of hanging or silently dropping
    courses."""
    db.add(models.CoursePrerequisite(course_id=COURSE_ML, prerequisite_course_id=COURSE_DL))
    db.commit()

    candidate = reps.candidate_profile(db, CAND)
    target = reps.role_target_profile(db, ROLE)
    gaps = analyze_gap(db, candidate, target)

    with pytest.raises(RoadmapCycleError) as exc_info:
        generate_roadmap(db, gaps)

    assert COURSE_ML in exc_info.value.cycle_course_ids
    assert COURSE_DL in exc_info.value.cycle_course_ids
