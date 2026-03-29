import hashlib
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.services.assessment import generate_assessment_download_link
from app.services.assessment_store import (
    ReportRecord,
    get_assessment,
    get_candidate_recording_key,
    get_latest_candidate_by_assessment,
    get_latest_report_by_assessment,
    get_candidate_by_id,
    get_report_by_candidate,
    mark_candidate_submitted,
    store_recording_key,
    upsert_report,
)
from app.services.report_engine import run_scoring_and_store_report

router = APIRouter(tags=["candidate"])

_UPLOAD_SESSIONS: dict[str, dict[str, object]] = {}


def _safe_key(name: str) -> str:
    return name.replace("..", "").lstrip("/").replace("\\", "/")


def _iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, UTC).isoformat()


def _find_latest_submission(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_submissions_dir)
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.glob(f"{assessment_id}-*.zip")
        if path.is_file()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _find_latest_recording(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_recordings_dir) / "recordings"
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.glob(f"assessment-{assessment_id}-*.webm")
        if path.is_file()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _find_latest_reflection(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_recordings_dir) / "reflection" / str(assessment_id)
    if not root.exists():
        return None
    candidates = [path for path in root.rglob("*.webm") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _report_payload_from_record(
    *,
    report: ReportRecord,
    candidate_name: str | None,
    candidate_email: str,
    assessment_title: str,
    submitted_at: str,
) -> dict[str, object]:
    return {
        "id": report.candidate_id,
        "assessmentId": report.assessment_id,
        "assessmentTitle": assessment_title,
        "name": candidate_name,
        "email": candidate_email,
        "score": report.score,
        "codeQuality": report.code_quality,
        "results": report.results,
        "diffs": report.diffs,
        "codeSummaryBullets": report.code_summary_bullets,
        "reportReady": report.report_ready,
        "error": report.error,
        "assessmentType": report.assessment_type,
        "appUsage": report.app_usage,
        "totalDuration": report.total_duration,
        "submissionFile": report.submission_file,
        "assessmentRecordingKey": report.assessment_recording_key,
        "reflectionRecordingKey": report.reflection_recording_key,
        "submittedAt": submitted_at,
    }


def _init_pending_report(settings: Settings, candidate_id: int, assessment_id: int, assessment_type: str) -> None:
    upsert_report(
        settings,
        candidate_id=candidate_id,
        assessment_id=assessment_id,
        score=None,
        code_quality=None,
        results=[],
        diffs=[],
        code_summary_bullets=["Submission received. Report generation is in progress."],
        report_ready=False,
        error=None,
        assessment_type=assessment_type,
        app_usage=[],
        total_duration=None,
        submission_file=None,
        assessment_recording_key=None,
        reflection_recording_key=None,
    )


def _upload_response_payload(
    *,
    candidate_id: int | None,
    assessment_id: str,
    path: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "message": "Upload successful",
        "path": path,
        "assessmentId": assessment_id,
    }
    if candidate_id is None:
        return payload
    payload.update(
        {
            "candidateId": candidate_id,
            "reportId": candidate_id,
            "reportUrl": f"/report/{candidate_id}",
            "loadingUrl": f"/sample/loading/{candidate_id}",
            "reportReady": False,
        }
    )
    return payload


@router.get("/api/public/assessment/{assessment_id}")
def public_assessment(assessment_id: str, settings: Settings = Depends(get_settings)):
    if assessment_id == "default":
        return {"id": "default", "title": "Default Assessment"}
    try:
        numeric_id = int(assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Assessment not found") from exc
    assessment = get_assessment(settings, numeric_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"id": assessment.id, "title": assessment.title}


@router.get("/api/reflection/sections")
def reflection_sections():
    return {
        "sections": [
            {
                "id": "demo_work",
                "question": "Show us a demo of your work.",
                "requiresScreenShare": True,
                "timeLimit": 120,
            },
            {
                "id": "struggles",
                "question": "Given more time, what would you implement next?",
                "requiresScreenShare": False,
                "timeLimit": 60,
            },
        ]
    }


@router.get("/api/assessments/{assessment_id}/reflection-questions")
def reflection_questions_for_assessment(assessment_id: int):
    # Keep behavior stable for frontend: currently same shared section list for all assessments.
    return reflection_sections()


@router.post("/download-assessment")
def download_assessment(settings: Settings = Depends(get_settings)):
    return {"downloadUrl": generate_assessment_download_link(settings)}


@router.post("/get-presigned-upload-url")
def get_presigned_upload_url(
    payload: dict,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    file_name = _safe_key(str(payload.get("fileName", "upload.bin")))
    assessment_id = str(payload.get("assessmentId", "unknown"))
    section_id = str(payload.get("sectionId", "section"))
    key = _safe_key(f"reflection/{assessment_id}/{section_id}-{uuid.uuid4().hex}-{file_name}")
    base = settings.app_base_url
    return {"url": f"{base}/local-upload/{key}", "s3Key": key}


@router.put("/local-upload/{key:path}")
async def local_upload_put(key: str, request: Request, settings: Settings = Depends(get_settings)):
    safe_key = _safe_key(key)
    dest = Path(settings.local_recordings_dir) / safe_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = await request.body()
    dest.write_bytes(body)
    return JSONResponse({"ok": True})


@router.post("/notify-recording-upload")
def notify_recording_upload(payload: dict, settings: Settings = Depends(get_settings)):
    s3_key = payload.get("s3Key")
    email = payload.get("email")
    assessment_id = payload.get("assessmentId")
    recording_type = payload.get("type")
    if s3_key and email and assessment_id is not None and recording_type:
        try:
            store_recording_key(
                settings,
                email=str(email),
                assessment_id=int(assessment_id),
                s3_key=str(s3_key),
                recording_type=str(recording_type),
            )
        except (ValueError, TypeError):
            pass
    return {"ok": True, "s3Key": s3_key}


@router.post("/api/recording/start-multipart-upload")
def start_multipart_upload(payload: dict, settings: Settings = Depends(get_settings)):
    name = str(payload.get("name", "candidate"))
    assessment_id = str(payload.get("assessmentId", "unknown"))
    upload_id = uuid.uuid4().hex
    key = _safe_key(f"recordings/assessment-{assessment_id}-{name.replace(' ', '_')}-{upload_id}.webm")
    tmp_path = Path(settings.local_recordings_dir) / "tmp" / f"{upload_id}.part"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(b"")
    _UPLOAD_SESSIONS[upload_id] = {"key": key, "tmp_path": str(tmp_path), "parts": []}
    return {"uploadId": upload_id, "key": key}


@router.post("/api/recording/upload-part")
async def upload_part(request: Request):
    upload_id = request.headers.get("x-upload-id")
    part_number = request.headers.get("x-part-number")
    key = request.headers.get("x-s3-key")
    if not upload_id or not part_number or not key:
        raise HTTPException(status_code=400, detail="Missing upload headers")
    session = _UPLOAD_SESSIONS.get(upload_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Upload session not found")
    try:
        parsed_part_number = int(part_number)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid x-part-number header") from exc
    if parsed_part_number <= 0:
        raise HTTPException(status_code=400, detail="x-part-number must be a positive integer")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty part payload")
    tmp_path = Path(str(session["tmp_path"]))
    with tmp_path.open("ab") as handle:
        handle.write(body)
    etag = hashlib.md5(body).hexdigest()  # noqa: S324
    cast_parts = session["parts"]
    if isinstance(cast_parts, list):
        cast_parts.append({"ETag": etag, "PartNumber": parsed_part_number})
    return {"ETag": etag}


@router.post("/api/recording/complete-multipart-upload")
def complete_multipart_upload(payload: dict, settings: Settings = Depends(get_settings)):
    upload_id = str(payload.get("uploadId", ""))
    session = _UPLOAD_SESSIONS.get(upload_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Upload session not found")
    tmp_path = Path(str(session["tmp_path"]))
    parts = session.get("parts")
    if not isinstance(parts, list) or len(parts) == 0:
        raise HTTPException(status_code=400, detail="No uploaded parts found for this upload session")
    if not tmp_path.exists():
        raise HTTPException(status_code=404, detail="Upload payload not found")
    if tmp_path.stat().st_size <= 0:
        raise HTTPException(status_code=400, detail="Upload payload is empty")
    key = _safe_key(str(session["key"]))
    dest = Path(settings.local_recordings_dir) / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp_path, dest)
    _UPLOAD_SESSIONS.pop(upload_id, None)
    return {"message": "Upload complete", "s3Key": key}


@router.post("/api/recording/abort-upload")
def abort_upload(payload: dict):
    upload_id = str(payload.get("uploadId", ""))
    session = _UPLOAD_SESSIONS.pop(upload_id, None)
    if session is None:
        return {"message": "Upload already missing"}
    tmp_path = Path(str(session["tmp_path"]))
    if tmp_path.exists():
        tmp_path.unlink()
    return {"message": "Upload aborted"}


@router.post("/upload-zip")
async def upload_zip(
    background_tasks: BackgroundTasks,
    zipFile: UploadFile | None = File(default=None),
    assessmentId: str = Form("default"),
    name: str = Form(""),
    email: str = Form(""),
    settings: Settings = Depends(get_settings),
):
    dest_name = None
    if zipFile is not None:
        original_name = zipFile.filename or "submission.zip"
        if not original_name.lower().endswith(".zip"):
            original_name = f"{original_name}.zip"
        file_name = f"{assessmentId}-{uuid.uuid4().hex}-{original_name}"
        dest = Path(settings.local_submissions_dir) / _safe_key(file_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = await zipFile.read()
        dest.write_bytes(data)
        dest_name = dest.name
    candidate = None
    try:
        assessment_numeric = int(assessmentId)
        if email:
            candidate = mark_candidate_submitted(
                settings,
                assessment_id=assessment_numeric,
                email=email,
                name=name or None,
            )
            assessment = get_assessment(settings, assessment_numeric)
            assessment_type = assessment.assessment_type if assessment is not None else "default"
            _init_pending_report(settings, candidate.id, assessment_numeric, assessment_type)
    except ValueError:
        pass
    if candidate is not None:
        background_tasks.add_task(run_scoring_and_store_report, settings, candidate)
    return _upload_response_payload(
        candidate_id=candidate.id if candidate is not None else None,
        assessment_id=assessmentId,
        path=dest_name,
    )


@router.post("/upload-assessment4")
async def upload_assessment4(
    background_tasks: BackgroundTasks,
    submissionZip: UploadFile | None = File(default=None),
    notebookFile: UploadFile | None = File(default=None),
    assessmentId: str = Form("default"),
    name: str = Form(""),
    email: str = Form(""),
    settings: Settings = Depends(get_settings),
):
    if submissionZip is None:
        raise HTTPException(status_code=400, detail="submissionZip is required")
    if notebookFile is None:
        raise HTTPException(status_code=400, detail="notebookFile is required")

    upload_token = uuid.uuid4().hex
    zip_name = submissionZip.filename or "submission.zip"
    if not zip_name.lower().endswith(".zip"):
        zip_name = f"{zip_name}.zip"
    zip_dest_name = f"{assessmentId}-{upload_token}-{zip_name}"
    zip_dest = Path(settings.local_submissions_dir) / _safe_key(zip_dest_name)
    zip_dest.parent.mkdir(parents=True, exist_ok=True)
    zip_dest.write_bytes(await submissionZip.read())

    notebook_name = notebookFile.filename or "notebook.ipynb"
    if not notebook_name.lower().endswith(".ipynb"):
        notebook_name = f"{notebook_name}.ipynb"
    notebook_dest_name = f"{assessmentId}-{upload_token}-{notebook_name}"
    notebook_dest = Path(settings.local_submissions_dir) / _safe_key(notebook_dest_name)
    notebook_dest.write_bytes(await notebookFile.read())

    candidate = None
    try:
        assessment_numeric = int(assessmentId)
        if email:
            candidate = mark_candidate_submitted(
                settings,
                assessment_id=assessment_numeric,
                email=email,
                name=name or None,
            )
            assessment = get_assessment(settings, assessment_numeric)
            assessment_type = assessment.assessment_type if assessment is not None else "assessment4-ner"
            _init_pending_report(settings, candidate.id, assessment_numeric, assessment_type)
    except ValueError:
        pass

    if candidate is not None:
        background_tasks.add_task(run_scoring_and_store_report, settings, candidate)

    return _upload_response_payload(
        candidate_id=candidate.id if candidate is not None else None,
        assessment_id=assessmentId,
        path=zip_dest_name,
    )


@router.get("/report/{candidate_id}")
def report(candidate_id: int, settings: Settings = Depends(get_settings)):
    candidate = get_candidate_by_id(settings, candidate_id)
    report_record = None
    if candidate is not None:
        report_record = get_report_by_candidate(settings, candidate.id)

    if candidate is None:
        # Compatibility mode: allow /report/{assessmentId} and resolve latest candidate.
        candidate = get_latest_candidate_by_assessment(settings, candidate_id)
        report_record = get_latest_report_by_assessment(settings, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Report not found")

    assessment = get_assessment(settings, candidate.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if report_record is not None:
        return _report_payload_from_record(
            report=report_record,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            assessment_title=assessment.title,
            submitted_at=candidate.invited_at,
        )

    submission = _find_latest_submission(settings, candidate.assessment_id)
    assessment_recording = _find_latest_recording(settings, candidate.assessment_id)
    reflection_recording = _find_latest_reflection(settings, candidate.assessment_id)

    has_submission = submission is not None
    has_assessment_recording = assessment_recording is not None
    has_reflection_recording = reflection_recording is not None
    submission_relative = (
        str(submission.relative_to(Path(settings.local_submissions_dir))) if submission else None
    )
    assessment_recording_relative = (
        str(assessment_recording.relative_to(Path(settings.local_recordings_dir)))
        if assessment_recording
        else None
    )
    reflection_recording_relative = (
        str(reflection_recording.relative_to(Path(settings.local_recordings_dir)))
        if reflection_recording
        else None
    )

    if candidate.status == "submitted":
        report_ready = False
        score = None
        code_quality = None
        error = "Report is being generated. Please refresh in a moment."
    else:
        report_ready = False
        score = None
        code_quality = None
        error = "Candidate has not submitted yet."

    results = [
        {
            "name": "Submission ZIP received",
            "status": "pass" if has_submission else "fail",
            "expected": "Upload a valid .zip project archive",
            "output": (
                f"Found {submission.name} ({submission.stat().st_size} bytes)"
                if submission
                else "No submission archive found"
            ),
        },
        {
            "name": "Workflow recording",
            "status": "pass" if has_assessment_recording else "partial",
            "expected": "Upload full-screen assessment workflow recording",
            "output": (
                f"Found {assessment_recording.name}"
                if assessment_recording
                else "No main workflow recording found"
            ),
        },
        {
            "name": "Reflection recording",
            "status": "pass" if has_reflection_recording else "partial",
            "expected": "Upload reflection response recording(s)",
            "output": (
                f"Found {reflection_recording.name}"
                if reflection_recording
                else "No reflection recording found"
            ),
        },
    ]

    summary_bullets = [
        "Submission received and linked to candidate record.",
        "Background evaluator is generating this report.",
        "Refresh this page in a few moments.",
    ]
    if submission:
        summary_bullets.append(f"Latest submission captured at {_iso_utc(submission.stat().st_mtime)}.")

    return {
        "id": candidate.id,
        "assessmentId": candidate.assessment_id,
        "assessmentTitle": assessment.title,
        "name": candidate.name,
        "email": candidate.email,
        "score": score,
        "codeQuality": code_quality,
        "results": results,
        "diffs": [],
        "codeSummaryBullets": summary_bullets,
        "reportReady": report_ready,
        "error": error,
        "assessmentType": assessment.assessment_type,
        "appUsage": [],
        "totalDuration": None,
        "submissionFile": submission_relative,
        "assessmentRecordingKey": assessment_recording_relative,
        "reflectionRecordingKey": reflection_recording_relative,
        "submittedAt": candidate.invited_at,
    }
