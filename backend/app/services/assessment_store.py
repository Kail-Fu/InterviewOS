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
    question_id: int | None
    job_link: str | None
    job_desc: str | None


@dataclass
class CandidateRecord:
    id: int
    assessment_id: int
    email: str
    name: str | None
    status: str
    invited_at: str


@dataclass
class QuestionRecord:
    id: int
    title: str
    summary: str
    difficulty: str
    role: str
    language: str
    overview: str
    estimated_time: str


def _connect(settings: Settings) -> sqlite3.Connection:
    db_path = Path(settings.local_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {str(row["name"]) for row in rows}
    if column in existing:
        return
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def init_assessment_store(settings: Settings) -> None:
    with _connect(settings) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                question_id INTEGER,
                job_link TEXT,
                job_desc TEXT
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                role TEXT NOT NULL,
                language TEXT NOT NULL,
                overview TEXT NOT NULL,
                estimated_time TEXT NOT NULL
            )
            """
        )
        _ensure_column(connection, "assessments", "question_id", "INTEGER")
        _ensure_column(connection, "assessments", "job_link", "TEXT")
        _ensure_column(connection, "assessments", "job_desc", "TEXT")
        _seed_questions(connection)
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


def _seed_questions(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT COUNT(*) AS count FROM questions").fetchone()
    if existing is not None and int(existing["count"]) > 0:
        return

    rows = [
        (
            "Build a FastAPI Assessment Service",
            "Implement invite, submission, and report APIs with clean architecture.",
            "medium",
            "Backend Engineer",
            "Python",
            "Design endpoints and persistence for assessment lifecycle and invite flow.",
            "90 minutes",
        ),
        (
            "Debug and Extend React Dashboard",
            "Ship a dashboard feature and explain tradeoffs in implementation.",
            "easy",
            "Frontend Engineer",
            "JavaScript",
            "Implement feature work in an existing React codebase with pragmatic quality.",
            "60 minutes",
        ),
        (
            "Streaming Recording Upload Pipeline",
            "Implement multipart upload flow for large recording files.",
            "hard",
            "Full-Stack Engineer",
            "TypeScript",
            "Build resilient upload APIs and client integration for large video artifacts.",
            "120 minutes",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO questions (title, summary, difficulty, role, language, overview, estimated_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _assessment_row_to_record(row: sqlite3.Row) -> AssessmentRecord:
    return AssessmentRecord(
        id=int(row["id"]),
        title=str(row["title"]),
        role=str(row["role"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        candidate_count=int(row["candidate_count"]),
        question_id=row["question_id"],
        job_link=row["job_link"],
        job_desc=row["job_desc"],
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
                a.question_id,
                a.job_link,
                a.job_desc,
                COALESCE(COUNT(c.id), 0) AS candidate_count
            FROM assessments a
            LEFT JOIN candidates c ON c.assessment_id = a.id
            GROUP BY a.id
            ORDER BY a.created_at DESC
            """
        ).fetchall()
        return [_assessment_row_to_record(row) for row in rows]


def get_assessment(settings: Settings, assessment_id: int) -> AssessmentRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT
                a.id,
                a.title,
                a.role,
                a.status,
                a.created_at,
                a.question_id,
                a.job_link,
                a.job_desc,
                COALESCE(COUNT(c.id), 0) AS candidate_count
            FROM assessments a
            LEFT JOIN candidates c ON c.assessment_id = a.id
            WHERE a.id = ?
            GROUP BY a.id
            """,
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None
        return _assessment_row_to_record(row)


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


def list_questions(settings: Settings) -> list[QuestionRecord]:
    with _connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT id, title, summary, difficulty, role, language, overview, estimated_time
            FROM questions
            ORDER BY id ASC
            """
        ).fetchall()
        return [
            QuestionRecord(
                id=int(row["id"]),
                title=str(row["title"]),
                summary=str(row["summary"]),
                difficulty=str(row["difficulty"]),
                role=str(row["role"]),
                language=str(row["language"]),
                overview=str(row["overview"]),
                estimated_time=str(row["estimated_time"]),
            )
            for row in rows
        ]


def get_question(settings: Settings, question_id: int) -> QuestionRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT id, title, summary, difficulty, role, language, overview, estimated_time
            FROM questions
            WHERE id = ?
            """,
            (question_id,),
        ).fetchone()
        if row is None:
            return None
        return QuestionRecord(
            id=int(row["id"]),
            title=str(row["title"]),
            summary=str(row["summary"]),
            difficulty=str(row["difficulty"]),
            role=str(row["role"]),
            language=str(row["language"]),
            overview=str(row["overview"]),
            estimated_time=str(row["estimated_time"]),
        )


def assessment_title_exists(settings: Settings, title: str) -> bool:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM assessments
            WHERE lower(title) = lower(?)
            LIMIT 1
            """,
            (title.strip(),),
        ).fetchone()
        return row is not None


def create_assessment(
    settings: Settings,
    *,
    title: str,
    question_id: int,
    job_link: str | None = None,
    job_desc: str | None = None,
) -> AssessmentRecord:
    question = get_question(settings, question_id)
    if question is None:
        raise ValueError("Question not found")

    created_at = _iso_now()
    with _connect(settings) as connection:
        cursor = connection.execute(
            """
            INSERT INTO assessments (title, role, status, created_at, question_id, job_link, job_desc)
            VALUES (?, ?, 'active', ?, ?, ?, ?)
            """,
            (title.strip(), question.role, created_at, question_id, job_link or "", job_desc or ""),
        )
        assessment_id = int(cursor.lastrowid)

    created = get_assessment(settings, assessment_id)
    if created is None:
        raise RuntimeError("Failed to create assessment")
    return created
