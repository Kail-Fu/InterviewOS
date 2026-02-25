import hashlib
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.services.assessment import generate_assessment_download_link
from app.services.assessment_store import get_assessment, mark_candidate_submitted

router = APIRouter(tags=["candidate"])

_UPLOAD_SESSIONS: dict[str, dict[str, object]] = {}


def _safe_key(name: str) -> str:
    return name.replace("..", "").lstrip("/").replace("\\", "/")


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
    # Keep endpoint for compatibility; upload is already persisted by /local-upload.
    return {"ok": True, "s3Key": payload.get("s3Key")}


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
    body = await request.body()
    tmp_path = Path(str(session["tmp_path"]))
    with tmp_path.open("ab") as handle:
        handle.write(body)
    etag = hashlib.md5(body).hexdigest()  # noqa: S324
    cast_parts = session["parts"]
    if isinstance(cast_parts, list):
        cast_parts.append({"ETag": etag, "PartNumber": int(part_number)})
    return {"ETag": etag}


@router.post("/api/recording/complete-multipart-upload")
def complete_multipart_upload(payload: dict, settings: Settings = Depends(get_settings)):
    upload_id = str(payload.get("uploadId", ""))
    session = _UPLOAD_SESSIONS.get(upload_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Upload session not found")
    tmp_path = Path(str(session["tmp_path"]))
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
    zipFile: UploadFile | None = File(default=None),
    assessmentId: str = Form("default"),
    name: str = Form(""),
    email: str = Form(""),
    settings: Settings = Depends(get_settings),
):
    dest_name = None
    if zipFile is not None:
        file_name = f"{assessmentId}-{uuid.uuid4().hex}-{zipFile.filename}"
        dest = Path(settings.local_submissions_dir) / _safe_key(file_name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = await zipFile.read()
        dest.write_bytes(data)
        dest_name = dest.name
    try:
        assessment_numeric = int(assessmentId)
        if email:
            mark_candidate_submitted(settings, assessment_id=assessment_numeric, email=email, name=name or None)
    except ValueError:
        pass
    return {"message": "Upload successful", "path": dest_name}
