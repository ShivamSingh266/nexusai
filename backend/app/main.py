from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.deps import get_current_user, require_roles
from app.api.gaps import router as gaps_router
from app.api.government import router as government_router
from app.api.jobs import router as jobs_router
from app.api.job_skills import router as job_skills_router
from app.api.meta import router as meta_router
from app.api.matching import router as matching_router
from app.api.profile import router as profile_router
from app.api.roadmaps import router as roadmaps_router
from app.api.recruiter_company import router as recruiter_company_router
from app.api.shortlists import router as shortlists_router
from app.api.skills import router as skills_router
from app.api.taxonomy import router as taxonomy_router
from app.core.config import settings
from app.models.user import User


app = FastAPI(
    title="NexusAI API",
    description="NexusAI Labour Market Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(auth_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(roadmaps_router, prefix="/api/v1")
app.include_router(skills_router, prefix="/api/v1")
app.include_router(recruiter_company_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(job_skills_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(taxonomy_router, prefix="/api/v1")
app.include_router(gaps_router, prefix="/api/v1")
app.include_router(government_router, prefix="/api/v1")
app.include_router(shortlists_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "nexusai-backend",
    }


@app.get("/api/v1/users/me", tags=["Users"])
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.name,
            "is_active": current_user.is_active,
        },
        "meta": {},
        "model_version": None,
        "source_version": "backend-v1",
        "generated_at": None,
        "warnings": [],
    }


@app.get("/api/v1/rbac/admin-test", tags=["RBAC"])
def admin_test(
    current_user: User = Depends(require_roles("admin")),
):
    return {
        "data": {
            "message": "Admin access granted",
            "user_id": current_user.id,
            "role": current_user.role.name,
        },
        "meta": {},
        "model_version": None,
        "source_version": "backend-v1",
        "generated_at": None,
        "warnings": [],
    }
