from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

from app.core.config import Settings


def grade_with_worker(settings: Settings, payload: dict[str, object]) -> dict[str, object]:
    url = f"{settings.grader_worker_url}/grade"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=settings.report_grader_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise RuntimeError("Grader worker returned a non-object payload")
            return parsed
    except error.URLError as exc:
        raise RuntimeError(f"Grader worker is unavailable at {url}: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Grader worker timed out after {settings.report_grader_timeout_seconds}s") from exc


def absolute_path_or_none(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path.resolve()) if path.exists() else None
