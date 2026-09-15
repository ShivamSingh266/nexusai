"""
Task 02 — F3 gap analyzer.

Frozen baseline (Final V2):
    gap_priority = normalized_demand * trend_multiplier * gap_severity * role_importance

Design notes:
- "Explicit overlap first" means we compute the raw skill-by-skill delta
  between candidate and target BEFORE touching any demand/trend signal.
  Demand and trend only ever multiply an already-real gap; they can't
  invent one. A skill the candidate already meets never shows up here,
  regardless of how hot the market for it is.
- demand/trend default to neutral (1.0) when Member 4/6 haven't published
  data yet for a skill, so this module can run standalone per the "thin
  vertical slice" rule in the blueprint, rather than blocking on upstream.
"""
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.core.representations import SkillProfile


@dataclass
class SkillGapResult:
    skill_id: str
    gap_severity: float
    normalized_demand: float
    trend_multiplier: float
    role_importance: float
    priority: float
    explanation: dict


def _latest_demand(db: Session, skill_id: str, district_id: str = None, sector: str = None) -> float:
    q = db.query(models.SkillDemandHistory).filter(models.SkillDemandHistory.skill_id == skill_id)
    if district_id:
        q = q.filter(models.SkillDemandHistory.district_id == district_id)
    if sector:
        q = q.filter(models.SkillDemandHistory.sector == sector)
    row = q.order_by(models.SkillDemandHistory.period.desc()).first()
    return row.demand_score if row and row.demand_score is not None else 1.0


def _trend_multiplier(db: Session, skill_id: str, district_id: str = None, sector: str = None) -> float:
    q = db.query(models.SkillForecast).filter(models.SkillForecast.skill_id == skill_id)
    if district_id:
        q = q.filter(models.SkillForecast.district_id == district_id)
    if sector:
        q = q.filter(models.SkillForecast.sector == sector)
    row = q.order_by(models.SkillForecast.horizon.desc()).first()
    return row.trend if row and row.trend is not None else 1.0


def compute_gap_severity(candidate_proficiency: float, min_proficiency: float) -> float:
    """Explicit overlap: how far below the bar the candidate sits. 0 if they
    already meet/exceed the requirement. Range: 0..1."""
    return max(0.0, min_proficiency - candidate_proficiency)


def analyze_gap(
    db: Session,
    candidate_profile: SkillProfile,
    target_profile: SkillProfile,
    district_id: str = None,
    sector: str = None,
) -> list[SkillGapResult]:
    results: list[SkillGapResult] = []

    for skill_id, target_entry in target_profile.skills.items():
        candidate_entry = candidate_profile.skills.get(skill_id)
        candidate_prof = candidate_entry.proficiency if candidate_entry else 0.0

        severity = compute_gap_severity(candidate_prof, target_entry.min_proficiency)
        if severity <= 0:
            continue  # explicit overlap: requirement already met, no gap to report

        demand = _latest_demand(db, skill_id, district_id, sector)
        trend = _trend_multiplier(db, skill_id, district_id, sector)
        importance = target_entry.importance or 1.0

        priority = (
            (demand ** settings.GAP_DEMAND_WEIGHT)
            * (trend ** settings.GAP_TREND_WEIGHT)
            * (severity ** settings.GAP_SEVERITY_WEIGHT)
            * (importance ** settings.GAP_IMPORTANCE_WEIGHT)
        )

        results.append(SkillGapResult(
            skill_id=skill_id,
            gap_severity=round(severity, 4),
            normalized_demand=round(demand, 4),
            trend_multiplier=round(trend, 4),
            role_importance=round(importance, 4),
            priority=round(priority, 4),
            explanation={
                "candidate_proficiency": round(candidate_prof, 4),
                "required_proficiency": target_entry.min_proficiency,
                "formula": "normalized_demand * trend_multiplier * gap_severity * role_importance",
                "scoring_version": settings.SCORING_VERSION,
            },
        ))

    results.sort(key=lambda r: r.priority, reverse=True)
    return results


def persist_gaps(db: Session, candidate_id: str, target_role_id: str,
                  results: list[SkillGapResult]) -> list[models.SkillGap]:
    rows = []
    for r in results:
        row = models.SkillGap(
            candidate_id=candidate_id,
            target_role_id=target_role_id,
            skill_id=r.skill_id,
            severity=r.gap_severity,
            demand=r.normalized_demand,
            trend=r.trend_multiplier,
            priority=r.priority,
            explanation=r.explanation,
            scoring_version=settings.SCORING_VERSION,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    return rows
