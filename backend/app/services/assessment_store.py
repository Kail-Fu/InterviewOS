import json
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
    assessment_type: str


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
    assessment_type: str


@dataclass
class ReportRecord:
    candidate_id: int
    assessment_id: int
    score: int | None
    code_quality: int | None
    results: list[dict[str, object]]
    diffs: list[dict[str, object]]
    code_summary_bullets: list[str]
    report_ready: bool
    error: str | None
    assessment_type: str
    app_usage: list[dict[str, object]]
    total_duration: int | None
    submission_file: str | None
    assessment_recording_key: str | None
    reflection_recording_key: str | None
    updated_at: str


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
                job_desc TEXT,
                assessment_type TEXT NOT NULL DEFAULT 'default'
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
                estimated_time TEXT NOT NULL,
                assessment_type TEXT NOT NULL DEFAULT 'default'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                candidate_id INTEGER PRIMARY KEY,
                assessment_id INTEGER NOT NULL,
                score INTEGER,
                code_quality INTEGER,
                results_json TEXT NOT NULL DEFAULT '[]',
                diffs_json TEXT NOT NULL DEFAULT '[]',
                code_summary_json TEXT NOT NULL DEFAULT '[]',
                report_ready INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                assessment_type TEXT NOT NULL DEFAULT 'default',
                app_usage_json TEXT NOT NULL DEFAULT '[]',
                total_duration INTEGER,
                submission_file TEXT,
                assessment_recording_key TEXT,
                reflection_recording_key TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            )
            """
        )

        _ensure_column(connection, "assessments", "question_id", "INTEGER")
        _ensure_column(connection, "assessments", "job_link", "TEXT")
        _ensure_column(connection, "assessments", "job_desc", "TEXT")
        _ensure_column(connection, "assessments", "assessment_type", "TEXT NOT NULL DEFAULT 'default'")
        _ensure_column(connection, "questions", "assessment_type", "TEXT NOT NULL DEFAULT 'default'")

        _seed_questions(connection)
        _seed_demo_rows(connection)


def _seed_demo_rows(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT COUNT(*) AS count FROM assessments").fetchone()
    if existing is not None and int(existing["count"]) > 0:
        return

    created_at = _iso_now()
    cursor = connection.execute(
        """
        INSERT INTO assessments (title, role, status, created_at, assessment_type)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Backend API Work Simulation", "Backend Engineer", "active", created_at, "default"),
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
    rows = [
        (
            "Users API",
            "Build/debug API behavior and endpoint logic in a realistic backend service.",
            "medium",
            "Backend Engineer",
            "JavaScript",
            "Focus on API correctness, edge-case handling, and implementation quality.",
            "90 minutes",
            "default",
        ),
        (
            "Supreme Court Q&A RAG System",
            "Build a retrieval-augmented generation workflow and pass functional checks.",
            "hard",
            "Backend Engineer",
            "Python",
            "Implement ingestion, retrieval, and answer generation for legal-style queries.",
            "120 minutes",
            "assessment3-rag",
        ),
        (
            "Named Entity Recognition (NER) - Product Attributes",
            "Train and evaluate a NER model and submit notebook artifacts.",
            "hard",
            "ML Engineer",
            "Python",
            "Fine-tune a NER pipeline, evaluate ID/OOD performance, and explain tradeoffs.",
            "120 minutes",
            "assessment4-ner",
        ),
        (
            "Insurance Document Processor - LlamaIndex API",
            "Extract structured JSON from documents and compare against expected outputs.",
            "medium",
            "Backend Engineer",
            "Python",
            "Implement deterministic extraction and schema-consistent responses.",
            "90 minutes",
            "json-comparison",
        ),
    ]
    for row in rows:
        exists = connection.execute(
            "SELECT 1 FROM questions WHERE lower(title) = lower(?) LIMIT 1",
            (row[0],),
        ).fetchone()
        if exists is not None:
            continue
        connection.execute(
            """
            INSERT INTO questions (title, summary, difficulty, role, language, overview, estimated_time, assessment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
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
        assessment_type=str(row["assessment_type"] or "default"),
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
                a.assessment_type,
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
                a.assessment_type,
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


def add_or_update_candidate(
    settings: Settings,
    *,
    assessment_id: int,
    email: str,
    name: str | None,
    status: str,
) -> CandidateRecord:
    normalized_email = email.strip().lower()
    invited_at = _iso_now()
    with _connect(settings) as connection:
        existing = connection.execute(
            """
            SELECT id, assessment_id, email, name, status, invited_at
            FROM candidates
            WHERE assessment_id = ? AND lower(email) = lower(?)
            LIMIT 1
            """,
            (assessment_id, normalized_email),
        ).fetchone()

        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO candidates (assessment_id, email, name, status, invited_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (assessment_id, normalized_email, (name or "").strip() or None, status, invited_at),
            )
            candidate_id = int(cursor.lastrowid)
        else:
            candidate_id = int(existing["id"])
            connection.execute(
                """
                UPDATE candidates
                SET name = COALESCE(NULLIF(?, ''), name),
                    status = ?,
                    invited_at = ?
                WHERE id = ?
                """,
                ((name or "").strip(), status, invited_at, candidate_id),
            )

        row = connection.execute(
            "SELECT id, assessment_id, email, name, status, invited_at FROM candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert candidate")
        return CandidateRecord(
            id=int(row["id"]),
            assessment_id=int(row["assessment_id"]),
            email=str(row["email"]),
            name=row["name"],
            status=str(row["status"]),
            invited_at=str(row["invited_at"]),
        )


def get_candidate_by_id(settings: Settings, candidate_id: int) -> CandidateRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT id, assessment_id, email, name, status, invited_at
            FROM candidates
            WHERE id = ?
            """,
            (candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return CandidateRecord(
            id=int(row["id"]),
            assessment_id=int(row["assessment_id"]),
            email=str(row["email"]),
            name=row["name"],
            status=str(row["status"]),
            invited_at=str(row["invited_at"]),
        )


def get_candidate_by_assessment_and_email(
    settings: Settings, *, assessment_id: int, email: str
) -> CandidateRecord | None:
    normalized_email = email.strip().lower()
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT id, assessment_id, email, name, status, invited_at
            FROM candidates
            WHERE assessment_id = ? AND lower(email) = lower(?)
            LIMIT 1
            """,
            (assessment_id, normalized_email),
        ).fetchone()
        if row is None:
            return None
        return CandidateRecord(
            id=int(row["id"]),
            assessment_id=int(row["assessment_id"]),
            email=str(row["email"]),
            name=row["name"],
            status=str(row["status"]),
            invited_at=str(row["invited_at"]),
        )


def get_latest_candidate_by_assessment(settings: Settings, assessment_id: int) -> CandidateRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT id, assessment_id, email, name, status, invited_at
            FROM candidates
            WHERE assessment_id = ?
            ORDER BY invited_at DESC
            LIMIT 1
            """,
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None
        return CandidateRecord(
            id=int(row["id"]),
            assessment_id=int(row["assessment_id"]),
            email=str(row["email"]),
            name=row["name"],
            status=str(row["status"]),
            invited_at=str(row["invited_at"]),
        )


def mark_candidate_submitted(
    settings: Settings,
    *,
    assessment_id: int,
    email: str,
    name: str | None = None,
) -> CandidateRecord:
    return add_or_update_candidate(
        settings,
        assessment_id=assessment_id,
        email=email,
        name=name,
        status="submitted",
    )


def list_questions(settings: Settings) -> list[QuestionRecord]:
    with _connect(settings) as connection:
        rows = connection.execute(
            """
            SELECT id, title, summary, difficulty, role, language, overview, estimated_time, assessment_type
            FROM questions
            WHERE lower(title) IN (
                'users api',
                'supreme court q&a rag system',
                'named entity recognition (ner) - product attributes',
                'insurance document processor - llamaindex api'
            )
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
                assessment_type=str(row["assessment_type"] or "default"),
            )
            for row in rows
        ]


def get_question(settings: Settings, question_id: int) -> QuestionRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT id, title, summary, difficulty, role, language, overview, estimated_time, assessment_type
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
            assessment_type=str(row["assessment_type"] or "default"),
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
            INSERT INTO assessments (title, role, status, created_at, question_id, job_link, job_desc, assessment_type)
            VALUES (?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            (
                title.strip(),
                question.role,
                created_at,
                question_id,
                job_link or "",
                job_desc or "",
                question.assessment_type or "default",
            ),
        )
        assessment_id = int(cursor.lastrowid)

    created = get_assessment(settings, assessment_id)
    if created is None:
        raise RuntimeError("Failed to create assessment")
    return created


def _row_to_report_record(row: sqlite3.Row) -> ReportRecord:
    return ReportRecord(
        candidate_id=int(row["candidate_id"]),
        assessment_id=int(row["assessment_id"]),
        score=row["score"],
        code_quality=row["code_quality"],
        results=json.loads(row["results_json"] or "[]"),
        diffs=json.loads(row["diffs_json"] or "[]"),
        code_summary_bullets=json.loads(row["code_summary_json"] or "[]"),
        report_ready=bool(int(row["report_ready"])),
        error=row["error"],
        assessment_type=str(row["assessment_type"] or "default"),
        app_usage=json.loads(row["app_usage_json"] or "[]"),
        total_duration=row["total_duration"],
        submission_file=row["submission_file"],
        assessment_recording_key=row["assessment_recording_key"],
        reflection_recording_key=row["reflection_recording_key"],
        updated_at=str(row["updated_at"]),
    )


def upsert_report(
    settings: Settings,
    *,
    candidate_id: int,
    assessment_id: int,
    score: int | None,
    code_quality: int | None,
    results: list[dict[str, object]],
    diffs: list[dict[str, object]],
    code_summary_bullets: list[str],
    report_ready: bool,
    error: str | None,
    assessment_type: str,
    app_usage: list[dict[str, object]],
    total_duration: int | None,
    submission_file: str | None,
    assessment_recording_key: str | None,
    reflection_recording_key: str | None,
) -> ReportRecord:
    now = _iso_now()
    with _connect(settings) as connection:
        connection.execute(
            """
            INSERT INTO reports (
                candidate_id, assessment_id, score, code_quality, results_json, diffs_json, code_summary_json,
                report_ready, error, assessment_type, app_usage_json, total_duration, submission_file,
                assessment_recording_key, reflection_recording_key, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(candidate_id) DO UPDATE SET
                assessment_id = excluded.assessment_id,
                score = excluded.score,
                code_quality = excluded.code_quality,
                results_json = excluded.results_json,
                diffs_json = excluded.diffs_json,
                code_summary_json = excluded.code_summary_json,
                report_ready = excluded.report_ready,
                error = excluded.error,
                assessment_type = excluded.assessment_type,
                app_usage_json = excluded.app_usage_json,
                total_duration = excluded.total_duration,
                submission_file = excluded.submission_file,
                assessment_recording_key = excluded.assessment_recording_key,
                reflection_recording_key = excluded.reflection_recording_key,
                updated_at = excluded.updated_at
            """,
            (
                candidate_id,
                assessment_id,
                score,
                code_quality,
                json.dumps(results),
                json.dumps(diffs),
                json.dumps(code_summary_bullets),
                1 if report_ready else 0,
                error,
                assessment_type,
                json.dumps(app_usage),
                total_duration,
                submission_file,
                assessment_recording_key,
                reflection_recording_key,
                now,
            ),
        )
        row = connection.execute(
            "SELECT * FROM reports WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert report")
        return _row_to_report_record(row)


def get_report_by_candidate(settings: Settings, candidate_id: int) -> ReportRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            "SELECT * FROM reports WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_report_record(row)


def get_latest_report_by_assessment(settings: Settings, assessment_id: int) -> ReportRecord | None:
    with _connect(settings) as connection:
        row = connection.execute(
            """
            SELECT * FROM reports
            WHERE assessment_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (assessment_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_report_record(row)
