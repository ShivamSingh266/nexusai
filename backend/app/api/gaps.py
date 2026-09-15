from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.core import representations as reps
from app.core.gap import analyze_gap, persist_gaps
from app.config import settings

router = APIRouter(prefix="/api/v1/gaps", tags=["gaps"])


@router.post("/analyze", response_model=schemas.GapAnalyzeResponse)
def analyze(req: schemas.GapAnalyzeRequest, db: Session = Depends(get_db)):
    candidate_profile = reps.candidate_profile(db, req.candidate_id)
    target_profile = reps.role_target_profile(db, req.target_role_id)

    if not target_profile.skills:
        raise HTTPException(status_code=404, detail="target_role_id has no defined role_skills")

    results = analyze_gap(db, candidate_profile, target_profile, req.district_id, req.sector)

    if req.persist:
        persist_gaps(db, req.candidate_id, req.target_role_id, results)

    return schemas.GapAnalyzeResponse(
        candidate_id=req.candidate_id,
        target_role_id=req.target_role_id,
        scoring_version=settings.SCORING_VERSION,
        gaps=[schemas.SkillGapOut(**r.__dict__) for r in results],
    )
