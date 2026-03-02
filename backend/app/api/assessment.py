from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr

from app.core.config import Settings, get_settings
from app.services.assessment import (
    generate_assessment_download_link,
    schedule_reminder_email,
)
from app.services.assessment_store import get_assessment
from app.services.invites import create_and_send_invite

router = APIRouter(prefix="/assessments", tags=["assessments"])
legacy_router = APIRouter(tags=["assessments-legacy"])


class StartAssessmentRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    shareConsent: str | None = None
    company: str | None = None
    assessmentId: int | str | None = None


@router.post("/start")
async def start_assessment(
    payload: StartAssessmentRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
):
    if payload.name:
        assessment_id = payload.assessmentId if payload.assessmentId is not None else "default"
        assessment_type = "default"
        try:
            numeric_assessment_id = int(str(assessment_id))
            assessment = get_assessment(settings, numeric_assessment_id)
            if assessment is not None:
                assessment_type = assessment.assessment_type
        except ValueError:
            pass
        return {
            "downloadUrl": generate_assessment_download_link(settings),
            "assessmentId": assessment_id,
            "assessmentType": assessment_type,
            "s3Key": settings.assessment_object_key,
        }

    create_and_send_invite(payload.email, settings)
    background_tasks.add_task(schedule_reminder_email, payload.email, settings)
    return {"message": "Assessment sent to candidate."}


@legacy_router.post("/start-assessment", include_in_schema=False)
async def start_assessment_legacy(
    payload: StartAssessmentRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
):
    return await start_assessment(payload, background_tasks, settings)
