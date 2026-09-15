from fastapi import FastAPI

from app.api import gaps, roadmaps, matching, jobs, shortlists, whatif
from app.core.versioning import version_manifest

app = FastAPI(title="NexusAI — Gap, Matching, Roadmap & Shortlist Engine (Member 5)")

app.include_router(gaps.router)
app.include_router(roadmaps.router)
app.include_router(matching.router)
app.include_router(jobs.router)
app.include_router(shortlists.router)
app.include_router(whatif.router)


@app.get("/api/v1/meta/versions")
def get_versions():
    return version_manifest()


@app.get("/health")
def health():
    return {"status": "ok"}
