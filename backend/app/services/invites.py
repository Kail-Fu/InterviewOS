from fastapi import HTTPException

from app.core.config import Settings
from app.services.assessment import (
    generate_assessment_download_link,
    send_assessment_email,
)
from app.services.assessment_store import add_or_update_candidate, get_candidate_by_id
from app.services.assessment_store import get_assessment, get_candidate_by_assessment_and_email
from app.services.invite_store import (
    ACTIVE_STATUSES,
    InviteRecord,
    create_invite,
    get_invite_by_token,
    get_latest_invite_by_email,
    get_latest_invite_by_email_and_assessment,
    mark_invite_taken,
)


def _invite_url(token: str, settings: Settings) -> str:
    return f"{settings.frontend_base_url}/take-assessment?token={token}"


def _to_public_invite(invite: InviteRecord, settings: Settings) -> dict[str, str | int | None]:
    candidate_name = None
    if invite.assessment_id is not None:
        candidate = get_candidate_by_assessment_and_email(
            settings, assessment_id=invite.assessment_id, email=invite.email
        )
        if candidate is not None:
            candidate_name = candidate.name

    return {
        "id": invite.id,
        "email": invite.email,
        "name": candidate_name,
        "token": invite.token,
        "assessmentId": invite.assessment_id,
        "status": invite.status,
        "createdAt": invite.created_at,
        "expiresAt": invite.expires_at,
        "takenAt": invite.taken_at,
        "supersededAt": invite.superseded_at,
        "inviteUrl": _invite_url(invite.token, settings),
    }


def create_and_send_invite(
    email: str,
    settings: Settings,
    *,
    assessment_id: int | None = None,
    candidate_name: str | None = None,
) -> dict[str, str | int | None]:
    normalized_email = email.strip().lower()
    invite = create_invite(
        normalized_email,
        settings,
        assessment_id=assessment_id,
        status="invited",
        supersede_existing=True,
    )
    send_assessment_email(normalized_email, _invite_url(invite.token, settings), settings)
    if assessment_id is not None:
        add_or_update_candidate(
            settings,
            assessment_id=assessment_id,
            email=normalized_email,
            name=candidate_name,
            status="invited",
        )
    return _to_public_invite(invite, settings)


def resend_invite(
    *,
    settings: Settings,
    email: str | None = None,
    token: str | None = None,
    assessment_id: int | None = None,
    candidate_id: int | None = None,
) -> dict[str, str | int | None]:
    if not email and not token and candidate_id is None:
        raise HTTPException(status_code=400, detail="Provide email, token, or candidateId.")

    if candidate_id is not None:
        candidate = get_candidate_by_id(settings, candidate_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate not found.")
        email = candidate.email
        if assessment_id is None:
            assessment_id = candidate.assessment_id

    target_assessment_id = assessment_id
    source_invite = None
    if token:
        source_invite = get_invite_by_token(token, settings)
    elif email:
        normalized_email = email.strip().lower()
        if target_assessment_id is not None:
            source_invite = get_latest_invite_by_email_and_assessment(
                normalized_email,
                target_assessment_id,
                settings,
            )
        else:
            source_invite = get_latest_invite_by_email(normalized_email, settings)

    if source_invite is None:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if source_invite.status == "taken":
        raise HTTPException(status_code=409, detail="Invite already taken.")

    if target_assessment_id is not None:
        invite_assessment_id = source_invite.assessment_id
        if invite_assessment_id is not None and invite_assessment_id != target_assessment_id:
            raise HTTPException(
                status_code=409,
                detail="Invite does not belong to the provided assessment.",
            )

    resolved_assessment_id = (
        target_assessment_id if target_assessment_id is not None else source_invite.assessment_id
    )

    resent = create_invite(
        source_invite.email,
        settings,
        assessment_id=resolved_assessment_id,
        status="resent",
        resent_from_token=source_invite.token,
        supersede_existing=True,
    )
    send_assessment_email(source_invite.email, _invite_url(resent.token, settings), settings, is_resend=True)
    if resolved_assessment_id is not None:
        add_or_update_candidate(
            settings,
            assessment_id=resolved_assessment_id,
            email=source_invite.email,
            name=None,
            status="resent",
        )
    return _to_public_invite(resent, settings)


def verify_invite(token: str, settings: Settings) -> dict[str, object]:
    invite = get_invite_by_token(token, settings)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invalid token.")

    assessment_missing = False
    if invite.assessment_id is not None:
        assessment_missing = get_assessment(settings, invite.assessment_id) is None

    is_active = invite.status in ACTIVE_STATUSES and not assessment_missing
    payload: dict[str, object] = {
        "valid": is_active,
        "invite": _to_public_invite(invite, settings),
    }
    if invite.status == "expired":
        payload["expired"] = True
    if invite.status == "taken":
        payload["taken"] = True
    if assessment_missing:
        payload["assessmentMissing"] = True
        payload["reason"] = "Assessment not found."
    if is_active:
        payload["assessmentDownloadUrl"] = generate_assessment_download_link(settings)
    return payload


def mark_taken(token: str, settings: Settings) -> dict[str, object]:
    invite = mark_invite_taken(token, settings)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return {
        "markedTaken": invite.status == "taken",
        "invite": _to_public_invite(invite, settings),
    }
