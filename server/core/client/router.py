"""
Client router — aggregator for student and professor features.
"""
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from core.db.main import get_session
from core.dependencies import RoleChecker
from core.db.models import User, Course, Enrollment, Section, CourseProfessor

# Sub-routers
from core.client.attendance.router import attendance_router
from core.client.quiz.router import quiz_router

client_router = APIRouter()

# Include sub-routers
client_router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
client_router.include_router(quiz_router, prefix="/quiz", tags=["Quiz"])


# ────────────────────────────────────────────────────────
# STUDENT — Dashboard / Courses
# ────────────────────────────────────────────────────────

@client_router.get("/student/courses", tags=["Student"])
async def get_student_courses(
    user: User = Depends(RoleChecker(["student"])),
    session: AsyncSession = Depends(get_session),
):
    """Get all courses the student is enrolled in."""
    result = await session.execute(
        select(Course, Enrollment)
        .join(Enrollment, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == user.id)
    )
    rows = result.all()

    courses = []
    for course, enrollment in rows:
        courses.append({
            "id": str(course.id),
            "name": course.name,
            "year": course.year,
            "department_id": str(course.department_id) if course.department_id else None,
            "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
        })

    return courses


# ────────────────────────────────────────────────────────
# INSTRUCTOR — Courses
# ────────────────────────────────────────────────────────

@client_router.get("/instructor/courses", tags=["Instructor"])
async def get_instructor_courses(
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Get courses assigned to the current professor."""
    result = await session.execute(
        select(Course)
        .join(CourseProfessor)
        .where(CourseProfessor.professor_id == user.id)
    )
    courses = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "year": c.year,
            "department_id": str(c.department_id) if c.department_id else None,
        }
        for c in courses
    ]


@client_router.get("/sections", tags=["Common"])
async def get_sections(
    session: AsyncSession = Depends(get_session),
):
    """Get all available sections."""
    from core.db.models import Section
    result = await session.execute(select(Section))
    sections = result.scalars().all()
    return [{"id": str(s.id), "name": s.name} for s in sections]
