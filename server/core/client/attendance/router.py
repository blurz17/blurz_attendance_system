"""
Attendance router — endpoints for students and professors.
"""
import uuid
from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db.main import get_session
from core.dependencies import RoleChecker
from core.db.models import User
from core.client.attendance.schema import (
    GenerateQRRequest, GenerateQRResponse,
    ScanQRRequest, ScanQRResponse,
    AttendanceRecord, CourseAttendanceMatrix,
)
from core.client.attendance import service as att_svc

attendance_router = APIRouter()


@attendance_router.post("/generate", response_model=GenerateQRResponse, status_code=status.HTTP_201_CREATED)
async def generate_qr_code(
    data: GenerateQRRequest,
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Generate a QR code for attendance."""
    qr = await att_svc.generate_qr(
        course_id=data.course_id, week_number=data.week_number,
        expiry_minutes=data.expiry_minutes, generated_by=user.id,
        user_role=user.role, section_id=data.section_id, session=session,
    )
    return GenerateQRResponse(
        qr_code_id=qr.id, token=qr.token, expires_at=qr.expires_at,
        course_id=qr.course_id, week_number=qr.week_number, section_id=qr.section_id,
    )


@attendance_router.post("/scan", response_model=ScanQRResponse)
async def scan_qr_code(
    data: ScanQRRequest,
    user: User = Depends(RoleChecker(["student"])),
    session: AsyncSession = Depends(get_session),
):
    """Scan a QR code to mark attendance."""
    await att_svc.scan_qr(token=data.token, student_id=user.id, session=session)
    return ScanQRResponse(message="Attendance recorded successfully")


@attendance_router.get("/my-records", response_model=list[AttendanceRecord])
async def get_my_attendance(
    course_id: uuid.UUID = None,
    user: User = Depends(RoleChecker(["student"])),
    session: AsyncSession = Depends(get_session),
):
    """Get the current student's attendance records."""
    return await att_svc.get_student_attendance(student_id=user.id, course_id=course_id, session=session)


@attendance_router.get("/report/{course_id}")
async def get_course_attendance_report(
    course_id: uuid.UUID,
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Get attendance report for all students in a course."""
    return await att_svc.get_course_attendance_report(
        course_id=course_id, user_id=user.id, user_role=user.role, session=session,
    )


@attendance_router.get("/report/full/{course_id}", response_model=CourseAttendanceMatrix)
async def get_full_course_attendance_report(
    course_id: uuid.UUID,
    user: User = Depends(RoleChecker(["professor"])),
    session: AsyncSession = Depends(get_session),
):
    """Get comprehensive attendance matrix for a course."""
    return await att_svc.get_full_course_attendance_report(
        course_id=course_id, instructor_id=user.id, instructor_role=user.role, session=session,
    )
