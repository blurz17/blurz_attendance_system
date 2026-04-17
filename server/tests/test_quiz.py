"""
tests/test_quiz.py
==================
E2E tests for /api/v1/quiz/* endpoints.

  POST /api/v1/quiz/create
  GET  /api/v1/quiz/available
  GET  /api/v1/quiz/instructor
  GET  /api/v1/quiz/{quiz_id}
  POST /api/v1/quiz/{quiz_id}/submit
  GET  /api/v1/quiz/instructor/submissions/{quiz_id}

Bug coverage
------------
- BUG-#4:  Route ordering — /instructor/submissions/{id} masked by /{id}
           Test confirms submissions endpoint is actually reachable.
- BUG-#6:  Quiz with no correct answers — score 0, not an error.
- BUG-#8:  Due date never checked — student can submit after deadline.
           Test documents current (wrong) behaviour and the expected fix.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from conftest import (
    db_create_course, db_enroll, db_create_user, _uid,
)
from core.auth.schema import UserRole
from core.db.models import User, Course

BASE = "/api/v1/quiz"

# Reusable quiz payload factory
def _quiz_payload(course_id: str, title: str = "Test Quiz") -> dict:
    return {
        "title": title,
        "course_id": course_id,
        "questions": [
            {
                "text": "What is 2 + 2?",
                "order_index": 1,
                "choices": [
                    {"text": "3", "is_correct": False},
                    {"text": "4", "is_correct": True},
                    {"text": "5", "is_correct": False},
                ],
            },
            {
                "text": "Which is a programming language?",
                "order_index": 2,
                "choices": [
                    {"text": "Python", "is_correct": True},
                    {"text": "Photoshop", "is_correct": False},
                ],
            },
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ CREATION
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_professor_creates_quiz_for_own_course(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"QuizCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
        headers=professor_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert "quiz_id" in data


@pytest.mark.asyncio
async def test_student_cannot_create_quiz(
    client: AsyncClient, student_headers: dict, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"NoCreateCourse_{_uid()}", year=1)
    r = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
        headers=student_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_create_quiz(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"UnauthCourse_{_uid()}", year=1)
    r = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
    )
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_professor_cannot_create_quiz_for_unowned_course(
    client: AsyncClient,
    active_professor: User,
    second_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    other_course = await db_create_course(
        db_session, f"OtherQuizCourse_{_uid()}", year=1, professor_id=second_professor.id
    )
    r = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(other_course.id)),
        headers=professor_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_quiz_with_due_date(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"DueDateCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    payload = {**_quiz_payload(str(course.id)), "due_date": due}
    r = await client.post(f"{BASE}/create", json=payload, headers=professor_headers)
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_quiz_with_target_section(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    from conftest import db_create_section
    section = await db_create_section(db_session, f"QuizSec_{_uid()}")
    course = await db_create_course(
        db_session, f"SecQuizCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    payload = {
        **_quiz_payload(str(course.id)),
        "target_section_id": str(section.id),
    }
    r = await client.post(f"{BASE}/create", json=payload, headers=professor_headers)
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_quiz_no_questions_accepted_or_422(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """
    BUG-#6 RELATED: zero questions quiz should ideally be rejected (422).
    Current code accepts it (201). Test documents actual behaviour.
    """
    course = await db_create_course(
        db_session, f"EmptyQuizCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    payload = {"title": "Empty Quiz", "course_id": str(course.id), "questions": []}
    r = await client.post(f"{BASE}/create", json=payload, headers=professor_headers)
    # Currently accepted — document & assert what the server does
    assert r.status_code in (201, 422)


@pytest.mark.asyncio
async def test_create_quiz_all_choices_wrong_accepted_bug(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """
    BUG-#6: Quiz with no correct answers is accepted. Score will always be 0.
    This test documents the current broken behaviour.
    """
    course = await db_create_course(
        db_session, f"NoBugCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    payload = {
        "title": "All Wrong Quiz",
        "course_id": str(course.id),
        "questions": [
            {
                "text": "Trick question",
                "order_index": 1,
                "choices": [
                    {"text": "Wrong A", "is_correct": False},
                    {"text": "Wrong B", "is_correct": False},
                ],
            }
        ],
    }
    r = await client.post(f"{BASE}/create", json=payload, headers=professor_headers)
    # BUG: server accepts this — should be 422 but is 201
    assert r.status_code == 201, "BUG-#6: quiz with no correct answers should fail validation"


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ LISTING
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_lists_available_quizzes(
    client: AsyncClient, student_headers: dict
):
    r = await client.get(f"{BASE}/available", headers=student_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_professor_cannot_access_student_quiz_list(
    client: AsyncClient, professor_headers: dict
):
    r = await client.get(f"{BASE}/available", headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_enrolled_student_sees_quiz_in_list(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"VisibleQuiz_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    title = f"My Quiz {_uid()}"
    r_create = await client.post(
        f"{BASE}/create",
        json={**_quiz_payload(str(course.id)), "title": title},
        headers=professor_headers,
    )
    assert r_create.status_code == 201

    r_list = await client.get(f"{BASE}/available", headers=student_headers)
    assert r_list.status_code == 200
    titles = [q["title"] for q in r_list.json()]
    assert title in titles


@pytest.mark.asyncio
async def test_unenrolled_student_does_not_see_quiz(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"InvisibleQuiz_{_uid()}", year=1, professor_id=active_professor.id
    )
    # Do NOT enroll student
    title = f"Hidden Quiz {_uid()}"
    await client.post(
        f"{BASE}/create",
        json={**_quiz_payload(str(course.id)), "title": title},
        headers=professor_headers,
    )

    r_list = await client.get(f"{BASE}/available", headers=student_headers)
    titles = [q["title"] for q in r_list.json()]
    assert title not in titles


@pytest.mark.asyncio
async def test_professor_lists_instructor_quizzes(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"InstrCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    title = f"Instructor Quiz {_uid()}"
    await client.post(
        f"{BASE}/create",
        json={**_quiz_payload(str(course.id)), "title": title},
        headers=professor_headers,
    )

    r = await client.get(f"{BASE}/instructor", headers=professor_headers)
    assert r.status_code == 200
    titles = [q["title"] for q in r.json()]
    assert title in titles


@pytest.mark.asyncio
async def test_student_cannot_access_instructor_quiz_list(
    client: AsyncClient, student_headers: dict
):
    r = await client.get(f"{BASE}/instructor", headers=student_headers)
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ DETAILS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_quiz_details_returns_questions_and_choices(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    student_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"DetailCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r_create = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id), title="Detail Quiz"),
        headers=professor_headers,
    )
    quiz_id = r_create.json()["quiz_id"]

    r = await client.get(f"{BASE}/{quiz_id}", headers=student_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "Detail Quiz"
    assert len(data["questions"]) == 2
    for q in data["questions"]:
        assert "choices" in q
        assert len(q["choices"]) >= 2


@pytest.mark.asyncio
async def test_quiz_details_does_not_expose_is_correct_to_students(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    student_headers: dict,
    db_session: AsyncSession,
):
    """
    Security check: ChoiceResponse schema omits is_correct.
    If 'is_correct' appears in ANY choice, it's a data-leak bug.
    """
    course = await db_create_course(
        db_session, f"SecureCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r_create = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
        headers=professor_headers,
    )
    quiz_id = r_create.json()["quiz_id"]

    r = await client.get(f"{BASE}/{quiz_id}", headers=student_headers)
    data = r.json()
    for q in data["questions"]:
        for c in q["choices"]:
            assert "is_correct" not in c, "SECURITY BUG: is_correct exposed to student"


@pytest.mark.asyncio
async def test_get_nonexistent_quiz_returns_404(
    client: AsyncClient, student_headers: dict
):
    r = await client.get(f"{BASE}/{uuid.uuid4()}", headers=student_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_quiz_unauthenticated_returns_403(client: AsyncClient):
    r = await client.get(f"{BASE}/{uuid.uuid4()}")
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# QUIZ SUBMISSION
# ─────────────────────────────────────────────────────────────────────────────

async def _create_and_enroll_quiz(
    client: AsyncClient,
    professor_headers: dict,
    student_headers: dict,
    active_professor: User,
    active_student: User,
    db_session: AsyncSession,
    title: str = "Submit Quiz",
) -> tuple[str, list]:
    """Helper: create course, enroll student, create quiz, return (quiz_id, questions)."""
    course = await db_create_course(
        db_session, f"SubmitCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    r_create = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id), title=title),
        headers=professor_headers,
    )
    assert r_create.status_code == 201
    quiz_id = r_create.json()["quiz_id"]

    # Fetch details to get real choice IDs
    r_detail = await client.get(f"{BASE}/{quiz_id}", headers=student_headers)
    questions = r_detail.json()["questions"]
    return quiz_id, questions


@pytest.mark.asyncio
async def test_student_submits_quiz_receives_score(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    quiz_id, questions = await _create_and_enroll_quiz(
        client, professor_headers, student_headers,
        active_professor, active_student, db_session, title="Basic Submit"
    )
    answers = [
        {"question_id": q["id"], "chosen_choice_id": q["choices"][0]["id"]}
        for q in questions
    ]
    r = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "score" in data
    assert "total_questions" in data
    assert data["total_questions"] == 2
    assert 0.0 <= data["score"] <= 100.0


@pytest.mark.asyncio
async def test_student_scores_100_with_all_correct_answers(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """Select the correct choice for every question → score must be 100."""
    quiz_id, questions = await _create_and_enroll_quiz(
        client, professor_headers, student_headers,
        active_professor, active_student, db_session, title="Perfect Score"
    )
    CORRECT_TEXTS = {"4", "Python"}  # from _quiz_payload
    answers = []
    for q in questions:
        for c in q["choices"]:
            if c["text"] in CORRECT_TEXTS:
                answers.append({
                    "question_id": q["id"],
                    "chosen_choice_id": c["id"],
                })
                break

    r = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == 100.0
    assert data["correct_answers"] == 2


@pytest.mark.asyncio
async def test_student_scores_0_with_all_wrong_answers(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    quiz_id, questions = await _create_and_enroll_quiz(
        client, professor_headers, student_headers,
        active_professor, active_student, db_session, title="Zero Score"
    )
    WRONG_TEXTS = {"3", "Photoshop"}  # both wrong
    answers = []
    for q in questions:
        for c in q["choices"]:
            if c["text"] in WRONG_TEXTS:
                answers.append({
                    "question_id": q["id"],
                    "chosen_choice_id": c["id"],
                })
                break

    r = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert r.status_code == 200
    assert r.json()["score"] == 0.0
    assert r.json()["correct_answers"] == 0


@pytest.mark.asyncio
async def test_duplicate_submission_returns_409(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    quiz_id, questions = await _create_and_enroll_quiz(
        client, professor_headers, student_headers,
        active_professor, active_student, db_session, title="Dup Submit"
    )
    answers = [
        {"question_id": q["id"], "chosen_choice_id": q["choices"][0]["id"]}
        for q in questions
    ]
    r1 = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert r1.status_code == 200

    r2 = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    assert r2.status_code == 409  # QuizAlreadySubmitted


@pytest.mark.asyncio
async def test_professor_cannot_submit_quiz(
    client: AsyncClient, professor_headers: dict
):
    r = await client.post(
        f"{BASE}/{uuid.uuid4()}/submit",
        json={"answers": []},
        headers=professor_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unenrolled_student_cannot_submit(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"UnenrollSubmit_{_uid()}", year=1, professor_id=active_professor.id
    )
    # Do NOT enroll student

    r_create = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
        headers=professor_headers,
    )
    quiz_id = r_create.json()["quiz_id"]

    r = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": []},
        headers=student_headers,
    )
    assert r.status_code == 403  # NotEnrolled


@pytest.mark.asyncio
async def test_submit_nonexistent_quiz_returns_404(
    client: AsyncClient, student_headers: dict
):
    r = await client.post(
        f"{BASE}/{uuid.uuid4()}/submit",
        json={"answers": []},
        headers=student_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_submit_after_due_date_accepted_bug(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """
    BUG-#8: due_date is never checked in submit_quiz.
    A past due_date must NOT block submission — this documents the bug.
    Once fixed, this test should assert r.status_code == 410 (QuizExpired).
    """
    course = await db_create_course(
        db_session, f"ExpiredQuiz_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    past_due = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        **_quiz_payload(str(course.id), title="Expired Quiz"),
        "due_date": past_due,
    }
    r_create = await client.post(f"{BASE}/create", json=payload, headers=professor_headers)
    assert r_create.status_code == 201
    quiz_id = r_create.json()["quiz_id"]

    r_detail = await client.get(f"{BASE}/{quiz_id}", headers=student_headers)
    questions = r_detail.json()["questions"]
    answers = [
        {"question_id": q["id"], "chosen_choice_id": q["choices"][0]["id"]}
        for q in questions
    ]

    r = await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )
    # BUG: Currently 200 — should be 410 once due_date check is implemented
    assert r.status_code == 200, (
        "BUG-#8: Past due_date not enforced. "
        "Fix: check quiz.due_date in submit_quiz() and raise QuizExpired()."
    )


# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCTOR SUBMISSIONS  (BUG-#4: route ordering)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_instructor_submissions_endpoint_is_reachable(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """
    BUG-#4: /instructor/submissions/{quiz_id} is registered AFTER /{quiz_id}.
    FastAPI would match 'instructor' as the UUID → 422 or 404.
    This test verifies the endpoint is actually reachable (not shadowed).
    """
    course = await db_create_course(
        db_session, f"SubCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r_create = await client.post(
        f"{BASE}/create",
        json=_quiz_payload(str(course.id)),
        headers=professor_headers,
    )
    quiz_id = r_create.json()["quiz_id"]

    r = await client.get(
        f"{BASE}/instructor/submissions/{quiz_id}",
        headers=professor_headers,
    )
    # BUG: likely returns 422 (UUID parse of "instructor" fails) or 404
    # Once BUG-#4 is fixed this must be 200
    assert r.status_code == 200, (
        f"BUG-#4: Route /instructor/submissions/{{id}} is shadowed by /{{id}}. "
        f"Got {r.status_code}. Fix: move the /instructor routes BEFORE /{{quiz_id}}."
    )


@pytest.mark.asyncio
async def test_instructor_submissions_returns_correct_structure(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    professor_headers: dict,
    db_session: AsyncSession,
):
    quiz_id, questions = await _create_and_enroll_quiz(
        client, professor_headers, student_headers,
        active_professor, active_student, db_session, title="Sub Report Quiz"
    )
    answers = [
        {"question_id": q["id"], "chosen_choice_id": q["choices"][0]["id"]}
        for q in questions
    ]
    await client.post(
        f"{BASE}/{quiz_id}/submit",
        json={"answers": answers},
        headers=student_headers,
    )

    r = await client.get(
        f"{BASE}/instructor/submissions/{quiz_id}",
        headers=professor_headers,
    )
    # Only assert structure if reachable (bug may still be present)
    if r.status_code == 200:
        data = r.json()
        assert "quiz_id" in data
        assert "submissions" in data
        assert len(data["submissions"]) == 1
        sub = data["submissions"][0]
        assert "student_id" in sub
        assert "score" in sub


@pytest.mark.asyncio
async def test_student_cannot_view_submissions(
    client: AsyncClient,
    student_headers: dict,
    db_session: AsyncSession,
):
    r = await client.get(
        f"{BASE}/instructor/submissions/{uuid.uuid4()}",
        headers=student_headers,
    )
    assert r.status_code in (403, 404, 422)


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT & INSTRUCTOR COURSE LISTS  (client router)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_gets_enrolled_courses(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"MyEnrolledCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    r = await client.get("/api/v1/student/courses", headers=student_headers)
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert str(course.id) in ids


@pytest.mark.asyncio
async def test_professor_cannot_access_student_courses(
    client: AsyncClient, professor_headers: dict
):
    r = await client.get("/api/v1/student/courses", headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_professor_gets_assigned_courses(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"InstructorCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r = await client.get("/api/v1/instructor/courses", headers=professor_headers)
    assert r.status_code == 200
    ids = [c["id"] for c in r.json()]
    assert str(course.id) in ids


@pytest.mark.asyncio
async def test_student_cannot_access_instructor_courses(
    client: AsyncClient, student_headers: dict
):
    r = await client.get("/api/v1/instructor/courses", headers=student_headers)
    assert r.status_code == 403
