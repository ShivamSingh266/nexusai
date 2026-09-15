from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, models
from app.core import representations as reps
from app.core.whatif import evaluate_what_if

router = APIRouter(prefix="/api/v1/whatif", tags=["whatif"])


@router.post("/evaluate", response_model=schemas.WhatIfResponse)
def evaluate(req: schemas.WhatIfRequest, db: Session = Depends(get_db)):
    candidate_profile = reps.candidate_profile(db, req.candidate_id)
    target_profile = reps.role_target_profile(db, req.target_role_id)
    name_lookup = {s.id: s.canonical_name for s in db.query(models.Skill).all()}

    result = evaluate_what_if(
        db, candidate_profile, target_profile, req.hypothetical_skills,
        name_lookup, req.district_id, req.sector,
    )

    return schemas.WhatIfResponse(
        baseline_score=result.baseline_match.score,
        hypothetical_score=result.hypothetical_match.score,
        score_delta=result.score_delta,
        baseline_gap_count=result.baseline_gap_count,
        hypothetical_gap_count=result.hypothetical_gap_count,
        gap_priority_removed=result.gap_priority_removed,
        resolved_skill_ids=result.resolved_skill_ids,
    )
