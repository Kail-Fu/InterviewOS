from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI
from pydantic import BaseModel

APP_ROOT = Path(__file__).resolve().parents[1]
STARTER_ROOT = APP_ROOT / "starter"
ASSETS_ROOT = APP_ROOT / "assets"
WORKSPACE_ROOT = APP_ROOT / "workspace"

app = FastAPI(title="InterviewOS Grader")


class GradeRequest(BaseModel):
    candidateId: int
    assessmentId: int
    assessmentType: str = "default"
    submissionFile: str | None = None
    notebookFile: str | None = None
    submissionPath: str | None = None
    notebookPath: str | None = None
    recordingPath: str | None = None
    reflectionPath: str | None = None
    questionData: dict[str, Any] | None = None


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_cmd(args: list[str], *, cwd: Path | None = None, timeout: int = 120, env: dict[str, str] | None = None) -> CommandResult:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        text=True,
        capture_output=True,
        env={**os.environ, **(env or {})},
    )
    return CommandResult(proc.returncode, proc.stdout[-12000:], proc.stderr[-12000:])


def safe_extract(zip_path: Path, dest: Path) -> Path:
    destination = dest.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (dest / member.filename).resolve()
            try:
                target.relative_to(destination)
            except ValueError:
                raise ValueError(f"Unsafe archive path: {member.filename}") from None
        archive.extractall(dest)
    return normalize_root(dest)


def normalize_root(root: Path) -> Path:
    ignored = {"__MACOSX", ".DS_Store", "Thumbs.db"}
    dirs = [p for p in root.iterdir() if p.name not in ignored and p.is_dir()]
    files = [p for p in root.iterdir() if p.name not in ignored and p.is_file()]
    if len(dirs) == 1 and not files:
        return normalize_root(dirs[0])
    if (root / "assessment").is_dir():
        return normalize_root(root / "assessment")
    return root


def iter_files(root: Path, *, include_ext: tuple[str, ...] | None = None) -> list[Path]:
    skip_dirs = {"node_modules", ".git", "__MACOSX", "venv", ".venv", "dist", "build", "target", "__pycache__"}
    out: list[Path] = []
    for path in root.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.name == ".DS_Store" or path.name.startswith("._"):
            continue
        if path.is_file() and (include_ext is None or path.suffix.lower() in include_ext):
            out.append(path)
    return out


def find_file(root: Path, name: str, required_part: str | None = None) -> Path | None:
    for path in iter_files(root):
        if path.name == name and (required_part is None or required_part in str(path)):
            return path
    return None


def find_available_port(start: int = 3001) -> int:
    for port in range(start, start + 300):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available port found")


def wait_for_http(url: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            requests.get(url, timeout=2)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Server did not become reachable: {last_error}")


def status_result(name: str, status: str, expected: Any, output: Any, score: int | None = None, max_score: int | None = None) -> dict[str, Any]:
    row = {"name": name, "status": status, "expected": expected, "output": output}
    if score is not None:
        row["score"] = score
    if max_score is not None:
        row["maxScore"] = max_score
    return row


def generate_diffs(starter: Path, submission: Path, limit: int = 20) -> list[dict[str, str]]:
    diffs: list[dict[str, str]] = []
    exts = (".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".md", ".json")
    starter_files = {str(p.relative_to(starter)): p for p in iter_files(starter, include_ext=exts)} if starter.exists() else {}
    submission_files = {str(p.relative_to(submission)): p for p in iter_files(submission, include_ext=exts)}
    for rel, submitted in submission_files.items():
        original = ""
        status = "added"
        if rel in starter_files:
            try:
                original = starter_files[rel].read_text(errors="replace")
            except Exception:
                original = ""
            status = "modified"
        try:
            modified = submitted.read_text(errors="replace")
        except Exception:
            modified = ""
        if original != modified:
            diffs.append({"path": rel, "status": status, "original": original[:50000], "modified": modified[:50000]})
        if len(diffs) >= limit:
            break
    return diffs


def default_starter_baseline(workspace: Path) -> Path:
    distributed_zip = ASSETS_ROOT / "example_assessment.zip"
    if distributed_zip.is_file():
        try:
            return safe_extract(distributed_zip, workspace / "distributed-starter")
        except Exception:
            pass
    return STARTER_ROOT / "assessment"


def analyze_screen(recording_path: str | None) -> tuple[list[dict[str, Any]], int, list[str]]:
    warnings: list[str] = []
    if not recording_path:
        return [], 0, warnings
    path = Path(recording_path)
    if not path.is_file():
        return [], 0, warnings
    try:
        result = run_cmd([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ], timeout=20)
        duration = int(round(float(result.stdout.strip() or "0")))
        if duration > 0:
            return [{"name": "Screen Recording", "duration": duration}], duration, warnings
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Screen analysis skipped: {exc}")
    return [], 0, warnings


def run_eslint(js_files: list[Path]) -> tuple[float | None, list[dict[str, Any]], dict[str, Any]]:
    if not js_files:
        return None, [], {"totalFindings": 0, "findingsByType": {}}
    file_issues: list[dict[str, Any]] = []
    total_errors = total_warnings = 0
    for file_path in js_files[:30]:
        try:
            result = run_cmd([
                "eslint", "--no-eslintrc", "--env", "node", "--parser-options", "ecmaVersion:2021",
                "--rule", "no-unused-vars:warn", "--rule", "no-undef:error", "--format", "json", str(file_path),
            ], timeout=30)
            parsed = json.loads(result.stdout or "[]")
            messages = []
            source_lines = file_path.read_text(errors="replace").splitlines()
            for item in parsed:
                for msg in item.get("messages", []):
                    severity = int(msg.get("severity") or 0)
                    total_errors += 1 if severity == 2 else 0
                    total_warnings += 1 if severity == 1 else 0
                    line = int(msg.get("line") or 1)
                    messages.append({
                        "ruleId": msg.get("ruleId") or "unknown",
                        "severity": severity,
                        "message": msg.get("message") or "",
                        "line": line,
                        "column": msg.get("column"),
                        "codeLine": source_lines[line - 1] if 0 <= line - 1 < len(source_lines) else "",
                    })
            if messages:
                file_issues.append({"file": file_path.name, "messages": messages})
        except Exception:
            continue
    score = max(0, 10 - min(total_errors * 2, 8) - min(total_warnings * 0.75, 4))
    return score, file_issues, {
        "totalFindings": total_errors + total_warnings,
        "findingsByType": {"error": total_errors, "warning": total_warnings},
    }


def structural_similarity(expected: Any, actual: Any) -> int:
    if expected == actual:
        return 100
    if isinstance(expected, dict) and isinstance(actual, dict):
        keys = set(expected.keys()) | set(actual.keys())
        if not keys:
            return 100
        return round(sum(structural_similarity(expected.get(k), actual.get(k)) for k in keys) / len(keys))
    if isinstance(expected, list) and isinstance(actual, list):
        if not expected and not actual:
            return 100
        pairs = zip(expected, actual)
        denom = max(len(expected), len(actual), 1)
        return round(sum(structural_similarity(a, b) for a, b in pairs) / denom)
    if expected is None or actual is None:
        return 0
    expected_s = str(expected).strip().lower()
    actual_s = str(actual).strip().lower()
    return round(difflib.SequenceMatcher(None, expected_s, actual_s).ratio() * 100)


def users_api_eval(submission: Path, starter: Path | None = None) -> dict[str, Any]:
    server_path = find_file(submission, "server.js", "users-service") or find_file(submission, "server.js")
    if server_path is None:
        return fail_report("server.js not found in submitted Users API project", "default")
    project_dir = server_path.parent
    if (project_dir / "package.json").exists():
        run_cmd(["npm", "install", "--omit=dev"], cwd=project_dir, timeout=180)
    port = find_available_port(3001)
    proc = subprocess.Popen(
        ["node", str(server_path)], cwd=str(project_dir), env={**os.environ, "PORT": str(port)},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    results: list[dict[str, Any]] = []
    try:
        wait_for_http(f"http://127.0.0.1:{port}/users/inactive", timeout=25)
        tests = [
            ("Invalid ID: abc", f"http://127.0.0.1:{port}/users/abc", 400),
            ("Invalid ID: symbols", f"http://127.0.0.1:{port}/users/123!@#", 400),
            ("Invalid ID: undefined", f"http://127.0.0.1:{port}/users/undefined", 400),
            ("Filter by status", f"http://127.0.0.1:{port}/users?status=active", 200),
            ("Filter by team", f"http://127.0.0.1:{port}/users?team=engineering", 200),
            ("Filter by status and team", f"http://127.0.0.1:{port}/users?status=inactive&team=marketing", 200),
            ("Inactive users", f"http://127.0.0.1:{port}/users/inactive", 200),
        ]
        for name, url, expected in tests:
            try:
                resp = requests.get(url, timeout=8)
                results.append(status_result(name, "pass" if resp.status_code == expected else "fail", expected, resp.status_code))
            except Exception as exc:  # noqa: BLE001
                results.append(status_result(name, "fail", expected, str(exc)))
    except Exception as exc:  # noqa: BLE001
        results.append(status_result("Server startup", "fail", "Candidate server responds", str(exc)))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    passed = len([r for r in results if r.get("status") == "pass"])
    score = round((passed / max(len(results), 1)) * 100)
    eslint_score, eslint_issues, eslint_analysis = run_eslint(iter_files(submission, include_ext=(".js", ".jsx")))
    code_quality = round((eslint_score if eslint_score is not None else 6) * 10)
    return {
        "score": score,
        "codeQuality": code_quality,
        "results": results,
        "diffs": generate_diffs(starter or STARTER_ROOT / "assessment", submission),
        "codeSummaryBullets": ["Users API grader executed endpoint tests.", f"{passed}/{len(results)} checks passed."],
        "eslintIssues": eslint_issues,
        "eslintAnalysis": eslint_analysis,
        "assessmentType": "default",
    }


def json_comparison_eval(submission: Path, question_data: dict[str, Any] | None) -> dict[str, Any]:
    main_py = find_file(submission, "main.py", "fastapi_server") or find_file(submission, "main.py")
    if main_py is None:
        return fail_report("fastapi_server/main.py not found", "json-comparison")
    starter_name = "llama-index-assessment" if "llama" in ((question_data or {}).get("title", "").lower()) else "assessment2"
    fastapi_dir = main_py.parent
    venv = fastapi_dir / ".interviewos-venv"
    python = venv / "bin" / "python"
    try:
        run_cmd(["python", "-m", "venv", str(venv)], timeout=120)
        pip = venv / "bin" / "pip"
        run_cmd([str(pip), "install", "--upgrade", "pip"], timeout=120)
        req = fastapi_dir / "requirements.txt"
        if req.exists():
            run_cmd([str(pip), "install", "-r", str(req)], timeout=240)
        else:
            run_cmd([str(pip), "install", "fastapi", "uvicorn", "python-multipart"], timeout=180)
    except Exception:
        python = Path("python")
    port = find_available_port(4200)
    proc = subprocess.Popen(
        [str(python), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(fastapi_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    results: list[dict[str, Any]] = []
    try:
        wait_for_http(f"http://127.0.0.1:{port}/api/health", timeout=35)
        docs_dir = STARTER_ROOT / starter_name / "src" / "documents"
        answers_dir = STARTER_ROOT / starter_name / "fastapi_server" / "answers"
        for i in range(1, 11):
            doc = docs_dir / f"document_{i}.pdf"
            answer = answers_dir / f"document_{i}.json"
            if not doc.exists() or not answer.exists():
                continue
            expected = json.loads(answer.read_text())
            try:
                with doc.open("rb") as handle:
                    resp = requests.post(f"http://127.0.0.1:{port}/api/process", files={"file": (doc.name, handle, "application/pdf")}, timeout=90)
                data = resp.json()
                actual = data.get("extractedData", data)
                similarity = structural_similarity(expected, actual)
                test_score = 10 if similarity >= 80 else 8 if similarity >= 60 else 5 if similarity >= 50 else 0
                results.append({
                    "name": f"Document {i} Processing",
                    "status": "pass" if test_score >= 8 else "partial" if test_score >= 5 else "fail",
                    "input": doc.name,
                    "expected": json.dumps(expected, indent=2),
                    "output": json.dumps(actual, indent=2),
                    "score": test_score,
                    "maxScore": 10,
                    "similarity": similarity,
                    "summary": {"expected": "Valid schema-aligned JSON", "output": f"Similarity: {similarity}%"},
                })
            except Exception as exc:  # noqa: BLE001
                results.append(status_result(f"Document {i} Processing", "fail", "Successful JSON extraction", str(exc), 0, 10))
    except Exception as exc:  # noqa: BLE001
        results.append(status_result("FastAPI server setup", "fail", "Server starts and responds", str(exc), 0, 10))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(venv, ignore_errors=True)
    total = sum(int(r.get("score", 0)) for r in results)
    max_total = sum(int(r.get("maxScore", 10)) for r in results) or 1
    return {
        "score": round((total / max_total) * 100),
        "codeQuality": None,
        "results": results,
        "diffs": generate_diffs(STARTER_ROOT / starter_name, submission),
        "codeSummaryBullets": [f"Document processor grader executed {len(results)} fixture checks."],
        "assessmentType": "json-comparison",
    }


def external_autograder(script: Path, submission: Path, assessment_type: str, timeout: int = 900) -> dict[str, Any]:
    try:
        result = run_cmd(["python", str(script), str(submission)], cwd=APP_ROOT, timeout=timeout)
        match = re.search(r"\{[\s\S]*\}", result.stdout)
        parsed = json.loads(match.group(0)) if match else {"success": False, "error": "No JSON output", "stdout": result.stdout, "stderr": result.stderr}
        if assessment_type == "assessment4-ner" and parsed.get("success"):
            id_f1 = float(parsed.get("id_macro_f1", 0))
            ood_f1 = float(parsed.get("ood_macro_f1", 0))
            score = round(((id_f1 + ood_f1) / 2) * 100)
            return {
                "score": score,
                "codeQuality": None,
                "results": [
                    status_result("In-Domain F1", "pass" if id_f1 >= 0.8 else "partial", ">= 0.80", round(id_f1, 4)),
                    status_result("Out-of-Domain F1", "pass" if ood_f1 >= 0.8 else "partial", ">= 0.80", round(ood_f1, 4)),
                    status_result("Inference Latency", "pass", "Measured latency", parsed.get("latency_sec")),
                ],
                "diffs": notebook_diffs(submission),
                "codeSummaryBullets": ["NER model autograder executed ID/OOD evaluation."],
                "assessment4Results": parsed,
                "assessmentType": assessment_type,
            }
        tests = parsed.get("tests", [])
        max_points = parsed.get("max_points", 100) or 100
        total_points = parsed.get("total_points", 0) or 0
        return {
            "score": round((total_points / max_points) * 100),
            "codeQuality": None,
            "results": tests if isinstance(tests, list) else [],
            "diffs": [],
            "codeSummaryBullets": [f"Autograder completed for {assessment_type}."],
            "autograderOutput": parsed,
            "assessmentType": assessment_type,
            "error": None if parsed.get("success") else parsed.get("error"),
        }
    except Exception as exc:  # noqa: BLE001
        return fail_report(f"Autograder failed: {exc}", assessment_type)


def notebook_diffs(submission: Path) -> list[dict[str, str]]:
    starter = APP_ROOT / "assessment4" / "starter_notebook.ipynb"
    notebooks = iter_files(submission, include_ext=(".ipynb",))
    if not starter.exists() or not notebooks:
        return []
    try:
        return [{"path": notebooks[0].name, "status": "modified", "original": starter.read_text(errors="replace")[:50000], "modified": notebooks[0].read_text(errors="replace")[:50000]}]
    except Exception:
        return []


def fail_report(message: str, assessment_type: str) -> dict[str, Any]:
    return {
        "score": 0,
        "codeQuality": 0,
        "results": [status_result("Report generation", "fail", "Evaluate submission", message)],
        "diffs": [],
        "codeSummaryBullets": [message],
        "assessmentType": assessment_type,
        "error": message,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/grade")
def grade(payload: GradeRequest) -> dict[str, Any]:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f"candidate-{payload.candidateId}-", dir=WORKSPACE_ROOT))
    warnings: list[str] = []
    try:
        submission_zip = Path(payload.submissionPath or "")
        if not submission_zip.is_file():
            return {**fail_report("Submission ZIP not found", payload.assessmentType), "reportReady": True}
        submission = safe_extract(submission_zip, workspace / "submission")
        if payload.notebookPath and Path(payload.notebookPath).is_file():
            shutil.copy2(payload.notebookPath, submission / Path(payload.notebookPath).name)
        assessment_type = (payload.assessmentType or "default").strip().lower()
        if assessment_type == "json-comparison":
            report = json_comparison_eval(submission, payload.questionData)
        elif assessment_type == "assessment3-rag":
            report = external_autograder(APP_ROOT / "assessment3" / "assessment3_autograder.py", submission, assessment_type)
        elif assessment_type == "assessment4-ner":
            report = external_autograder(APP_ROOT / "assessment4" / "assessment4_autograder.py", submission, assessment_type)
        else:
            report = users_api_eval(submission, default_starter_baseline(workspace))
        app_usage, duration, screen_warnings = analyze_screen(payload.recordingPath)
        warnings.extend(screen_warnings)
        report.setdefault("appUsage", app_usage)
        report.setdefault("totalDuration", duration)
        if warnings:
            report["warnings"] = warnings
        report["reportReady"] = True
        report["status"] = "ready"
        return report
    except Exception as exc:  # noqa: BLE001
        return {**fail_report(str(exc), payload.assessmentType), "reportReady": True, "status": "failed"}
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
