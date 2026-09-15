from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, models
from app.core import representations as reps
from app.core.matching import match
from app.core.shortlist import rank_shortlist

router = APIRouter(prefix="/api/v1/shortlists", tags=["shortlists"])


def _skill_name_lookup(db: Session) -> dict[str, str]:
    return {s.id: s.canonical_name for s in db.query(models.Skill).all()}


@router.post("", response_model=schemas.ShortlistCreateResponse)
def create_shortlist(req: schemas.ShortlistCreateRequest, db: Session = Depends(get_db)):
    target_profile = reps.job_target_profile(db, req.job_id)
    name_lookup = _skill_name_lookup(db)

    candidate_matches = []
    for cid in req.candidate_ids:
        candidate_profile = reps.candidate_profile(db, cid)
        r = match(candidate_profile, target_profile, name_lookup)
        candidate_matches.append((cid, r))

    ranked = rank_shortlist(candidate_matches, top_n=req.top_n)

    shortlist = models.Shortlist(job_id=req.job_id, recruiter_id=req.recruiter_id)
    db.add(shortlist)
    db.flush()

    for rc in ranked:
        db.add(models.ShortlistItem(
            shortlist_id=shortlist.id, candidate_id=rc.candidate_id,
            rank=rc.rank, decision="pending",
        ))
    db.commit()

    return schemas.ShortlistCreateResponse(
        shortlist_id=shortlist.id, job_id=req.job_id,
        items=[schemas.ShortlistItemOut(
            candidate_id=rc.candidate_id, rank=rc.rank,
            score=rc.match_result.score, decision="pending",
        ) for rc in ranked],
    )
