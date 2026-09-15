"""
Deterministic demo seed. Run with:
    python -m app.seed

Wipes and recreates every table this module owns, then loads a small,
realistic dataset so `docs/demo_script.md` (see README) always reproduces
the same screenshots/values — required by the testing checklist.
"""
from app.database import Base, engine, SessionLocal
from app import models

DEMO_CANDIDATE = "demo-candidate-1"
DEMO_ROLE = "demo-role-ml-engineer"
DEMO_RECRUITER = "demo-recruiter-1"


def reset_and_seed():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()

    skills = {
        "python": models.Skill(canonical_name="Python", category="programming",
                                aliases=["py"], source="seed", version="v1"),
        "sql": models.Skill(canonical_name="SQL", category="data", source="seed", version="v1"),
        "ml_fundamentals": models.Skill(canonical_name="ML Fundamentals", category="ml",
                                         source="seed", version="v1"),
        "deep_learning": models.Skill(canonical_name="Deep Learning", category="ml",
                                       source="seed", version="v1"),
        "nlp": models.Skill(canonical_name="NLP", category="ml", source="seed", version="v1"),
    }
    for s in skills.values():
        db.add(s)
    db.flush()

    role = models.Role(id=DEMO_ROLE, name="ML Engineer", sector="tech", source="seed")
    db.add(role)
    db.add_all([
        models.RoleSkill(role_id=role.id, skill_id=skills["python"].id, importance=0.9, min_proficiency=0.6),
        models.RoleSkill(role_id=role.id, skill_id=skills["sql"].id, importance=0.5, min_proficiency=0.4),
        models.RoleSkill(role_id=role.id, skill_id=skills["ml_fundamentals"].id, importance=1.0, min_proficiency=0.7),
        models.RoleSkill(role_id=role.id, skill_id=skills["deep_learning"].id, importance=0.8, min_proficiency=0.6),
        models.RoleSkill(role_id=role.id, skill_id=skills["nlp"].id, importance=0.6, min_proficiency=0.5),
    ])

    db.add_all([
        models.CandidateSkill(candidate_id=DEMO_CANDIDATE, skill_id=skills["python"].id,
                               proficiency=0.8, evidence="project", source="seed"),
        models.CandidateSkill(candidate_id=DEMO_CANDIDATE, skill_id=skills["sql"].id,
                               proficiency=0.5, evidence="self-reported", source="seed"),
        models.CandidateSkill(candidate_id=DEMO_CANDIDATE, skill_id=skills["ml_fundamentals"].id,
                               proficiency=0.45, evidence="course", source="seed"),
    ])

    job = models.Job(recruiter_id=DEMO_RECRUITER, title="ML Engineer", company="Demo Corp",
                      description="Applied ML role for the SIH demo.", district="Pune",
                      sector="tech", exp=2, salary="8-12 LPA", mode="hybrid", source="seed",
                      status="open")
    db.add(job)
    db.flush()
    db.add_all([
        models.JobSkill(job_id=job.id, skill_id=skills["python"].id, importance=0.9, required_level=0.6),
        models.JobSkill(job_id=job.id, skill_id=skills["ml_fundamentals"].id, importance=1.0, required_level=0.7),
        models.JobSkill(job_id=job.id, skill_id=skills["deep_learning"].id, importance=0.8, required_level=0.5),
    ])

    db.add(models.SkillDemandHistory(skill_id=skills["deep_learning"].id, district_id="Pune",
                                      sector="tech", period="2026-Q3", posting_count=140,
                                      demand_score=0.9, source="seed"))
    db.add(models.SkillForecast(skill_id=skills["deep_learning"].id, district_id="Pune",
                                 sector="tech", horizon="6m", forecast=0.95, trend=1.3,
                                 model_version="seed-static"))

    course_ml = models.Course(provider="NPTEL", name="ML Fundamentals", district_id="Pune",
                               sector="tech", level="beginner", duration="6w", mode="online",
                               source_url="https://example.org/ml-fundamentals")
    course_dl = models.Course(provider="NPTEL", name="Deep Learning", district_id="Pune",
                               sector="tech", level="intermediate", duration="8w", mode="online",
                               source_url="https://example.org/deep-learning")
    db.add_all([course_ml, course_dl])
    db.flush()
    db.add_all([
        models.CourseSkill(course_id=course_ml.id, skill_id=skills["ml_fundamentals"].id, coverage_level=1.0),
        models.CourseSkill(course_id=course_dl.id, skill_id=skills["deep_learning"].id, coverage_level=1.0),
    ])
    db.add(models.CoursePrerequisite(course_id=course_dl.id, prerequisite_course_id=course_ml.id))

    db.commit()
    print(f"Seeded. candidate_id={DEMO_CANDIDATE} role_id={role.id} job_id={job.id}")
    db.close()


if __name__ == "__main__":
    reset_and_seed()
