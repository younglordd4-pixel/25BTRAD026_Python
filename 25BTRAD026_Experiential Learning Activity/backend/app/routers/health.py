from fastapi import APIRouter

from ..schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Get Health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", app="StudyVerse Offline Backend")
