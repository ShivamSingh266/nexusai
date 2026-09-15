from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class RoadmapCycleError(ValueError):
    """Raised when prerequisite relationships contain a cycle."""


@dataclass(frozen=True)
class RoadmapStep:
    skill_id: str
    priority: float
    prerequisites: tuple[str, ...]


def validate_prerequisite_dag(
    prerequisites: Mapping[str, Sequence[str]],
) -> None:
    """
    Validate that prerequisite relationships form a DAG.

    A cycle anywhere in the supplied prerequisite graph is rejected.
    """
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            raise RoadmapCycleError(
                f"Prerequisite cycle detected involving {skill_id}"
            )

        if skill_id in visited:
            return

        visiting.add(skill_id)

        for prerequisite in sorted(prerequisites.get(skill_id, ())):
            visit(prerequisite)

        visiting.remove(skill_id)
        visited.add(skill_id)

    all_skills = set(prerequisites)

    for required in prerequisites.values():
        all_skills.update(required)

    for skill_id in sorted(all_skills):
        visit(skill_id)


def sequence_roadmap(
    gaps: Sequence[RoadmapStep],
) -> list[RoadmapStep]:
    """
    Return roadmap steps in prerequisite-first order.

    Prerequisites that are themselves roadmap steps must be completed before
    their dependent step. Prerequisites outside the roadmap are treated as
    external/already-satisfied dependencies.

    Among otherwise independent skills:
    1. Higher priority wins.
    2. Skill ID ascending breaks ties.
    """
    prerequisites = {
        step.skill_id: step.prerequisites
        for step in gaps
    }

    validate_prerequisite_dag(prerequisites)

    steps = {step.skill_id: step for step in gaps}
    roadmap_skill_ids = set(steps)

    remaining = set(steps)
    completed: set[str] = set()
    ordered: list[RoadmapStep] = []

    while remaining:
        ready = [
            skill_id
            for skill_id in remaining
            if all(
                prerequisite not in roadmap_skill_ids
                or prerequisite in completed
                for prerequisite in prerequisites.get(skill_id, ())
            )
        ]

        if not ready:
            raise RoadmapCycleError(
                "Unable to sequence roadmap because prerequisite dependencies "
                "cannot be satisfied."
            )

        ready.sort(
            key=lambda skill_id: (
                -steps[skill_id].priority,
                skill_id,
            )
        )

        selected = ready[0]
        ordered.append(steps[selected])
        completed.add(selected)
        remaining.remove(selected)

    return ordered