import hashlib
import os
import secrets
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import Settings, get_settings
from app.services.assessment import generate_assessment_download_link
from app.services.assessment_store import (
    ReportRecord,
    get_assessment,
    get_default_assessment,
    get_question,
    get_latest_candidate_by_assessment,
    list_reflection_uploads_for_candidate,
    get_latest_report_by_assessment,
    get_candidate_by_id,
    get_report_by_candidate,
    mark_candidate_submitted,
    question_to_payload,
    record_reflection_upload,
    upsert_report,
)
from app.services.invite_store import get_invite_by_token
from app.services.report_engine import run_scoring_and_store_report

router = APIRouter(tags=["candidate"])

_UPLOAD_SESSIONS: dict[str, dict[str, object]] = {}
_UPLOAD_SESSION_TTL_SECONDS = 60 * 60
_LOCAL_UPLOAD_TOKENS: dict[str, dict[str, object]] = {}
_LOCAL_UPLOAD_TOKEN_TTL_SECONDS = 15 * 60
_LOCAL_UPLOAD_MAX_BYTES = 250 * 1024 * 1024


def _drop_upload_session(upload_id: str) -> None:
    session = _UPLOAD_SESSIONS.pop(upload_id, None)
    if session is None:
        return
    tmp_path = Path(str(session.get("tmp_path", "")))
    if tmp_path.is_file():
        try:
            tmp_path.unlink()
        except OSError:
            pass


def _prune_expired_upload_sessions() -> None:
    now = time.monotonic()
    expired = [
        upload_id
        for upload_id, session in _UPLOAD_SESSIONS.items()
        if now - float(session.get("created_at", now)) > _UPLOAD_SESSION_TTL_SECONDS
    ]
    for upload_id in expired:
        _drop_upload_session(upload_id)


def _safe_key(name: str) -> str:
    return name.replace("..", "").replace("\\", "/").lstrip("/")


def _recordings_destination(settings: Settings, key: str) -> Path:
    safe_key = _safe_key(key)
    if not safe_key:
        raise HTTPException(status_code=400, detail="Missing upload key")
    root = Path(settings.local_recordings_dir).resolve()
    dest = (root / safe_key).resolve()
    try:
        dest.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid upload key") from exc
    return dest


def _prune_local_upload_tokens() -> None:
    now = time.monotonic()
    expired = [
        token
        for token, session in _LOCAL_UPLOAD_TOKENS.items()
        if now > float(session.get("expires_at", 0))
    ]
    for token in expired:
        _LOCAL_UPLOAD_TOKENS.pop(token, None)


def _issue_local_upload_token(key: str) -> str:
    _prune_local_upload_tokens()
    token = secrets.token_urlsafe(32)
    _LOCAL_UPLOAD_TOKENS[token] = {
        "key": _safe_key(key),
        "expires_at": time.monotonic() + _LOCAL_UPLOAD_TOKEN_TTL_SECONDS,
    }
    return token


def _consume_local_upload_token(token: str | None, key: str) -> None:
    _prune_local_upload_tokens()
    if not token:
        raise HTTPException(status_code=403, detail="Missing upload token")
    session = _LOCAL_UPLOAD_TOKENS.pop(token, None)
    if session is None:
        raise HTTPException(status_code=403, detail="Invalid or expired upload token")
    if session.get("key") != _safe_key(key):
        raise HTTPException(status_code=403, detail="Upload token does not match key")


def _resolve_assessment_id(raw_assessment_id: object, settings: Settings) -> int:
    raw = str(raw_assessment_id or "").strip()
    if not raw or raw == "default":
        assessment = get_default_assessment(settings)
        if assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")
        return assessment.id
    try:
        assessment_id = int(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid assessmentId") from exc
    if get_assessment(settings, assessment_id) is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment_id


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


def _submission_path(settings: Settings, key: str | None) -> Path | None:
    if not key:
        return None
    root = Path(settings.local_submissions_dir).resolve()
    path = (root / _safe_key(key)).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.is_file() else None


def _recording_path(settings: Settings, key: str | None) -> Path | None:
    if not key:
        return None
    root = Path(settings.local_recordings_dir).resolve()
    path = (root / _safe_key(key)).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if _is_playable_recording(path) else None


def _is_playable_recording(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _find_latest_recording(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_recordings_dir) / "recordings"
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.glob(f"assessment-{assessment_id}-*.webm")
        if _is_playable_recording(path)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _find_reflections(settings: Settings, assessment_id: int, email: str) -> list[Path]:
    uploads = list_reflection_uploads_for_candidate(
        settings,
        assessment_id=assessment_id,
        email=email,
    )
    reflections: list[Path] = []
    for upload in uploads:
        candidate_reflection = _recording_path(settings, str(upload.get("s3Key") or ""))
        if candidate_reflection is not None:
            reflections.append(candidate_reflection)
    if reflections:
        return reflections

    root = Path(settings.local_recordings_dir) / "reflection" / str(assessment_id)
    if not root.exists():
        return []

    # Legacy fallback (before reflection uploads were candidate-attributed):
    # only return a recording when the folder is unambiguous.
    candidates = [path for path in root.rglob("*.webm") if _is_playable_recording(path)]
    if len(candidates) != 1:
        return []
    return candidates


def _find_latest_reflection(settings: Settings, assessment_id: int, email: str) -> Path | None:
    reflections = _find_reflections(settings, assessment_id, email)
    return reflections[-1] if reflections else None


def _reflection_payload_for_candidate(settings: Settings, candidate_id: int, assessment_id: int, email: str) -> list[dict[str, object]]:
    uploads = list_reflection_uploads_for_candidate(
        settings,
        assessment_id=assessment_id,
        email=email,
    )
    payload: list[dict[str, object]] = []
    for upload in uploads:
        key = str(upload.get("s3Key") or "")
        path = _recording_path(settings, key)
        if not key or path is None:
            continue
        payload.append(
            {
                "sectionId": upload.get("sectionId"),
                "s3Key": str(path.relative_to(Path(settings.local_recordings_dir).resolve())),
                "uploadedAt": upload.get("uploadedAt"),
                "videoUrl": f"/api/artifacts/recordings/{candidate_id}/reflection/{len(payload)}",
            }
        )
    return payload


def _report_payload_from_record(
    *,
    report: ReportRecord,
    candidate_name: str | None,
    candidate_email: str,
    assessment_title: str,
    submitted_at: str,
) -> dict[str, object]:
    payload = dict(report.payload or {})
    payload.update({
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
        "status": "ready" if report.report_ready and not report.error else "failed" if report.error else "processing",
    })
    payload["submissionDownloadUrl"] = f"/api/artifacts/submissions/{report.candidate_id}"
    if report.assessment_recording_key:
        payload["assessmentVideoUrl"] = f"/api/artifacts/recordings/{report.candidate_id}/assessment"
    reflection_recordings = payload.get("reflectionRecordings")
    if not isinstance(reflection_recordings, list):
        reflection_recordings = []
    if not reflection_recordings and report.reflection_recording_key:
        reflection_recordings = [{"sectionId": None, "s3Key": report.reflection_recording_key}]
    normalized_reflections: list[dict[str, object]] = []
    for index, reflection in enumerate(reflection_recordings):
        if not isinstance(reflection, dict):
            continue
        item = dict(reflection)
        item["videoUrl"] = f"/api/artifacts/recordings/{report.candidate_id}/reflection/{index}"
        normalized_reflections.append(item)
    payload["reflectionRecordings"] = normalized_reflections
    payload["reflectionVideoUrls"] = [item["videoUrl"] for item in normalized_reflections]
    if report.reflection_recording_key:
        payload["reflectionVideoUrl"] = f"/api/artifacts/recordings/{report.candidate_id}/reflection"
    return payload


def _init_pending_report(
    settings: Settings,
    candidate_id: int,
    assessment_id: int,
    assessment_type: str,
    *,
    submission_file: str | None = None,
) -> None:
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
        submission_file=submission_file,
        assessment_recording_key=None,
        reflection_recording_key=None,
        payload={
            "id": candidate_id,
            "assessmentId": assessment_id,
            "score": None,
            "codeQuality": None,
            "results": [],
            "diffs": [],
            "codeSummaryBullets": ["Submission received. Report generation is in progress."],
            "reportReady": False,
            "status": "processing",
            "error": None,
            "assessmentType": assessment_type,
            "appUsage": [],
            "totalDuration": None,
            "submissionFile": submission_file,
        },
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
        assessment = get_default_assessment(settings)
        if assessment is None:
            return {"id": "default", "title": "Default Assessment"}
        return {"id": assessment.id, "title": assessment.title}
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
    invite_token = str(payload.get("inviteToken", "")).strip()
    assessment_id = _resolve_assessment_id(payload.get("assessmentId"), settings)
    invite = get_invite_by_token(invite_token, settings)
    if (
        invite is None
        or (invite.assessment_id is not None and invite.assessment_id != assessment_id)
        or invite.status not in {"invited", "resent", "taken"}
    ):
        raise HTTPException(status_code=403, detail="Invalid invite token")

    section_id = _safe_key(str(payload.get("sectionId", "section")))
    key = _safe_key(f"reflection/{assessment_id}/{section_id}-{uuid.uuid4().hex}-{file_name}")
    _recordings_destination(settings, key)
    upload_token = _issue_local_upload_token(key)
    base = settings.app_base_url
    return {"url": f"{base}/local-upload/{key}?token={upload_token}", "s3Key": key}


@router.put("/local-upload/{key:path}")
async def local_upload_put(key: str, request: Request, settings: Settings = Depends(get_settings)):
    safe_key = _safe_key(key)
    _consume_local_upload_token(request.query_params.get("token"), safe_key)
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > _LOCAL_UPLOAD_MAX_BYTES:
                raise HTTPException(status_code=413, detail="Upload too large")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid content-length") from exc
    dest = _recordings_destination(settings, safe_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = await request.body()
    if len(body) == 0:
        raise HTTPException(status_code=400, detail="Upload is empty")
    if len(body) > _LOCAL_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Upload too large")
    dest.write_bytes(body)
    return JSONResponse({"ok": True})


@router.post("/notify-recording-upload")
def notify_recording_upload(payload: dict, settings: Settings = Depends(get_settings)):
    upload_type = str(payload.get("type", "")).strip().lower()
    if upload_type == "reflection":
        s3_key = str(payload.get("s3Key", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        raw_assessment_id = payload.get("assessmentId")
        section_id = payload.get("sectionId")
        if not s3_key or not email:
            raise HTTPException(status_code=400, detail="Missing reflection upload metadata")
        assessment_id = _resolve_assessment_id(raw_assessment_id, settings)
        record_reflection_upload(
            settings,
            assessment_id=assessment_id,
            email=email,
            section_id=str(section_id) if section_id is not None else None,
            s3_key=_safe_key(s3_key),
        )

    # Keep endpoint response stable for frontend callers.
    return {"ok": True, "s3Key": payload.get("s3Key")}


@router.post("/api/recording/start-multipart-upload")
def start_multipart_upload(payload: dict, settings: Settings = Depends(get_settings)):
    _prune_expired_upload_sessions()
    name = str(payload.get("name", "candidate"))
    assessment_id = str(payload.get("assessmentId", "unknown"))
    upload_id = uuid.uuid4().hex
    key = _safe_key(f"recordings/assessment-{assessment_id}-{name.replace(' ', '_')}-{upload_id}.webm")
    tmp_path = Path(settings.local_recordings_dir) / "tmp" / f"{upload_id}.part"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(b"")
    _UPLOAD_SESSIONS[upload_id] = {
        "key": key,
        "tmp_path": str(tmp_path),
        "parts": [],
        "created_at": time.monotonic(),
    }
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
    if time.monotonic() - float(session.get("created_at", time.monotonic())) > _UPLOAD_SESSION_TTL_SECONDS:
        _drop_upload_session(upload_id)
        raise HTTPException(status_code=410, detail="Upload session expired")
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
    if time.monotonic() - float(session.get("created_at", time.monotonic())) > _UPLOAD_SESSION_TTL_SECONDS:
        _drop_upload_session(upload_id)
        raise HTTPException(status_code=410, detail="Upload session expired")
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
        assessment = get_assessment(settings, assessment_numeric)
        if email and assessment is not None:
            candidate = mark_candidate_submitted(
                settings,
                assessment_id=assessment_numeric,
                email=email,
                name=name or None,
            )
            _init_pending_report(
                settings,
                candidate.id,
                assessment_numeric,
                assessment.assessment_type,
                submission_file=dest_name,
            )
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
        assessment = get_assessment(settings, assessment_numeric)
        if email and assessment is not None:
            candidate = mark_candidate_submitted(
                settings,
                assessment_id=assessment_numeric,
                email=email,
                name=name or None,
            )
            _init_pending_report(
                settings,
                candidate.id,
                assessment_numeric,
                assessment.assessment_type,
                submission_file=zip_dest_name,
            )
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
    question = get_question(settings, assessment.question_id) if assessment.question_id else None
    question_payload = question_to_payload(question)

    if report_record is not None:
        payload = _report_payload_from_record(
            report=report_record,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            assessment_title=assessment.title,
            submitted_at=candidate.invited_at,
        )
        payload.setdefault("questionData", question_payload)
        reflection_payload = _reflection_payload_for_candidate(
            settings,
            candidate.id,
            candidate.assessment_id,
            candidate.email,
        )
        if reflection_payload:
            payload["reflectionRecordings"] = reflection_payload
            payload["reflectionVideoUrls"] = [item["videoUrl"] for item in reflection_payload]
        return payload

    submission = _find_latest_submission(settings, candidate.assessment_id)
    assessment_recording = _find_latest_recording(settings, candidate.assessment_id)
    reflection_recordings = _find_reflections(settings, candidate.assessment_id, candidate.email)
    reflection_recording = reflection_recordings[-1] if reflection_recordings else None

    has_submission = submission is not None
    has_assessment_recording = assessment_recording is not None
    has_reflection_recording = bool(reflection_recordings)
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
            "name": "Reflection recordings",
            "status": "pass" if has_reflection_recording else "partial",
            "expected": "Upload reflection response recording(s)",
            "output": (
                f"{len(reflection_recordings)} reflection recording(s) found"
                if reflection_recordings
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
        "reflectionRecordings": _reflection_payload_for_candidate(
            settings,
            candidate.id,
            candidate.assessment_id,
            candidate.email,
        ),
        "submittedAt": candidate.invited_at,
        "status": "processing" if candidate.status == "submitted" else "pending",
        "questionData": question_payload,
        "submissionDownloadUrl": f"/api/artifacts/submissions/{candidate.id}",
    }


@router.post("/download-submission")
def download_submission(payload: dict, settings: Settings = Depends(get_settings)):
    raw_candidate_id = payload.get("candidateId") or payload.get("assessmentId")
    try:
        candidate_id = int(str(raw_candidate_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Missing candidateId") from exc
    candidate = get_candidate_by_id(settings, candidate_id)
    report_record = get_report_by_candidate(settings, candidate_id)
    if candidate is None or report_record is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission = _submission_path(settings, report_record.submission_file)
    if submission is None:
        submission = _find_latest_submission(settings, candidate.assessment_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"downloadUrl": f"/api/artifacts/submissions/{candidate_id}"}


@router.get("/api/artifacts/submissions/{candidate_id}")
def download_submission_artifact(candidate_id: int, settings: Settings = Depends(get_settings)):
    candidate = get_candidate_by_id(settings, candidate_id)
    report_record = get_report_by_candidate(settings, candidate_id)
    if candidate is None or report_record is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission = _submission_path(settings, report_record.submission_file)
    if submission is None:
        submission = _find_latest_submission(settings, candidate.assessment_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    safe_name = (candidate.name or "candidate").replace("/", "_").replace("\\", "_").strip() or "candidate"
    return FileResponse(
        submission,
        media_type="application/zip",
        filename=f"{safe_name}_submission.zip",
    )


@router.get("/api/artifacts/recordings/{candidate_id}/reflection/{index}")
def reflection_recording_artifact(candidate_id: int, index: int, settings: Settings = Depends(get_settings)):
    candidate = get_candidate_by_id(settings, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    recordings = _find_reflections(settings, candidate.assessment_id, candidate.email)
    if index < 0 or index >= len(recordings):
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(recordings[index], media_type="video/webm")


@router.get("/api/artifacts/recordings/{candidate_id}/{kind}")
def recording_artifact(candidate_id: int, kind: str, settings: Settings = Depends(get_settings)):
    candidate = get_candidate_by_id(settings, candidate_id)
    report_record = get_report_by_candidate(settings, candidate_id)
    if candidate is None or report_record is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    if kind == "assessment":
        recording = _recording_path(settings, report_record.assessment_recording_key)
        if recording is None:
            recording = _find_latest_recording(settings, candidate.assessment_id)
    elif kind == "reflection":
        reflection_recordings = _find_reflections(settings, candidate.assessment_id, candidate.email)
        recording = reflection_recordings[-1] if reflection_recordings else None
        if recording is None:
            recording = _recording_path(settings, report_record.reflection_recording_key)
        if recording is None:
            recording = _find_latest_reflection(settings, candidate.assessment_id, candidate.email)
    else:
        raise HTTPException(status_code=404, detail="Recording not found")
    if recording is None:
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(recording, media_type="video/webm")
