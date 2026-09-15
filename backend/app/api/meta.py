"""Backend contract and model metadata API."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.core.gap import SCORING_VERSION
from app.schemas.meta import MatchingMetadata, VersionMetadataResponse

router = APIRouter(prefix="/meta", tags=["Metadata"])


@router.get("/versions", response_model=VersionMetadataResponse)
def get_versions() -> VersionMetadataResponse:
    """Return deterministic versions currently active in the backend."""
    return VersionMetadataResponse(
        data={
            "backend_version": settings.APP_VERSION,
            "taxonomy_version": settings.TAXONOMY_VERSION,
            "gap_scoring_version": SCORING_VERSION,
            "matching": MatchingMetadata(
                implemented=False,
                version=None,
                weights=None,
            ),
        },
        meta={},
        model_version=None,
        source_version="backend-v1",
        generated_at=datetime.now(timezone.utc),
        warnings=["Matching is not implemented in this backend version."],
    )