from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.core.config import Settings, get_settings
from app.services.invites import (
    create_and_send_invite,
    mark_taken,
    resend_invite,
    verify_invite,
)

router = APIRouter(prefix="/api/invite", tags=["invite"])


class CandidateInvite(BaseModel):
    email: EmailStr
    name: str | None = None


class BulkInviteRequest(BaseModel):
    candidates: list[CandidateInvite]


class ResendInviteRequest(BaseModel):
    email: EmailStr | None = None
    token: str | None = None


class MarkTakenRequest(BaseModel):
    token: str


@router.post("/bulk")
def send_bulk_invites(payload: BulkInviteRequest, settings: Settings = Depends(get_settings)):
    invites = [create_and_send_invite(candidate.email, settings) for candidate in payload.candidates]
    return {"message": "Invites sent.", "count": len(invites), "invites": invites}


@router.post("/resend")
def resend(payload: ResendInviteRequest, settings: Settings = Depends(get_settings)):
    invite = resend_invite(settings=settings, email=payload.email, token=payload.token)
    return {"message": "Invite resent.", "invite": invite}


@router.get("/verify")
def verify(token: str, settings: Settings = Depends(get_settings)):
    return verify_invite(token, settings)


@router.post("/mark-taken")
def mark_invite_taken(payload: MarkTakenRequest, settings: Settings = Depends(get_settings)):
    return mark_taken(payload.token, settings)
