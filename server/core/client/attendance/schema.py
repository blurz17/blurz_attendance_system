"""
Attendance schemas — QR code generation and scanning.
"""
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────
# QR Code Generation
# ──────────────────────────────────────────────

class GenerateQRRequest(BaseModel):
    course_id: uuid.UUID
    week_number: int = Field(ge=1, le=52)
    expiry_minutes: int = Field(default=15, ge=1, le=1440)
    section_id: Optional[uuid.UUID] = None  # None = professor (all sections)


class GenerateQRResponse(BaseModel):
    qr_code_id: uuid.UUID
    token: str
    expires_at: datetime
    course_id: uuid.UUID
    week_number: int
    section_id: Optional[uuid.UUID] = None


# ──────────────────────────────────────────────
# QR Scanning
# ──────────────────────────────────────────────

class ScanQRRequest(BaseModel):
    token: str  # The scanned QR token string


class ScanQRResponse(BaseModel):
    message: str
    course_name: Optional[str] = None
    week_number: Optional[int] = None


# ──────────────────────────────────────────────
# Attendance Records
# ──────────────────────────────────────────────

class AttendanceRecord(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    course_name: Optional[str] = None
    week_number: int
    scanned_at: datetime

    model_config = {"from_attributes": True}


class CourseAttendanceSummary(BaseModel):
    course_id: uuid.UUID
    course_name: str
    total_weeks: int
    attended_weeks: int
    records: list[AttendanceRecord]


# ──────────────────────────────────────────────
# Instructor Report Matrix
# ──────────────────────────────────────────────

class AttendeeInfo(BaseModel):
    id: uuid.UUID
    name: str
    university_id: str


class SessionInfo(BaseModel):
    id: uuid.UUID
    week_number: int
    generated_at: datetime


class CourseAttendanceMatrix(BaseModel):
    course_id: uuid.UUID
    course_name: str
    students: list[AttendeeInfo]
    sessions: list[SessionInfo]
    attendance: dict[str, dict[str, bool]]  # student_id -> { session_id: is_present }
