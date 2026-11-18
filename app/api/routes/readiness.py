from fastapi import APIRouter, HTTPException

from app.schemas.readiness import ReadinessRequest
from app.services.readiness_service import ReadinessError, calculate_readiness

router = APIRouter(prefix="/api/v1/readiness", tags=["Readiness"])


@router.post("")
def readiness(request: ReadinessRequest) -> dict[str, object]:
    try:
        return calculate_readiness(request)
    except ReadinessError as exc:
        raise HTTPException(422, detail={"code": "READINESS_INVALID_INPUT", "message": str(exc)}) from exc
