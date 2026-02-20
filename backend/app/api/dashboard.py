from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.services.assessment_store import (
    assessment_title_exists,
    create_assessment,
    get_question,
    list_assessments,
    list_candidates,
    list_questions,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


class CreateAssessmentRequest(BaseModel):
    title: str
    questionId: int
    jobLink: str | None = None
    jobDesc: str | None = None


@router.get("/assessments")
def get_assessments(settings: Settings = Depends(get_settings)):
    assessments = list_assessments(settings)
    return {
        "assessments": [
            {
                "id": item.id,
                "title": item.title,
                "role": item.role,
                "status": item.status,
                "createdAt": item.created_at,
                "candidateCount": item.candidate_count,
                "questionId": item.question_id,
                "jobLink": item.job_link,
                "jobDesc": item.job_desc,
            }
            for item in assessments
        ]
    }


@router.get("/candidates")
def get_candidates(
    assessment_id: int | None = Query(default=None, alias="assessmentId"),
    settings: Settings = Depends(get_settings),
):
    candidates = list_candidates(settings, assessment_id=assessment_id)
    return {
        "candidates": [
            {
                "id": item.id,
                "assessmentId": item.assessment_id,
                "email": item.email,
                "name": item.name,
                "status": item.status,
                "invitedAt": item.invited_at,
            }
            for item in candidates
        ]
    }


@router.get("/questions")
def get_questions(settings: Settings = Depends(get_settings)):
    questions = list_questions(settings)
    return [
        {
            "id": item.id,
            "_id": item.id,
            "title": item.title,
            "summary": item.summary,
            "difficulty": item.difficulty,
            "role": item.role,
            "language": item.language,
            "overview": item.overview,
            "estimatedTime": item.estimated_time,
        }
        for item in questions
    ]


@router.get("/questions/{question_id}")
def get_question_by_id(question_id: int, settings: Settings = Depends(get_settings)):
    question = get_question(settings, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return {
        "id": question.id,
        "_id": question.id,
        "title": question.title,
        "summary": question.summary,
        "difficulty": question.difficulty,
        "role": question.role,
        "language": question.language,
        "overview": question.overview,
        "estimatedTime": question.estimated_time,
    }


@router.get("/assessments/check-title")
def check_assessment_title(title: str = Query(...), settings: Settings = Depends(get_settings)):
    if not title.strip():
        raise HTTPException(status_code=400, detail="Missing title")
    return {"exists": assessment_title_exists(settings, title)}


@router.post("/new-assessments")
def new_assessment(payload: CreateAssessmentRequest, settings: Settings = Depends(get_settings)):
    clean_title = payload.title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Missing title")
    if assessment_title_exists(settings, clean_title):
        raise HTTPException(status_code=409, detail="An assessment with this title already exists")
    try:
        created = create_assessment(
            settings,
            title=clean_title,
            question_id=payload.questionId,
            job_link=payload.jobLink,
            job_desc=payload.jobDesc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "id": created.id,
        "title": created.title,
        "role": created.role,
        "status": created.status,
    }
