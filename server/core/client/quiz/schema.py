"""
Quiz schemas — quiz creation, listing, submission.
"""
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional, List


# ────────────────────────────────────────────────────────
# Quiz Creation
# ────────────────────────────────────────────────────────

class ChoiceCreate(BaseModel):
    text: str
    is_correct: bool = False


class QuestionCreate(BaseModel):
    text: str
    order_index: int
    choices: List[ChoiceCreate]


class CreateQuizRequest(BaseModel):
    title: str
    course_id: uuid.UUID
    due_date: Optional[datetime] = None
    target_section_id: Optional[uuid.UUID] = None  # None = all sections (professor)
    questions: List[QuestionCreate]


# ────────────────────────────────────────────────────────
# Quiz Response
# ────────────────────────────────────────────────────────

class ChoiceResponse(BaseModel):
    id: uuid.UUID
    text: str
    # is_correct is NOT exposed to students during quiz taking

    model_config = {"from_attributes": True}


class ChoiceWithAnswer(BaseModel):
    """For quiz results — includes whether the choice is correct."""
    id: uuid.UUID
    text: str
    is_correct: bool

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: uuid.UUID
    text: str
    order_index: int
    choices: List[ChoiceResponse]

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    id: uuid.UUID
    title: str
    course_id: uuid.UUID
    creator_role: str
    target_section_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    questions: List[QuestionResponse] = []

    model_config = {"from_attributes": True}


class QuizListItem(BaseModel):
    id: uuid.UUID
    title: str
    course_id: uuid.UUID
    course_name: Optional[str] = None
    due_date: Optional[datetime] = None
    question_count: int = 0
    is_submitted: bool = False
    score: Optional[float] = None

    model_config = {"from_attributes": True}


# ────────────────────────────────────────────────────────
# Quiz Submission
# ────────────────────────────────────────────────────────

class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    chosen_choice_id: uuid.UUID


class SubmitQuizRequest(BaseModel):
    answers: List[AnswerSubmit]


class SubmitQuizResponse(BaseModel):
    message: str
    score: float
    total_questions: int
    correct_answers: int


# ────────────────────────────────────────────────────────
# Instructor Result View
# ────────────────────────────────────────────────────────

class InstructorQuizSubmission(BaseModel):
    student_id: uuid.UUID
    student_name: str
    university_id: str
    score: float
    submitted_at: datetime


class QuizSubmissionsResponse(BaseModel):
    quiz_id: uuid.UUID
    quiz_title: str
    submissions: List[InstructorQuizSubmission]
