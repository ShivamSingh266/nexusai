from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, models
from app.core import representations as reps
from app.core.matching import match
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["matching"])


def _skill_name_lookup(db: Session) -> dict[str, str]:
    return {s.id: s.canonical_name for s in db.query(models.Skill).all()}


def _persist_match(db: Session, candidate_id: str, job_id: str, result) -> None:
    existing = db.query(models.JobMatch).filter_by(candidate_id=candidate_id, job_id=job_id).first()
    payload = dict(
        score=result.score, skill_score=result.components.get("skill_coverage"),
        semantic_score=result.components.get("semantic"),
        experience_score=result.components.get("experience"),
        matched_json=result.matched_skills, missing_json=result.missing_skills,
        scoring_version=settings.SCORING_VERSION,
    )
    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
    else:
        db.add(models.JobMatch(candidate_id=candidate_id, job_id=job_id, **payload))
    db.commit()


@router.post("/matching/jobs", response_model=list[schemas.MatchResponse])
def rank_jobs(req: schemas.RankJobsRequest, db: Session = Depends(get_db)):
    """Applicant -> job direction. Ranks candidate against a set of jobs
    (or all open jobs if job_ids omitted)."""
    candidate_profile = reps.candidate_profile(db, req.candidate_id)
    name_lookup = _skill_name_lookup(db)

    if req.job_ids:
        jobs = db.query(models.Job).filter(models.Job.id.in_(req.job_ids)).all()
    else:
        jobs = db.query(models.Job).filter(models.Job.status == "open").all()

    results = []
    for job in jobs:
        target_profile = reps.job_target_profile(db, job.id)
        r = match(candidate_profile, target_profile, name_lookup)
        _persist_match(db, req.candidate_id, job.id, r)
        results.append((job.id, r))

    results.sort(key=lambda item: -item[1].score)
    if req.top_n:
        results = results[:req.top_n]

    return [_to_match_response(req.candidate_id, jid, r) for jid, r in results]


@router.get("/jobs/{job_id}/candidates", response_model=list[schemas.MatchResponse])
def rank_candidates(job_id: str, top_n: int | None = Query(default=None), db: Session = Depends(get_db)):
    """Recruiter -> candidate direction. Same match() function as above —
    just candidate/target roles swapped for the call."""
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    target_profile = reps.job_target_profile(db, job_id)
    name_lookup = _skill_name_lookup(db)

    candidate_ids = [row[0] for row in db.query(models.CandidateSkill.candidate_id).distinct().all()]

    results = []
    for cid in candidate_ids:
        candidate_profile = reps.candidate_profile(db, cid)
        r = match(candidate_profile, target_profile, name_lookup)
        _persist_match(db, cid, job_id, r)
        results.append((cid, r))

    results.sort(key=lambda item: -item[1].score)
    if top_n:
        results = results[:top_n]

    return [_to_match_response(cid, job_id, r) for cid, r in results]


def _to_match_response(candidate_id: str, job_id: str, r) -> schemas.MatchResponse:
    return schemas.MatchResponse(
        candidate_id=candidate_id, job_id=job_id, score=r.score,
        components=schemas.MatchComponentsOut(**r.components),
        weights_used=r.weights_used, matched_skills=r.matched_skills,
        missing_skills=r.missing_skills, explanation=r.explanation,
        scoring_version=r.scoring_version,
    )
