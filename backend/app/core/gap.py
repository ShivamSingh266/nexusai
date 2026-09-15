"""Deterministic canonical-skill gap analysis."""

from dataclasses import dataclass
from pathlib import Path

from app.core.representations import SkillProfile

DEMAND_SOURCE_VERSION = "naukri:indian-job-market-dataset-2025"
SCORING_VERSION = "gap-v1"
NEUTRAL_TREND_MULTIPLIER = 1.0


@dataclass(frozen=True)
class DemandSignal:
    normalized_demand: float
    trend_multiplier: float | None


@dataclass(frozen=True)
class MatchedSkill:
    skill_id: str
    taxonomy_version: str
    coverage: float
    explanation: str


@dataclass(frozen=True)
class MissingSkill:
    skill_id: str
    taxonomy_version: str
    priority: float | None
    normalized_demand: float | None
    trend_multiplier: float
    gap_severity: float
    role_importance: float
    explanation: str


def _processed_demand_path() -> Path:
    return Path(__file__).resolve().parents[3] / "datasets" / "processed" / "skill_demand_history.csv"


def load_demand_signals(
    *,
    skill_ids: set[str],
    district_id: str | None,
    sector: str | None,
) -> dict[str, DemandSignal]:
    """Load the best applicable non-null demand signal from the CSV."""
    import csv

    signals: dict[str, DemandSignal] = {}
    with _processed_demand_path().open(newline="", encoding="utf-8") as demand_file:
        for row in csv.DictReader(demand_file):
            skill_id = row["skill_id"]
            if skill_id not in skill_ids:
                continue
            if district_id is not None and row["district_id"] != district_id:
                continue
            if sector is not None and row["sector"] != sector:
                continue
            if not row["demand_score"].strip():
                continue

            demand_score = float(row["demand_score"])
            recent_growth = row["recent_growth"].strip()
            trend = 1.0 + float(recent_growth) if recent_growth else None
            current = signals.get(skill_id)
            if current is None or demand_score > current.normalized_demand:
                signals[skill_id] = DemandSignal(demand_score, trend)
    return signals


def analyze_gap(
    *,
    candidate: SkillProfile,
    required_skills: tuple[tuple[str, float], ...],
    district_id: str | None,
    sector: str | None,
) -> tuple[list[MatchedSkill], list[MissingSkill], list[str]]:
    """Compare canonical candidate skills with target skills."""
    candidate_ids = {skill.skill_id for skill in candidate.skills}
    demand = load_demand_signals(
        skill_ids={skill_id for skill_id, _ in required_skills},
        district_id=district_id,
        sector=sector,
    )
    matched: list[MatchedSkill] = []
    missing: list[MissingSkill] = []
    warnings: list[str] = []
    fallback_used = False
    unavailable_demand = False

    for skill_id, role_importance in required_skills:
        if skill_id in candidate_ids:
            matched.append(
                MatchedSkill(
                    skill_id=skill_id,
                    taxonomy_version=candidate.taxonomy_version,
                    coverage=1.0,
                    explanation="Candidate contains the required canonical skill.",
                )
            )
            continue

        signal = demand.get(skill_id)
        normalized_demand = signal.normalized_demand if signal else None
        if normalized_demand is None:
            unavailable_demand = True
        trend = signal.trend_multiplier if signal and signal.trend_multiplier is not None else None
        if trend is None:
            trend = NEUTRAL_TREND_MULTIPLIER
            fallback_used = True

        gap_severity = 1.0
        priority = (
            normalized_demand * trend * gap_severity * role_importance
            if normalized_demand is not None
            else None
        )
        missing.append(
            MissingSkill(
                skill_id=skill_id,
                taxonomy_version=candidate.taxonomy_version,
                priority=priority,
                normalized_demand=normalized_demand,
                trend_multiplier=trend,
                gap_severity=gap_severity,
                role_importance=role_importance,
                explanation=(
                    "Required canonical skill is absent from the candidate profile."
                    if normalized_demand is not None
                    else "Required skill is absent, but no applicable demand value exists."
                ),
            )
        )

    if fallback_used:
        warnings.append("Trend unavailable; neutral trend multiplier 1.0 was used.")
    if unavailable_demand:
        warnings.append("Demand unavailable for one or more skills; priority was not fabricated.")
    missing.sort(key=lambda item: (item.priority is None, -(item.priority or 0), item.skill_id))
    return matched, missing, warnings