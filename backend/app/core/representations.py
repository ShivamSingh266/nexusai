"""
Task 01 — Profile / target representations.

Every other engine (gap, match, roadmap, shortlist, what-if) consumes these
plain dataclasses instead of touching the ORM directly. This is the seam that
keeps Task04's match() function reusable for both applicant->job and
recruiter->candidate: both sides get converted into the same SkillProfile
shape before scoring.
"""
from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy.orm import Session

from app import models


@dataclass
class SkillEntry:
    skill_id: str
    proficiency: float = 1.0        # 0..1 — irrelevant (=1.0) on the "target" side
    importance: float = 1.0         # 0..1 — irrelevant on the "profile" side
    min_proficiency: float = 0.0    # only meaningful on the target side
    evidence: Optional[str] = None  # "certified" / "project" / "self-reported" / None


@dataclass
class SkillProfile:
    """A generic bag of skills. Used for BOTH:
    - a candidate's actual skills (proficiency matters, importance is 1.0)
    - a job/role's required skills (importance matters, proficiency is n/a)
    """
    owner_id: str
    kind: str  # "candidate" | "job" | "role"
    skills: dict[str, SkillEntry] = field(default_factory=dict)  # skill_id -> entry
    experience_years: Optional[float] = None
    education_level: Optional[float] = None   # normalized 0..1 scale, e.g. degree tier
    district: Optional[str] = None
    mode: Optional[str] = None                # remote/hybrid/onsite


def candidate_profile(db: Session, candidate_id: str, experience_years: float = None,
                       education_level: float = None, district: str = None) -> SkillProfile:
    rows = db.query(models.CandidateSkill).filter(
        models.CandidateSkill.candidate_id == candidate_id
    ).all()
    skills = {
        r.skill_id: SkillEntry(skill_id=r.skill_id, proficiency=r.proficiency, evidence=r.evidence)
        for r in rows
    }
    return SkillProfile(
        owner_id=candidate_id, kind="candidate", skills=skills,
        experience_years=experience_years, education_level=education_level, district=district,
    )


def role_target_profile(db: Session, role_id: str) -> SkillProfile:
    rows = db.query(models.RoleSkill).filter(models.RoleSkill.role_id == role_id).all()
    skills = {
        r.skill_id: SkillEntry(skill_id=r.skill_id, importance=r.importance,
                                min_proficiency=r.min_proficiency)
        for r in rows
    }
    return SkillProfile(owner_id=role_id, kind="role", skills=skills)


def job_target_profile(db: Session, job_id: str) -> SkillProfile:
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    rows = db.query(models.JobSkill).filter(models.JobSkill.job_id == job_id).all()
    skills = {
        r.skill_id: SkillEntry(skill_id=r.skill_id, importance=r.importance,
                                min_proficiency=r.required_level)
        for r in rows
    }
    return SkillProfile(
        owner_id=job_id, kind="job", skills=skills,
        experience_years=job.exp if job else None,
        district=job.district if job else None,
        mode=job.mode if job else None,
    )
