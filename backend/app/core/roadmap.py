"""
Task 06 — F5 roadmap generation.

Builds a course sequence for the candidate's gap skills, respecting
course_prerequisites edges via Kahn's algorithm (topological sort).
Validates the DAG and fails SAFELY on a cycle: raises RoadmapCycleError
with the offending course ids rather than silently truncating or looping,
so the API can return a clean 422 instead of corrupting a roadmap.
"""
from collections import defaultdict, deque
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app import models
from app.core.gap import SkillGapResult


class RoadmapCycleError(Exception):
    def __init__(self, cycle_course_ids: list[str]):
        self.cycle_course_ids = cycle_course_ids
        super().__init__(f"Prerequisite cycle detected among courses: {cycle_course_ids}")


@dataclass
class RoadmapStepPlan:
    skill_id: str
    course_id: str | None
    project: str | None
    step_order: int
    duration: str | None


def _best_course_for_skill(db: Session, skill_id: str) -> models.Course | None:
    row = (
        db.query(models.Course)
        .join(models.CourseSkill, models.CourseSkill.course_id == models.Course.id)
        .filter(models.CourseSkill.skill_id == skill_id)
        .order_by(models.CourseSkill.coverage_level.desc())
        .first()
    )
    return row


def _topo_sort_courses(db: Session, course_ids: set[str]) -> list[str]:
    """Kahn's algorithm restricted to the subgraph of `course_ids`.
    Prerequisite edges pointing outside this set are ignored (already
    assumed satisfied / out of scope for this roadmap)."""
    if not course_ids:
        return []

    edges = (
        db.query(models.CoursePrerequisite)
        .filter(models.CoursePrerequisite.course_id.in_(course_ids))
        .all()
    )

    indegree = {cid: 0 for cid in course_ids}
    adj = defaultdict(list)  # prereq -> [dependents]
    for e in edges:
        if e.prerequisite_course_id in course_ids and e.course_id in course_ids:
            adj[e.prerequisite_course_id].append(e.course_id)
            indegree[e.course_id] += 1

    queue = deque(sorted([cid for cid, d in indegree.items() if d == 0]))
    ordered = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for dependent in sorted(adj[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(course_ids):
        remaining = course_ids - set(ordered)
        raise RoadmapCycleError(sorted(remaining))

    return ordered


def generate_roadmap(
    db: Session,
    gap_results: list[SkillGapResult],
) -> list[RoadmapStepPlan]:
    """Highest-priority gaps get courses (or a fallback "project" step if no
    course covers the skill), the whole set is then topologically sorted so
    prerequisites always precede what depends on them."""
    skill_to_course: dict[str, models.Course] = {}
    fallback_skills: list[str] = []

    for gap in gap_results:
        course = _best_course_for_skill(db, gap.skill_id)
        if course:
            skill_to_course[gap.skill_id] = course
        else:
            fallback_skills.append(gap.skill_id)

    course_ids = {c.id for c in skill_to_course.values()}
    ordered_course_ids = _topo_sort_courses(db, course_ids)

    # Map course_id back to whichever skill(s) it satisfies, preserving the
    # gap-priority order among skills that share a course.
    course_to_skills: dict[str, list[str]] = defaultdict(list)
    for skill_id, course in skill_to_course.items():
        course_to_skills[course.id].append(skill_id)

    steps: list[RoadmapStepPlan] = []
    order = 1
    for course_id in ordered_course_ids:
        course = next(c for c in skill_to_course.values() if c.id == course_id)
        for skill_id in course_to_skills[course_id]:
            steps.append(RoadmapStepPlan(
                skill_id=skill_id, course_id=course_id, project=None,
                step_order=order, duration=course.duration,
            ))
            order += 1

    # Skills with no matching course become project-based steps, appended
    # last (they have no prerequisite data to respect).
    for skill_id in fallback_skills:
        steps.append(RoadmapStepPlan(
            skill_id=skill_id, course_id=None,
            project=f"Portfolio project demonstrating skill {skill_id}",
            step_order=order, duration=None,
        ))
        order += 1

    return steps


def persist_roadmap(db: Session, candidate_id: str, target_role_id: str,
                     steps: list[RoadmapStepPlan], model_version: str) -> models.Roadmap:
    roadmap = models.Roadmap(candidate_id=candidate_id, target_role_id=target_role_id,
                              model_version=model_version)
    db.add(roadmap)
    db.flush()  # get roadmap.id without committing yet

    for s in steps:
        db.add(models.RoadmapStep(
            roadmap_id=roadmap.id, skill_id=s.skill_id, course_id=s.course_id,
            project=s.project, step_order=s.step_order, duration=s.duration,
        ))
    db.commit()
    db.refresh(roadmap)
    return roadmap
