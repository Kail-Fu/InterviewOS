import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import Settings

ACTIVE_STATUSES = ("invited", "resent")


@dataclass
class InviteRecord:
    id: int
    email: str
    token: str
    status: str
    created_at: str
    expires_at: str
    taken_at: str | None
    superseded_at: str | None
    resent_from_token: str | None


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _settings_db_path(settings: Settings) -> Path:
    return Path(settings.local_db_path)


def _connect(settings: Settings) -> sqlite3.Connection:
    db_path = _settings_db_path(settings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_store(settings: Settings) -> None:
    with _connect(settings) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                taken_at TEXT,
                superseded_at TEXT,
                resent_from_token TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_invites_email_created_at ON invites(email, created_at DESC)"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_invites_token ON invites(token)")


def _row_to_record(row: sqlite3.Row) -> InviteRecord:
    return InviteRecord(
        id=int(row["id"]),
        email=str(row["email"]),
        token=str(row["token"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        expires_at=str(row["expires_at"]),
        taken_at=row["taken_at"],
        superseded_at=row["superseded_at"],
        resent_from_token=row["resent_from_token"],
    )


def _set_status(connection: sqlite3.Connection, invite_id: int, status: str) -> None:
    superseded_at = _iso(_utc_now()) if status == "superseded" else None
    taken_at = _iso(_utc_now()) if status == "taken" else None
    connection.execute(
        """
        UPDATE invites
        SET status = ?,
            superseded_at = COALESCE(?, superseded_at),
            taken_at = COALESCE(?, taken_at)
        WHERE id = ?
        """,
        (status, superseded_at, taken_at, invite_id),
    )


def _expire_if_needed(connection: sqlite3.Connection, invite: InviteRecord) -> InviteRecord:
    if invite.status not in ACTIVE_STATUSES:
        return invite

    expires_at = datetime.fromisoformat(invite.expires_at)
    if expires_at > _utc_now():
        return invite

    _set_status(connection, invite.id, "expired")
    row = connection.execute("SELECT * FROM invites WHERE id = ?", (invite.id,)).fetchone()
    if row is None:
        return invite
    return _row_to_record(row)


def supersede_active_invites(email: str, settings: Settings) -> int:
    with _connect(settings) as connection:
        result = connection.execute(
            """
            UPDATE invites
            SET status = 'superseded', superseded_at = ?
            WHERE lower(email) = lower(?)
              AND status IN ('invited', 'resent')
            """,
            (_iso(_utc_now()), email),
        )
        return int(result.rowcount)


def create_invite(
    email: str,
    settings: Settings,
    *,
    status: str = "invited",
    resent_from_token: str | None = None,
    supersede_existing: bool = True,
) -> InviteRecord:
    now = _utc_now()
    expires_at = now + timedelta(seconds=settings.invite_expiry_seconds)
    token = secrets.token_urlsafe(32)

    with _connect(settings) as connection:
        if supersede_existing:
            connection.execute(
                """
                UPDATE invites
                SET status = 'superseded', superseded_at = ?
                WHERE lower(email) = lower(?)
                  AND status IN ('invited', 'resent')
                """,
                (_iso(now), email),
            )

        cursor = connection.execute(
            """
            INSERT INTO invites (email, token, status, created_at, expires_at, resent_from_token)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, token, status, _iso(now), _iso(expires_at), resent_from_token),
        )
        invite_id = int(cursor.lastrowid)
        row = connection.execute("SELECT * FROM invites WHERE id = ?", (invite_id,)).fetchone()
        if row is None:
            raise RuntimeError("Failed to persist invite")
        return _row_to_record(row)


def get_invite_by_token(token: str, settings: Settings) -> InviteRecord | None:
    with _connect(settings) as connection:
        row = connection.execute("SELECT * FROM invites WHERE token = ?", (token,)).fetchone()
        if row is None:
            return None
        invite = _row_to_record(row)
        return _expire_if_needed(connection, invite)


def get_latest_invite_by_email(email: str, settings: Settings) -> InviteRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT * FROM invites
            WHERE lower(email) = lower(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (email,),
        ).fetchone()
        if row is None:
            return None
        invite = _row_to_record(row)
        return _expire_if_needed(connection, invite)


def mark_invite_taken(token: str, settings: Settings) -> InviteRecord | None:
    with _connect(settings) as connection:
        row = connection.execute("SELECT * FROM invites WHERE token = ?", (token,)).fetchone()
        if row is None:
            return None
        invite = _expire_if_needed(connection, _row_to_record(row))
        if invite.status not in ACTIVE_STATUSES:
            return invite

        _set_status(connection, invite.id, "taken")
        updated = connection.execute("SELECT * FROM invites WHERE id = ?", (invite.id,)).fetchone()
        if updated is None:
            return invite
        return _row_to_record(updated)
