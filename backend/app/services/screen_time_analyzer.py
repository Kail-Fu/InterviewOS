from __future__ import annotations

import subprocess
from pathlib import Path


def _probe_duration_seconds(video_path: Path) -> int:
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        raw = result.stdout.strip()
        return max(0, int(round(float(raw)))) if raw else 0
    except Exception:
        return 0


def analyze_screen_time(video_path: str | Path) -> tuple[list[dict[str, object]], int]:
    """Local analyzer hook for report pipeline.

    This is intentionally lightweight for OSS defaults: it extracts total duration
    and returns a coarse app-usage bucket. The interface matches the richer
    analyzer flow so we can swap in full model-based classification later.
    """
    path = Path(video_path)
    if not path.exists() or not path.is_file():
        return ([], 0)

    total_duration = _probe_duration_seconds(path)
    if total_duration <= 0:
        return ([], 0)

    return (
        [
            {
                'name': 'Screen Recording',
                'duration': total_duration,
            }
        ],
        total_duration,
    )
