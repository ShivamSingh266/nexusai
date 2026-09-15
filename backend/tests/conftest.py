import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models

CAND = "cand-1"
ROLE = "role-ml-engineer"
JOB = "job-1"

SKILL_PY = "skill-python"
SKILL_SQL = "skill-sql"
SKILL_ML = "skill-ml-fundamentals"
SKILL_DL = "skill-deep-learning"

COURSE_PY = "course-python-basics"
COURSE_ML = "course-ml-fundamentals"
COURSE_DL = "course-deep-learning"


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    for sid, name in [
        (SKILL_PY, "Python"), (SKILL_SQL, "SQL"),
        (SKILL_ML, "ML Fundamentals"), (SKILL_DL, "Deep Learning"),
    ]:
        session.add(models.Skill(id=sid, canonical_name=name, category="tech"))

    session.add(models.Role(id=ROLE, name="ML Engineer", sector="tech"))
    session.add_all([
        models.RoleSkill(role_id=ROLE, skill_id=SKILL_PY, importance=0.9, min_proficiency=0.6),
        models.RoleSkill(role_id=ROLE, skill_id=SKILL_SQL, importance=0.5, min_proficiency=0.4),
        models.RoleSkill(role_id=ROLE, skill_id=SKILL_ML, importance=1.0, min_proficiency=0.7),
        models.RoleSkill(role_id=ROLE, skill_id=SKILL_DL, importance=0.8, min_proficiency=0.6),
    ])

    # Candidate already meets Python and SQL, is short on ML fundamentals,
    # and has nothing at all in deep learning.
    session.add_all([
        models.CandidateSkill(candidate_id=CAND, skill_id=SKILL_PY, proficiency=0.8, evidence="project"),
        models.CandidateSkill(candidate_id=CAND, skill_id=SKILL_SQL, proficiency=0.5, evidence="self-reported"),
        models.CandidateSkill(candidate_id=CAND, skill_id=SKILL_ML, proficiency=0.4, evidence="course"),
    ])

    session.add(models.Job(
        id=JOB, recruiter_id="rec-1", title="ML Engineer", company="Acme",
        district="Pune", sector="tech", exp=2, mode="hybrid", status="open",
    ))
    session.add_all([
        models.JobSkill(job_id=JOB, skill_id=SKILL_PY, importance=0.9, required_level=0.6),
        models.JobSkill(job_id=JOB, skill_id=SKILL_ML, importance=1.0, required_level=0.7),
        models.JobSkill(job_id=JOB, skill_id=SKILL_DL, importance=0.8, required_level=0.5),
    ])

    session.add(models.SkillDemandHistory(
        skill_id=SKILL_DL, district_id="Pune", sector="tech",
        period="2026-Q3", posting_count=120, demand_score=0.9,
    ))
    session.add(models.SkillForecast(
        skill_id=SKILL_DL, district_id="Pune", sector="tech",
        horizon="6m", forecast=0.95, trend=1.3, model_version="prophet-v1",
    ))

    session.add(models.Course(id=COURSE_PY, provider="NPTEL", name="Python Basics", duration="4w"))
    session.add(models.Course(id=COURSE_ML, provider="NPTEL", name="ML Fundamentals", duration="6w"))
    session.add(models.Course(id=COURSE_DL, provider="NPTEL", name="Deep Learning", duration="8w"))
    session.add_all([
        models.CourseSkill(course_id=COURSE_PY, skill_id=SKILL_PY, coverage_level=1.0),
        models.CourseSkill(course_id=COURSE_ML, skill_id=SKILL_ML, coverage_level=1.0),
        models.CourseSkill(course_id=COURSE_DL, skill_id=SKILL_DL, coverage_level=1.0),
    ])
    # Deep Learning requires ML Fundamentals first — a real prerequisite edge.
    session.add(models.CoursePrerequisite(course_id=COURSE_DL, prerequisite_course_id=COURSE_ML))

    session.commit()
    yield session
    session.close()
