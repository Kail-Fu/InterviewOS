from fastapi import HTTPException

from app.core.config import Settings
from app.services.assessment import (
    generate_assessment_download_link,
    send_assessment_email,
)
from app.services.invite_store import (
    ACTIVE_STATUSES,
    InviteRecord,
    create_invite,
    get_invite_by_token,
    get_latest_invite_by_email,
    mark_invite_taken,
)


def _invite_url(token: str, settings: Settings) -> str:
    return f"{settings.frontend_base_url}/take-assessment?token={token}"


def _to_public_invite(invite: InviteRecord, settings: Settings) -> dict[str, str | int | None]:
    return {
        "id": invite.id,
        "email": invite.email,
        "token": invite.token,
        "status": invite.status,
        "createdAt": invite.created_at,
        "expiresAt": invite.expires_at,
        "takenAt": invite.taken_at,
        "supersededAt": invite.superseded_at,
        "inviteUrl": _invite_url(invite.token, settings),
    }


def create_and_send_invite(email: str, settings: Settings) -> dict[str, str | int | None]:
    normalized_email = email.strip().lower()
    invite = create_invite(normalized_email, settings, status="invited", supersede_existing=True)
    send_assessment_email(normalized_email, _invite_url(invite.token, settings), settings)
    return _to_public_invite(invite, settings)


def resend_invite(*, settings: Settings, email: str | None = None, token: str | None = None) -> dict[str, str | int | None]:
    if not email and not token:
        raise HTTPException(status_code=400, detail="Provide either email or token.")

    source_invite = None
    if token:
        source_invite = get_invite_by_token(token, settings)
    elif email:
        source_invite = get_latest_invite_by_email(email.strip().lower(), settings)

    if source_invite is None:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if source_invite.status == "taken":
        raise HTTPException(status_code=409, detail="Invite already taken.")

    resent = create_invite(
        source_invite.email,
        settings,
        status="resent",
        resent_from_token=source_invite.token,
        supersede_existing=True,
    )
    send_assessment_email(source_invite.email, _invite_url(resent.token, settings), settings, is_resend=True)
    return _to_public_invite(resent, settings)


def verify_invite(token: str, settings: Settings) -> dict[str, object]:
    invite = get_invite_by_token(token, settings)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invalid token.")

    is_active = invite.status in ACTIVE_STATUSES
    payload: dict[str, object] = {
        "valid": is_active,
        "invite": _to_public_invite(invite, settings),
    }
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
