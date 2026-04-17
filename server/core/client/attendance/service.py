"""
Attendance service — QR code generation with HMAC signing and Redis TTL,
attendance scanning with full validation.
"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, col
from sqlalchemy import and_

from core.db.models import (
    Course, QRCode, Student, Enrollment, Attendance, User, CourseProfessor
)
from core.db.redis import store_qr_token, check_qr_token
from core.security import generate_qr_token, verify_qr_token
from core.errors import (
    NotCourseInstructor, QRCodeExpired, QRCodeInvalid,
    NotEnrolled, SectionMismatch, DuplicateAttendance, DataNotFound,
)


# ── QR GENERATION ──────────────────────────────

async def generate_qr(
    course_id: uuid.UUID, week_number: int, expiry_minutes: int,
    generated_by: uuid.UUID, user_role: str,
    section_id: uuid.UUID = None, session: AsyncSession = None,
) -> QRCode:
    """Generate a QR code token for attendance."""
    await _verify_instructor(generated_by, course_id, user_role, session)

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)).replace(tzinfo=None)

    token = generate_qr_token(
        course_id=str(course_id), week_number=week_number,
        expires_at=expires_at.isoformat(), section_id=str(section_id) if section_id else None,
    )

    qr_code = QRCode(
        course_id=course_id, generated_by=generated_by, week_number=week_number,
        section_id=section_id, token=token, expires_at=expires_at, is_active=True,
    )
    session.add(qr_code)
    await session.commit()
    await session.refresh(qr_code)

    await store_qr_token(token=token, qr_code_id=str(qr_code.id), ttl_seconds=expiry_minutes * 60)
    return qr_code


async def _verify_instructor(user_id: uuid.UUID, course_id: uuid.UUID, role: str, session: AsyncSession):
    """Verify the user is a professor assigned to this course."""
    if role != "professor":
        raise NotCourseInstructor()

    result = await session.execute(
        select(CourseProfessor).where(
            and_(CourseProfessor.course_id == course_id, CourseProfessor.professor_id == user_id)
        )
    )
    if not result.scalar_one_or_none():
        raise NotCourseInstructor()


# ── QR SCANNING ────────────────────────────────

async def scan_qr(token: str, student_id: uuid.UUID, session: AsyncSession) -> Attendance:
    """
    Process a QR code scan:
    1. Check Redis (expired if missing)
    2. Verify HMAC signature
    3. Check enrollment
    4. Check section match
    5. Check duplicate
    6. Record attendance
    """
    # 1. Check Redis
    qr_code_id_str = await check_qr_token(token)
    if not qr_code_id_str:
        raise QRCodeExpired()
    qr_code_id = uuid.UUID(qr_code_id_str)

    # 2. Verify HMAC
    try:
        payload = verify_qr_token(token)
    except Exception:
        raise QRCodeInvalid()

    course_id = uuid.UUID(payload["course_id"])
    section_id = uuid.UUID(payload["section_id"]) if payload.get("section_id") else None

    # 3. Check enrollment
    enrollment = await session.execute(
        select(Enrollment).where(and_(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
    )
    if not enrollment.scalar_one_or_none():
        raise NotEnrolled()

    # 4. Check section match
    if section_id:
        student = await session.get(Student, student_id)
        if not student or str(student.section_id) != str(section_id):
            raise SectionMismatch()

    # 5. Check duplicate
    existing = await session.execute(
        select(Attendance).where(and_(Attendance.student_id == student_id, Attendance.qr_code_id == qr_code_id))
    )
    if existing.scalar_one_or_none():
        raise DuplicateAttendance()

    # 6. Record
    attendance = Attendance(student_id=student_id, qr_code_id=qr_code_id)
    session.add(attendance)
    await session.commit()
    await session.refresh(attendance)
    return attendance


# ── ATTENDANCE RECORDS ─────────────────────────

async def get_student_attendance(
    student_id: uuid.UUID, course_id: uuid.UUID = None, session: AsyncSession = None,
) -> list[dict]:
    """Get attendance records for a student, optionally filtered by course."""
    query = (
        select(Attendance, QRCode, Course)
        .join(QRCode, Attendance.qr_code_id == QRCode.id)
        .join(Course, QRCode.course_id == Course.id)
        .where(Attendance.student_id == student_id)
    )
    if course_id:
        query = query.where(QRCode.course_id == course_id)

    rows = (await session.execute(query.order_by(QRCode.course_id, QRCode.week_number))).all()

    return [
        {
            "id": att.id, "course_id": course.id, "course_name": course.name,
            "week_number": qr.week_number, "scanned_at": att.scanned_at,
        }
        for att, qr, course in rows
    ]


async def get_course_attendance_report(
    course_id: uuid.UUID, user_id: uuid.UUID, user_role: str, session: AsyncSession,
) -> list[dict]:
    """Get attendance report for all students in a course."""
    await _verify_instructor(user_id, course_id, user_role, session)
    # Reuse the full report
    result = await get_full_course_attendance_report(course_id, user_id, user_role, session)
    return result


async def get_full_course_attendance_report(
    course_id: uuid.UUID, instructor_id: uuid.UUID, instructor_role: str, session: AsyncSession,
) -> dict:
    """Get a complete attendance matrix (enrolled students vs all sessions)."""
    await _verify_instructor(instructor_id, course_id, instructor_role, session)

    course = await session.get(Course, course_id)
    if not course:
        raise DataNotFound()

    # Get enrolled students
    enrolled = (await session.execute(
        select(Student, User)
        .join(User, Student.id == User.id)
        .join(Enrollment, Student.id == Enrollment.student_id)
        .where(Enrollment.course_id == course_id)
        .order_by(User.full_name)
    )).all()

    # Get QR sessions
    qr_sessions = (await session.execute(
        select(QRCode).where(QRCode.course_id == course_id).order_by(QRCode.week_number, QRCode.created_at)
    )).scalars().all()

    # Get attendance records
    session_ids = [s.id for s in qr_sessions]
    student_ids = [s.id for s, u in enrolled]

    attendance_records = (await session.execute(
        select(Attendance).where(
            and_(col(Attendance.qr_code_id).in_(session_ids), col(Attendance.student_id).in_(student_ids))
        )
    )).scalars().all()

    # Build lookup: (student_id, qr_code_id) -> True
    present = {(str(a.student_id), str(a.qr_code_id)) for a in attendance_records}

    # Build matrix
    matrix = {}
    for s, u in enrolled:
        sid = str(s.id)
        matrix[sid] = {str(q.id): (sid, str(q.id)) in present for q in qr_sessions}

    return {
        "course_id": course.id,
        "course_name": course.name,
        "students": [{"id": s.id, "name": u.full_name, "university_id": u.university_id} for s, u in enrolled],
        "sessions": [{"id": s.id, "week_number": s.week_number, "generated_at": s.created_at} for s in qr_sessions],
        "attendance": matrix,
    }
