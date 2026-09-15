"""
GET/POST /api/v1/jobs is listed in the shared endpoint table (F1 search /
F6 create-job, both marked as touching other modules), but Member 5 only
needs read access here to feed the matcher. Kept minimal on purpose — do
not duplicate whatever Member 3/6 build for full job CRUD.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
def search_jobs(
    sector: str | None = Query(default=None),
    district: str | None = Query(default=None),
    status: str = Query(default="open"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Job).filter(models.Job.status == status)
    if sector:
        q = q.filter(models.Job.sector == sector)
    if district:
        q = q.filter(models.Job.district == district)
    jobs = q.all()
    return [
        {"id": j.id, "title": j.title, "company": j.company, "district": j.district,
         "sector": j.sector, "mode": j.mode, "status": j.status}
        for j in jobs
    ]
