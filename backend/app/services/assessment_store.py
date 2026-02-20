import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings


@dataclass
class AssessmentRecord:
    id: int
    title: str
    role: str
    status: str
    created_at: str
    candidate_count: int


@dataclass
class CandidateRecord:
    id: int
    assessment_id: int
    email: str
    name: str | None
    status: str
    invited_at: str


def _connect(settings: Settings) -> sqlite3.Connection:
    db_path = Path(settings.local_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def init_assessment_store(settings: Settings) -> None:
    with _connect(settings) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                name TEXT,
                status TEXT NOT NULL,
                invited_at TEXT NOT NULL,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            )
            """
        )
        _seed_demo_rows(connection)


def _seed_demo_rows(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT COUNT(*) AS count FROM assessments").fetchone()
    if existing is not None and int(existing["count"]) > 0:
        return

    created_at = _iso_now()
    cursor = connection.execute(
        """
        INSERT INTO assessments (title, role, status, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("Backend API Work Simulation", "Backend Engineer", "active", created_at),
    )
    assessment_id = int(cursor.lastrowid)
    connection.execute(
        """
        INSERT INTO candidates (assessment_id, email, name, status, invited_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (assessment_id, "candidate@example.com", "Sample Candidate", "invited", created_at),
    )


def list_assessments(settings: Settings) -> list[AssessmentRecord]:
    with _connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT
                a.id,
                a.title,
                a.role,
                a.status,
                a.created_at,
                COALESCE(COUNT(c.id), 0) AS candidate_count
            FROM assessments a
            LEFT JOIN candidates c ON c.assessment_id = a.id
            GROUP BY a.id
            ORDER BY a.created_at DESC
            """
        ).fetchall()
        return [
            AssessmentRecord(
                id=int(row["id"]),
                title=str(row["title"]),
                role=str(row["role"]),
                status=str(row["status"]),
                created_at=str(row["created_at"]),
                candidate_count=int(row["candidate_count"]),
            )
            for row in rows
        ]


def list_candidates(settings: Settings, assessment_id: int | None = None) -> list[CandidateRecord]:
    with _connect(settings) as connection:
        if assessment_id is None:
            rows = connection.execute(
                """
                SELECT id, assessment_id, email, name, status, invited_at
                FROM candidates
                ORDER BY invited_at DESC
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, assessment_id, email, name, status, invited_at
                FROM candidates
                WHERE assessment_id = ?
                ORDER BY invited_at DESC
                """,
                (assessment_id,),
            ).fetchall()
        return [
            CandidateRecord(
                id=int(row["id"]),
                assessment_id=int(row["assessment_id"]),
                email=str(row["email"]),
                name=row["name"],
                status=str(row["status"]),
                invited_at=str(row["invited_at"]),
            )
            for row in rows
        ]
