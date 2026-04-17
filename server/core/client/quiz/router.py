"""
Quiz router — endpoints for quiz creation, listing, and submission.
"""
import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db.main import get_session
from core.dependencies import RoleChecker, get_current_user
from core.db.models import User
from core.client.quiz.schema import (
    CreateQuizRequest, QuizListItem, QuizResponse,
    SubmitQuizRequest, SubmitQuizResponse, QuizSubmissionsResponse,
)
from core.client.quiz import service as quiz_svc

quiz_router = APIRouter()


@quiz_router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_quiz(
    data: CreateQuizRequest,
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Create a quiz with questions and choices."""
    quiz = await quiz_svc.create_quiz(
        title=data.title, course_id=data.course_id, created_by=user.id,
        creator_role=user.role, due_date=data.due_date,
        target_section_id=data.target_section_id, questions_data=data.questions, session=session,
    )
    return JSONResponse(content={"message": "Quiz created successfully", "quiz_id": str(quiz.id)}, status_code=201)


@quiz_router.get("/available", response_model=list[QuizListItem])
async def list_available_quizzes(
    user: User = Depends(RoleChecker(["student"])),
    session: AsyncSession = Depends(get_session),
):
    """List quizzes available for the current student."""
    return await quiz_svc.list_available_quizzes(student_id=user.id, session=session)


@quiz_router.get("/instructor", response_model=list[QuizListItem])
async def list_instructor_quizzes(
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """List quizzes created by the current instructor."""
    return await quiz_svc.list_instructor_quizzes(instructor_id=user.id, session=session)


@quiz_router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz_details(
    quiz_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a quiz with all its questions and choices."""
    return await quiz_svc.get_quiz_details(quiz_id, session)


@quiz_router.post("/{quiz_id}/submit", response_model=SubmitQuizResponse)
async def submit_quiz(
    quiz_id: uuid.UUID,
    data: SubmitQuizRequest,
    user: User = Depends(RoleChecker(["student"])),
    session: AsyncSession = Depends(get_session),
):
    """Submit a quiz with answers. Auto-scored."""
    return await quiz_svc.submit_quiz(quiz_id=quiz_id, student_id=user.id, answers=data.answers, session=session)


@quiz_router.get("/instructor/submissions/{quiz_id}", response_model=QuizSubmissionsResponse)
async def get_quiz_submissions(
    quiz_id: uuid.UUID,
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Get all submissions for a quiz."""
    return await quiz_svc.get_quiz_submissions(quiz_id=quiz_id, instructor_id=user.id, session=session)
