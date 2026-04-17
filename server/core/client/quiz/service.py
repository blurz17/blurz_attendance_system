"""
Quiz service — create, list, details, submission with auto-scoring.
"""
import uuid
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, col, and_
from sqlalchemy.orm import selectinload

from core.db.models import (
    Quiz, Question, Choice, QuizSubmission, SubmissionAnswer,
    Enrollment, Student, CourseProfessor, Course, User,
)
from core.errors import (
    QuizNotFound, InsufficientPermission, QuizAlreadySubmitted,
    NotEnrolled, SectionMismatch,
)


# ── QUIZ CREATION ──────────────────────────────

async def create_quiz(
    title: str, course_id: uuid.UUID, created_by: uuid.UUID,
    creator_role: str, due_date: datetime, target_section_id: uuid.UUID,
    questions_data: list, session: AsyncSession,
) -> Quiz:
    """Create a quiz with questions and choices."""
    # Professors can only create for their assigned courses
    if creator_role == "professor":
        cp = await session.execute(
            select(CourseProfessor).where(
                and_(CourseProfessor.course_id == course_id, CourseProfessor.professor_id == created_by)
            )
        )
        if not cp.scalar_one_or_none():
            raise InsufficientPermission()

    if due_date and due_date.tzinfo:
        due_date = due_date.astimezone(timezone.utc).replace(tzinfo=None)

    quiz = Quiz(
        title=title, course_id=course_id, created_by=created_by,
        creator_role=creator_role, due_date=due_date, target_section_id=target_section_id,
    )
    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)

    for idx, q_data in enumerate(questions_data):
        question = Question(quiz_id=quiz.id, text=q_data.text, order_index=q_data.order_index or (idx + 1))
        session.add(question)
        await session.commit()
        await session.refresh(question)

        for c_data in q_data.choices:
            session.add(Choice(question_id=question.id, text=c_data.text, is_correct=c_data.is_correct))

    await session.commit()
    return quiz


# ── LISTING QUIZZES ────────────────────────────

async def list_available_quizzes(student_id: uuid.UUID, session: AsyncSession) -> list[dict]:
    """List quizzes available for a student (enrolled courses, matching section)."""
    student = await session.get(Student, student_id)
    if not student:
        return []

    enrolled_ids = (await session.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == student_id)
    )).scalars().all()

    if not enrolled_ids:
        return []

    quizzes = (await session.execute(
        select(Quiz)
        .where(col(Quiz.course_id).in_(enrolled_ids))
        .where((Quiz.target_section_id == None) | (Quiz.target_section_id == student.section_id))
    )).scalars().all()

    quiz_list = []
    for q in quizzes:
        q_count = len((await session.execute(select(Question).where(Question.quiz_id == q.id))).scalars().all())
        course = await session.get(Course, q.course_id)

        submission = (await session.execute(
            select(QuizSubmission).where(
                and_(QuizSubmission.quiz_id == q.id, QuizSubmission.student_id == student_id)
            )
        )).scalar_one_or_none()

        quiz_list.append({
            "id": q.id, "title": q.title, "course_id": q.course_id,
            "course_name": course.name if course else "Unknown",
            "due_date": q.due_date, "question_count": q_count,
            "is_submitted": submission is not None,
            "score": submission.score if submission else None,
        })

    return quiz_list


async def list_instructor_quizzes(instructor_id: uuid.UUID, session: AsyncSession) -> list[dict]:
    """List quizzes created by a specific professor."""
    quizzes = (await session.execute(
        select(Quiz).where(Quiz.created_by == instructor_id)
    )).scalars().all()

    quiz_list = []
    for q in quizzes:
        q_count = len((await session.execute(select(Question).where(Question.quiz_id == q.id))).scalars().all())
        course = await session.get(Course, q.course_id)
        quiz_list.append({
            "id": q.id, "title": q.title, "course_id": q.course_id,
            "course_name": course.name if course else "Unknown",
            "due_date": q.due_date, "question_count": q_count,
        })

    return quiz_list


# ── QUIZ DETAILS ───────────────────────────────

async def get_quiz_details(quiz_id: uuid.UUID, session: AsyncSession) -> Quiz:
    """Get quiz with all questions and choices."""
    result = await session.execute(
        select(Quiz).where(Quiz.id == quiz_id)
        .options(selectinload(Quiz.questions).selectinload(Question.choices))
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise QuizNotFound()
    return quiz


# ── SUBMISSION & SCORING ───────────────────────

async def submit_quiz(
    quiz_id: uuid.UUID, student_id: uuid.UUID, answers: list, session: AsyncSession,
) -> dict:
    """Process a student's quiz submission with auto-scoring."""
    quiz = await session.get(Quiz, quiz_id)
    if not quiz:
        raise QuizNotFound()

    student = await session.get(Student, student_id)
    if not student:
        raise InsufficientPermission()

    # Must be enrolled
    enrollment = (await session.execute(
        select(Enrollment).where(and_(Enrollment.student_id == student_id, Enrollment.course_id == quiz.course_id))
    )).scalar_one_or_none()
    if not enrollment:
        raise NotEnrolled()

    # Section check
    if quiz.target_section_id and quiz.target_section_id != student.section_id:
        raise SectionMismatch()

    # No duplicate submissions
    existing = (await session.execute(
        select(QuizSubmission).where(and_(QuizSubmission.student_id == student_id, QuizSubmission.quiz_id == quiz_id))
    )).scalar_one_or_none()
    if existing:
        raise QuizAlreadySubmitted()

    # Get questions
    questions = (await session.execute(select(Question).where(Question.quiz_id == quiz.id))).scalars().all()
    total = len(questions)

    # Map answers: question_id → chosen_choice_id
    answer_map = {str(a.question_id): str(a.chosen_choice_id) for a in answers}

    # Create submission
    submission = QuizSubmission(student_id=student_id, quiz_id=quiz_id, score=0)
    session.add(submission)
    await session.commit()
    await session.refresh(submission)

    # Score each answer
    correct = 0
    for question in questions:
        chosen_id = answer_map.get(str(question.id))
        if not chosen_id:
            continue

        choice = (await session.execute(select(Choice).where(Choice.id == uuid.UUID(chosen_id)))).scalar_one_or_none()
        if choice and choice.is_correct:
            correct += 1

        session.add(SubmissionAnswer(
            submission_id=submission.id, question_id=question.id, chosen_choice_id=uuid.UUID(chosen_id),
        ))

    score = (correct / total * 100) if total > 0 else 0
    submission.score = score
    await session.commit()

    return {"message": "Quiz submitted successfully", "score": score, "total_questions": total, "correct_answers": correct}


# ── INSTRUCTOR RESULTS ─────────────────────────

async def get_quiz_submissions(quiz_id: uuid.UUID, instructor_id: uuid.UUID, session: AsyncSession) -> dict:
    """Get all submissions for a quiz (instructor view)."""
    quiz = await session.get(Quiz, quiz_id)
    if not quiz:
        raise QuizNotFound()

    # Must be creator or assigned to the course
    if str(quiz.created_by) != str(instructor_id):
        cp = (await session.execute(
            select(CourseProfessor).where(
                and_(CourseProfessor.course_id == quiz.course_id, CourseProfessor.professor_id == instructor_id)
            )
        )).scalar_one_or_none()
        if not cp:
            raise InsufficientPermission()

    rows = (await session.execute(
        select(QuizSubmission, User)
        .join(User, QuizSubmission.student_id == User.id)
        .where(QuizSubmission.quiz_id == quiz_id)
        .order_by(User.full_name)
    )).all()

    return {
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "submissions": [
            {
                "student_id": sub.student_id, "student_name": user.full_name,
                "university_id": user.university_id, "score": sub.score, "submitted_at": sub.submitted_at,
            }
            for sub, user in rows
        ],
    }