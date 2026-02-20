from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr

from app.core.config import Settings, get_settings
from app.services.assessment import (
    schedule_reminder_email,
)
from app.services.invites import create_and_send_invite

router = APIRouter(prefix="/assessments", tags=["assessments"])
legacy_router = APIRouter(tags=["assessments-legacy"])


class StartAssessmentRequest(BaseModel):
    email: EmailStr


@router.post("/start")
async def start_assessment(
    payload: StartAssessmentRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
):
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
