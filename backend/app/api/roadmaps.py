from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.core import representations as reps
from app.core.gap import analyze_gap
from app.core.roadmap import generate_roadmap, persist_roadmap, RoadmapCycleError
from app.core.versioning import ROADMAP_MODEL_VERSION

router = APIRouter(prefix="/api/v1/roadmaps", tags=["roadmaps"])


@router.post("/generate", response_model=schemas.RoadmapGenerateResponse)
def generate(req: schemas.RoadmapGenerateRequest, db: Session = Depends(get_db)):
    candidate_profile = reps.candidate_profile(db, req.candidate_id)
    target_profile = reps.role_target_profile(db, req.target_role_id)

    if not target_profile.skills:
        raise HTTPException(status_code=404, detail="target_role_id has no defined role_skills")

    gaps = analyze_gap(db, candidate_profile, target_profile, req.district_id, req.sector)

    try:
        steps = generate_roadmap(db, gaps)
    except RoadmapCycleError as e:
        # Fail safely: 422, not a 500 and not a silently-broken roadmap.
        raise HTTPException(
            status_code=422,
            detail={"error": "prerequisite_cycle", "course_ids": e.cycle_course_ids},
        )

    roadmap = persist_roadmap(db, req.candidate_id, req.target_role_id, steps, ROADMAP_MODEL_VERSION)

    return schemas.RoadmapGenerateResponse(
        roadmap_id=roadmap.id,
        model_version=ROADMAP_MODEL_VERSION,
        steps=[schemas.RoadmapStepOut(
            skill_id=s.skill_id, course_id=s.course_id, project=s.project,
            step_order=s.step_order, duration=s.duration,
        ) for s in steps],
    )
