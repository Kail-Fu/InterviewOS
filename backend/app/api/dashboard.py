from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.services.assessment_store import list_assessments, list_candidates

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/assessments")
def get_assessments(settings: Settings = Depends(get_settings)):
    assessments = list_assessments(settings)
    return {
        "assessments": [
            {
                "id": item.id,
                "title": item.title,
                "role": item.role,
                "status": item.status,
                "createdAt": item.created_at,
                "candidateCount": item.candidate_count,
            }
            for item in assessments
        ]
    }


@router.get("/candidates")
def get_candidates(
    assessment_id: int | None = Query(default=None, alias="assessmentId"),
    settings: Settings = Depends(get_settings),
):
    candidates = list_candidates(settings, assessment_id=assessment_id)
    return {
        "candidates": [
            {
                "id": item.id,
                "assessmentId": item.assessment_id,
                "email": item.email,
                "name": item.name,
                "status": item.status,
                "invitedAt": item.invited_at,
            }
            for item in candidates
        ]
    }
