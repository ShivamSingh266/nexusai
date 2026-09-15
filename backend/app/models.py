import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, DateTime, JSON,
    UniqueConstraint, Text
)

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Skill(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True, default=gen_uuid)
    canonical_name = Column(String, unique=True, nullable=False)
    category = Column(String)
    aliases = Column(JSON, default=list)
    source = Column(String)
    version = Column(String, default="v1")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    proficiency = Column(Float, nullable=False)  # 0..1
    evidence = Column(String)  # e.g. "certified", "project", "self-reported"
    source = Column(String)
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skill"),)


class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    sector = Column(String)
    source = Column(String)


class RoleSkill(Base):
    __tablename__ = "role_skills"
    id = Column(String, primary_key=True, default=gen_uuid)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    importance = Column(Float, default=1.0)  # 0..1, used in gap priority
    min_proficiency = Column(Float, default=0.5)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=gen_uuid)
    recruiter_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String)
    description = Column(Text)
    district = Column(String)
    sector = Column(String)
    exp = Column(Float)  # required years of experience
    salary = Column(String)
    mode = Column(String)  # remote/hybrid/onsite
    source = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="open")


class JobSkill(Base):
    __tablename__ = "job_skills"
    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    importance = Column(Float, default=1.0)
    required_level = Column(Float, default=0.5)


class SkillDemandHistory(Base):
    __tablename__ = "skill_demand_history"
    id = Column(String, primary_key=True, default=gen_uuid)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    district_id = Column(String)
    sector = Column(String)
    period = Column(String)  # e.g. "2026-Q3"
    posting_count = Column(Integer)
    demand_score = Column(Float)  # normalized 0..1 — consumed directly by gap analyzer
    source = Column(String)


class SkillForecast(Base):
    __tablename__ = "skill_forecasts"
    id = Column(String, primary_key=True, default=gen_uuid)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    district_id = Column(String)
    sector = Column(String)
    horizon = Column(String)
    forecast = Column(Float)
    trend = Column(Float)  # multiplier, e.g. 1.15 = growing 15%
    model_version = Column(String)
    metrics = Column(JSON)


class Course(Base):
    __tablename__ = "courses"
    id = Column(String, primary_key=True, default=gen_uuid)
    provider = Column(String)
    name = Column(String, nullable=False)
    district_id = Column(String)
    sector = Column(String)
    level = Column(String)
    duration = Column(String)
    mode = Column(String)
    source_url = Column(String)


class CourseSkill(Base):
    __tablename__ = "course_skills"
    id = Column(String, primary_key=True, default=gen_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    coverage_level = Column(Float, default=1.0)


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    id = Column(String, primary_key=True, default=gen_uuid)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    prerequisite_course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    __table_args__ = (UniqueConstraint("course_id", "prerequisite_course_id", name="uq_course_prereq"),)


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, nullable=False, index=True)
    target_role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    severity = Column(Float)
    demand = Column(Float)
    trend = Column(Float)
    priority = Column(Float)
    explanation = Column(JSON)
    scoring_version = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Roadmap(Base):
    __tablename__ = "roadmaps"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, nullable=False, index=True)
    target_role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_version = Column(String)


class RoadmapStep(Base):
    __tablename__ = "roadmap_steps"
    id = Column(String, primary_key=True, default=gen_uuid)
    roadmap_id = Column(String, ForeignKey("roadmaps.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=True)
    project = Column(String, nullable=True)
    step_order = Column(Integer, nullable=False)
    duration = Column(String)
    status = Column(String, default="pending")


class JobMatch(Base):
    __tablename__ = "job_matches"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    score = Column(Float)
    skill_score = Column(Float)
    semantic_score = Column(Float)
    experience_score = Column(Float)
    matched_json = Column(JSON)
    missing_json = Column(JSON)
    scoring_version = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)


class Shortlist(Base):
    __tablename__ = "shortlists"
    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    recruiter_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"
    id = Column(String, primary_key=True, default=gen_uuid)
    shortlist_id = Column(String, ForeignKey("shortlists.id"), nullable=False)
    candidate_id = Column(String, nullable=False)
    rank = Column(Integer)
    decision = Column(String, default="pending")  # pending/shortlisted/rejected
    notes = Column(Text)
    decided_at = Column(DateTime, nullable=True)
