from __future__ import annotations

from pathlib import Path
import zipfile

from app.core.config import Settings
from app.services.assessment_store import (
    CandidateRecord,
    get_assessment,
    get_latest_reflection_key_for_candidate,
    upsert_report,
)
from app.services.screen_time_analyzer import analyze_screen_time


def _safe_key(name: str) -> str:
    return name.replace('..', '').replace('\\', '/').lstrip('/')


def _safe_relative(path: Path, base: Path) -> str | None:
    try:
        return str(path.relative_to(base))
    except Exception:
        return None


def _find_latest_submission(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_submissions_dir)
    if not root.exists():
        return None
    matches = [p for p in root.glob(f'{assessment_id}-*.zip') if p.is_file()]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _find_latest_notebook(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_submissions_dir)
    if not root.exists():
        return None
    matches = [p for p in root.glob(f'{assessment_id}-*.ipynb') if p.is_file()]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _find_latest_assessment_recording(settings: Settings, assessment_id: int) -> Path | None:
    root = Path(settings.local_recordings_dir) / 'recordings'
    if not root.exists():
        return None
    matches = [p for p in root.glob(f'assessment-{assessment_id}-*.webm') if p.is_file()]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def _find_latest_reflection_recording(
    settings: Settings,
    assessment_id: int,
    candidate_email: str,
) -> Path | None:
    reflection_key = get_latest_reflection_key_for_candidate(
        settings,
        assessment_id=assessment_id,
        email=candidate_email,
    )
    if reflection_key:
        candidate_reflection = Path(settings.local_recordings_dir) / _safe_key(reflection_key)
        if candidate_reflection.is_file():
            return candidate_reflection

    root = Path(settings.local_recordings_dir) / 'reflection' / str(assessment_id)
    if not root.exists():
        return None

    # Legacy fallback (before reflection uploads were candidate-attributed):
    # only use a reflection recording when there is a single possible file.
    matches = [p for p in root.rglob('*.webm') if p.is_file()]
    if len(matches) != 1:
        return None
    return matches[0]


def _detect_assessment_type(assessment_type: str | None) -> str:
    if not assessment_type:
        return 'default'
    normalized = assessment_type.strip().lower()
    if normalized in {'default', 'assessment3-rag', 'assessment4-ner', 'json-comparison', 'java-maven'}:
        return normalized
    return 'default'


def _evaluate_submission(
    *,
    submission: Path | None,
    notebook: Path | None,
    assessment_type: str,
) -> tuple[int, int, list[dict[str, object]], list[str], list[dict[str, object]]]:
    if submission is None:
        return (
            0,
            0,
            [
                {
                    'name': 'Submission ZIP received',
                    'status': 'fail',
                    'expected': 'Upload a valid .zip project archive',
                    'output': 'No submission archive found',
                }
            ],
            ['No submission archive found.'],
            [],
        )

    archive_checks: list[dict[str, object]] = []
    summary: list[str] = []
    diffs: list[dict[str, object]] = []
    score = 40
    code_quality = 50

    try:
        with zipfile.ZipFile(submission, 'r') as zipf:
            names = zipf.namelist()
            file_count = len([n for n in names if not n.endswith('/')])
            has_readme = any(Path(n).name.lower().startswith('readme') for n in names)
            has_source = any(n.endswith(('.py', '.js', '.ts', '.java', '.ipynb')) for n in names)
            has_json = any(n.endswith('.json') for n in names)
            has_java = any(n.endswith('.java') for n in names)
            has_pom = any(Path(n).name.lower() == 'pom.xml' for n in names)
            has_ipynb = any(n.endswith('.ipynb') for n in names) or notebook is not None
            has_rag_marker = any('rag' in n.lower() for n in names)
            has_ner_marker = any('ner' in n.lower() for n in names)
            has_users_api_marker = any('users-service' in n.lower() or 'server.js' in n.lower() for n in names)
            has_retrieval_marker = any('retriev' in n.lower() or 'vector' in n.lower() for n in names)
            has_llama_marker = any('llama' in n.lower() or 'document' in n.lower() for n in names)
            code_files = [n for n in names if n.endswith(('.py', '.js', '.ts', '.java', '.ipynb', '.json'))]

        for entry in code_files[:8]:
            diffs.append(
                {
                    'path': entry,
                    'status': 'modified',
                    'modified': f'Submission artifact includes {entry}',
                }
            )

        archive_checks.append(
            {
                'name': 'Submission ZIP received',
                'status': 'pass',
                'expected': 'Upload a valid .zip project archive',
                'output': f'Found {submission.name}',
            }
        )
        archive_checks.append(
            {
                'name': 'Archive contains source files',
                'status': 'pass' if has_source else 'partial',
                'expected': 'Archive should include implementation files',
                'output': f'{file_count} files scanned',
            }
        )
        archive_checks.append(
            {
                'name': 'Documentation presence',
                'status': 'pass' if has_readme else 'partial',
                'expected': 'README or instructions included',
                'output': 'README found' if has_readme else 'README not found',
            }
        )

        score = min(100, 55 + min(file_count, 45))
        if not has_source:
            score = max(20, score - 25)
        if not has_readme:
            score = max(20, score - 10)

        if assessment_type == 'assessment3-rag':
            code_quality = 84 if has_rag_marker and has_retrieval_marker else 70
            archive_checks.append(
                {
                    'name': 'RAG pipeline artifacts',
                    'status': 'pass' if has_rag_marker else 'partial',
                    'expected': 'Include retrieval/indexing or RAG-related implementation files',
                    'output': 'RAG-specific files found' if has_rag_marker else 'No explicit RAG markers found',
                }
            )
            archive_checks.append(
                {
                    'name': 'Retrieval/index markers',
                    'status': 'pass' if has_retrieval_marker else 'partial',
                    'expected': 'Include retrieval/index/vector database logic',
                    'output': 'Retrieval markers found' if has_retrieval_marker else 'No retrieval markers found',
                }
            )
            summary.append('Assessment3 (RAG) evaluation path executed.')
        elif assessment_type == 'assessment4-ner':
            code_quality = 82 if has_ipynb else 62
            archive_checks.append(
                {
                    'name': 'NER notebook artifact',
                    'status': 'pass' if has_ipynb else 'partial',
                    'expected': 'Include notebook/script for NER training/evaluation',
                    'output': 'Notebook found' if has_ipynb else 'Notebook not found',
                }
            )
            archive_checks.append(
                {
                    'name': 'NER model indicators',
                    'status': 'pass' if has_ner_marker else 'partial',
                    'expected': 'Include NER-related code/config artifacts',
                    'output': 'NER markers found' if has_ner_marker else 'No explicit NER markers found',
                }
            )
            if notebook is not None:
                archive_checks.append(
                    {
                        'name': 'Separate notebook upload',
                        'status': 'pass',
                        'expected': 'Assessment4 notebook uploaded as companion artifact',
                        'output': f'Found {notebook.name}',
                    }
                )
            summary.append('Assessment4 (NER) evaluation path executed.')
        elif assessment_type == 'java-maven':
            code_quality = 80 if has_java and has_pom else 60
            archive_checks.append(
                {
                    'name': 'Maven project structure',
                    'status': 'pass' if has_pom else 'fail',
                    'expected': 'Include pom.xml for java-maven assessment',
                    'output': 'pom.xml found' if has_pom else 'pom.xml not found',
                }
            )
            archive_checks.append(
                {
                    'name': 'Java source presence',
                    'status': 'pass' if has_java else 'partial',
                    'expected': 'Include Java implementation files',
                    'output': 'Java files found' if has_java else 'No Java files found',
                }
            )
            summary.append('Java Maven evaluation path executed.')
        elif assessment_type == 'json-comparison':
            code_quality = 82 if has_json and has_llama_marker else 60
            archive_checks.append(
                {
                    'name': 'JSON output artifacts',
                    'status': 'pass' if has_json else 'partial',
                    'expected': 'Include structured JSON outputs/parsers',
                    'output': 'JSON artifacts found' if has_json else 'No JSON artifacts found',
                }
            )
            archive_checks.append(
                {
                    'name': 'Document processing markers',
                    'status': 'pass' if has_llama_marker else 'partial',
                    'expected': 'Include document parsing/extraction pipeline artifacts',
                    'output': 'Document-processing markers found' if has_llama_marker else 'No extraction markers found',
                }
            )
            summary.append('JSON-comparison evaluation path executed.')
        else:
            code_quality = 80 if has_users_api_marker else 58
            archive_checks.append(
                {
                    'name': 'Users API structure',
                    'status': 'pass' if has_users_api_marker else 'partial',
                    'expected': 'Include users-service/server implementation artifacts',
                    'output': 'Users API markers found' if has_users_api_marker else 'Users API markers missing',
                }
            )
            summary.append('Default evaluation path executed.')

        summary.append(f'Submission archive {submission.name} analyzed with {file_count} files.')
        summary.append(f'Evaluation path selected by assessment type: {assessment_type}.')
    except Exception as exc:
        archive_checks.append(
            {
                'name': 'Archive integrity',
                'status': 'fail',
                'expected': 'ZIP should be readable',
                'output': f'Failed to parse archive: {exc}',
            }
        )
        summary.append('Submission archive could not be parsed.')
        score = 0
        code_quality = 0

    return score, code_quality, archive_checks, summary, diffs


def run_scoring_and_store_report(settings: Settings, candidate: CandidateRecord) -> None:
    assessment = get_assessment(settings, candidate.assessment_id)
    if assessment is None:
        return

    assessment_type = _detect_assessment_type(getattr(assessment, 'assessment_type', 'default'))
    submission = _find_latest_submission(settings, candidate.assessment_id)
    notebook = _find_latest_notebook(settings, candidate.assessment_id)
    recording = _find_latest_assessment_recording(settings, candidate.assessment_id)
    reflection = _find_latest_reflection_recording(settings, candidate.assessment_id, candidate.email)

    try:
        base_score, code_quality, checks, summary, diffs = _evaluate_submission(
            submission=submission,
            notebook=notebook,
            assessment_type=assessment_type,
        )

        app_usage = []
        total_duration = 0
        if recording is not None:
            app_usage, total_duration = analyze_screen_time(recording)

        checks.append(
            {
                'name': 'Workflow recording',
                'status': 'pass' if recording else 'partial',
                'expected': 'Upload full-screen workflow recording',
                'output': recording.name if recording else 'No workflow recording found',
            }
        )
        checks.append(
            {
                'name': 'Reflection recording',
                'status': 'pass' if reflection else 'partial',
                'expected': 'Upload reflection response recording',
                'output': reflection.name if reflection else 'No reflection recording found',
            }
        )

        if recording and total_duration > 0:
            summary.append(f'Screen-time analyzer processed recording: {total_duration}s total duration.')
        if notebook is not None and assessment_type == 'assessment4-ner':
            summary.append(f'Assessment4 companion notebook detected: {notebook.name}.')

        final_score = base_score
        if recording:
            final_score = min(100, final_score + 5)
        if reflection:
            final_score = min(100, final_score + 5)

        upsert_report(
            settings,
            candidate_id=candidate.id,
            assessment_id=candidate.assessment_id,
            score=final_score,
            code_quality=code_quality,
            results=checks,
            diffs=diffs,
            code_summary_bullets=summary,
            report_ready=True,
            error=None,
            assessment_type=assessment_type,
            app_usage=app_usage,
            total_duration=total_duration,
            submission_file=_safe_relative(submission, Path(settings.local_submissions_dir)) if submission else None,
            assessment_recording_key=_safe_relative(recording, Path(settings.local_recordings_dir)) if recording else None,
            reflection_recording_key=_safe_relative(reflection, Path(settings.local_recordings_dir)) if reflection else None,
        )
    except Exception as exc:
        upsert_report(
            settings,
            candidate_id=candidate.id,
            assessment_id=candidate.assessment_id,
            score=0,
            code_quality=0,
            results=[
                {
                    'name': 'Report generation',
                    'status': 'fail',
                    'expected': 'Evaluate submission and produce report payload',
                    'output': f'Failed with error: {exc}',
                }
            ],
            diffs=[],
            code_summary_bullets=['Report generation failed. Please inspect backend logs.'],
            report_ready=True,
            error=str(exc),
            assessment_type=assessment_type,
            app_usage=[],
            total_duration=None,
            submission_file=_safe_relative(submission, Path(settings.local_submissions_dir)) if submission else None,
            assessment_recording_key=_safe_relative(recording, Path(settings.local_recordings_dir)) if recording else None,
            reflection_recording_key=_safe_relative(reflection, Path(settings.local_recordings_dir)) if reflection else None,
        )
