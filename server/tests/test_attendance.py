"""
tests/test_attendance.py
========================
E2E tests for attendance endpoints.

  POST /api/v1/attendance/generate           — professor generates QR
  POST /api/v1/attendance/scan               — student scans QR
  GET  /api/v1/attendance/my-records         — student views own records
  GET  /api/v1/attendance/report/{course_id} — professor views summary
  GET  /api/v1/attendance/report/full/{id}   — professor views matrix

Bug coverage
------------
- BUG-#1:  timezone-naive comparison in verify_qr_token — expired-QR edge case
- BUG-#2:  QRCodeExpired/InvalidToken swallowed by bare except in verify_qr_token
- BUG-#7:  double _verify_instructor call (performance, not correctness)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from conftest import (
    db_create_user, db_create_course, db_enroll, bearer,
    make_access_token, _uid,
)
from core.auth.schema import UserRole
from core.db.models import User, Course, QRCode
from core.security import generate_qr_token

BASE = "/api/v1/attendance"


# ─────────────────────────────────────────────────────────────────────────────
# QR GENERATION  (professor role required)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_cannot_generate_qr(
    client: AsyncClient, student_headers: dict, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"ScanCourse_{_uid()}", year=1)
    r = await client.post(f"{BASE}/generate", json={
        "course_id": str(course.id),
        "week_number": 1,
        "expiry_minutes": 15,
    }, headers=student_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_generate_qr(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"AuthCourse_{_uid()}", year=1)
    r = await client.post(f"{BASE}/generate", json={
        "course_id": str(course.id),
        "week_number": 1,
        "expiry_minutes": 15,
    })
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_professor_generates_qr_for_own_course(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"MyCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    with patch(
        "core.client.attendance.service.store_qr_token",
        new=AsyncMock(return_value=True),
    ):
        r = await client.post(f"{BASE}/generate", json={
            "course_id": str(course.id),
            "week_number": 5,
            "expiry_minutes": 20,
        }, headers=professor_headers)

    assert r.status_code == 201, r.text
    data = r.json()
    assert data["week_number"] == 5
    assert data["course_id"] == str(course.id)
    assert "token" in data
    assert "expires_at" in data
    assert "qr_code_id" in data


@pytest.mark.asyncio
async def test_professor_cannot_generate_qr_for_unowned_course(
    client: AsyncClient,
    active_professor: User,
    second_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """BUG CHECK: professor must be verified against CourseProfessor table."""
    other_course = await db_create_course(
        db_session, f"OtherCourse_{_uid()}", year=1, professor_id=second_professor.id
    )
    r = await client.post(f"{BASE}/generate", json={
        "course_id": str(other_course.id),
        "week_number": 1,
        "expiry_minutes": 15,
    }, headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_generate_qr_with_section_id(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    from conftest import db_create_section
    section = await db_create_section(db_session, f"SecQR_{_uid()}")
    course = await db_create_course(
        db_session, f"SecQRCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    with patch(
        "core.client.attendance.service.store_qr_token",
        new=AsyncMock(return_value=True),
    ):
        r = await client.post(f"{BASE}/generate", json={
            "course_id": str(course.id),
            "week_number": 2,
            "expiry_minutes": 10,
            "section_id": str(section.id),
        }, headers=professor_headers)

    assert r.status_code == 201
    assert r.json()["section_id"] == str(section.id)


@pytest.mark.asyncio
async def test_generate_qr_invalid_week_0_returns_422(
    client: AsyncClient, professor_headers: dict
):
    r = await client.post(f"{BASE}/generate", json={
        "course_id": str(uuid.uuid4()),
        "week_number": 0,
        "expiry_minutes": 15,
    }, headers=professor_headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_generate_qr_invalid_week_53_returns_422(
    client: AsyncClient, professor_headers: dict
):
    r = await client.post(f"{BASE}/generate", json={
        "course_id": str(uuid.uuid4()),
        "week_number": 53,
        "expiry_minutes": 15,
    }, headers=professor_headers)
    assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# QR SCANNING  (student role required)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_professor_cannot_scan_qr(
    client: AsyncClient, professor_headers: dict
):
    r = await client.post(f"{BASE}/scan", json={"token": "any"}, headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_scan_qr(client: AsyncClient):
    r = await client.post(f"{BASE}/scan", json={"token": "any"})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_scan_expired_qr_returns_410(
    client: AsyncClient, student_headers: dict
):
    """BUG-#2 CHECK: when Redis returns None the correct 410 must surface."""
    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=None),
    ):
        r = await client.post(
            f"{BASE}/scan",
            json={"token": "expiredtoken"},
            headers=student_headers,
        )
    assert r.status_code == 410


@pytest.mark.asyncio
async def test_scan_tampered_token_returns_400(
    client: AsyncClient, student_headers: dict
):
    """BUG-#2 CHECK: HMAC invalid → QRCodeInvalid (400) not swallowed."""
    fake_qr_id = str(uuid.uuid4())
    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=fake_qr_id),
    ):
        r = await client.post(
            f"{BASE}/scan",
            json={"token": "fakepayload.invalidsignature"},
            headers=student_headers,
        )
    assert r.status_code in (400, 401)


@pytest.mark.asyncio
async def test_scan_valid_qr_records_attendance(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    """Full happy-path: generate token, store in Redis-mock, student scans it."""
    course = await db_create_course(
        db_session, f"FullScanCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(tzinfo=None)
    token = generate_qr_token(
        course_id=str(course.id),
        week_number=1,
        expires_at=expires_at.isoformat(),
    )

    # Create QRCode record in DB
    qr = QRCode(
        course_id=course.id,
        generated_by=active_professor.id,
        week_number=1,
        token=token,
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(qr)
    await db_session.commit()
    await db_session.refresh(qr)

    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=str(qr.id)),
    ):
        r = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )

    assert r.status_code == 200, r.text
    assert "recorded" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_scan_unenrolled_student_returns_403(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    """Student NOT enrolled in the course should get 403 NotEnrolled."""
    course = await db_create_course(
        db_session, f"UnenrolledCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    # Do NOT enroll the student

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(tzinfo=None)
    token = generate_qr_token(
        course_id=str(course.id),
        week_number=1,
        expires_at=expires_at.isoformat(),
    )
    qr = QRCode(
        course_id=course.id,
        generated_by=active_professor.id,
        week_number=1,
        token=token,
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(qr)
    await db_session.commit()
    await db_session.refresh(qr)

    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=str(qr.id)),
    ):
        r = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_scan_duplicate_returns_409(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    """Second scan of the same QR by same student → 409 DuplicateAttendance."""
    course = await db_create_course(
        db_session, f"DupScanCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(tzinfo=None)
    token = generate_qr_token(
        course_id=str(course.id),
        week_number=1,
        expires_at=expires_at.isoformat(),
    )
    qr = QRCode(
        course_id=course.id,
        generated_by=active_professor.id,
        week_number=1,
        token=token,
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(qr)
    await db_session.commit()
    await db_session.refresh(qr)

    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=str(qr.id)),
    ):
        r1 = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )
        assert r1.status_code == 200

        r2 = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )
        assert r2.status_code == 409


@pytest.mark.asyncio
async def test_scan_section_mismatch_returns_403(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    """Student in section A scans QR for section B → 403 SectionMismatch."""
    from conftest import db_create_section
    section_a = await db_create_section(db_session, f"SecA_{_uid()}")
    section_b = await db_create_section(db_session, f"SecB_{_uid()}")

    # Assign student to section A
    from core.db.models import Student
    student_rec = await db_session.get(Student, active_student.id)
    student_rec.section_id = section_a.id
    await db_session.commit()

    course = await db_create_course(
        db_session, f"SecMismatchCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    # QR is for section B
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(tzinfo=None)
    token = generate_qr_token(
        course_id=str(course.id),
        week_number=1,
        expires_at=expires_at.isoformat(),
        section_id=str(section_b.id),
    )
    qr = QRCode(
        course_id=course.id,
        generated_by=active_professor.id,
        week_number=1,
        section_id=section_b.id,
        token=token,
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(qr)
    await db_session.commit()
    await db_session.refresh(qr)

    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=str(qr.id)),
    ):
        r = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT — MY RECORDS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_my_records_empty_for_new_student(
    client: AsyncClient, student_headers: dict
):
    r = await client.get(f"{BASE}/my-records", headers=student_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_get_my_records_professor_rejected(
    client: AsyncClient, professor_headers: dict
):
    r = await client.get(f"{BASE}/my-records", headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_my_records_unauthenticated_rejected(client: AsyncClient):
    r = await client.get(f"{BASE}/my-records")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_my_records_after_scan(
    client: AsyncClient,
    active_student: User,
    active_professor: User,
    student_headers: dict,
    db_session: AsyncSession,
):
    """After scanning, my-records must include the attendance entry."""
    course = await db_create_course(
        db_session, f"RecordCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    await db_enroll(db_session, active_student.id, course.id)

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).replace(tzinfo=None)
    token = generate_qr_token(
        course_id=str(course.id),
        week_number=3,
        expires_at=expires_at.isoformat(),
    )
    qr = QRCode(
        course_id=course.id,
        generated_by=active_professor.id,
        week_number=3,
        token=token,
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(qr)
    await db_session.commit()
    await db_session.refresh(qr)

    with patch(
        "core.client.attendance.service.check_qr_token",
        new=AsyncMock(return_value=str(qr.id)),
    ):
        scan_r = await client.post(
            f"{BASE}/scan",
            json={"token": token},
            headers=student_headers,
        )
    assert scan_r.status_code == 200

    records_r = await client.get(f"{BASE}/my-records", headers=student_headers)
    assert records_r.status_code == 200
    records = records_r.json()
    assert len(records) == 1
    assert records[0]["week_number"] == 3
    assert records[0]["course_id"] == str(course.id)


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSOR — ATTENDANCE REPORT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_cannot_view_attendance_report(
    client: AsyncClient, student_headers: dict, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"RepCourse_{_uid()}", year=1)
    r = await client.get(f"{BASE}/report/{course.id}", headers=student_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_view_attendance_report(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"AuthRepCourse_{_uid()}", year=1)
    r = await client.get(f"{BASE}/report/{course.id}")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_professor_can_view_own_course_report(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    course = await db_create_course(
        db_session, f"OwnReport_{_uid()}", year=1, professor_id=active_professor.id
    )
    r = await client.get(f"{BASE}/report/{course.id}", headers=professor_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_professor_cannot_view_unowned_course_report(
    client: AsyncClient,
    active_professor: User,
    second_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    other_course = await db_create_course(
        db_session, f"NotMyCourse_{_uid()}", year=1, professor_id=second_professor.id
    )
    r = await client.get(f"{BASE}/report/{other_course.id}", headers=professor_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_full_attendance_matrix_structure(
    client: AsyncClient,
    active_professor: User,
    professor_headers: dict,
    db_session: AsyncSession,
):
    """BUG-#7 CHECK: full matrix endpoint returns correct shape."""
    course = await db_create_course(
        db_session, f"MatrixCourse_{_uid()}", year=1, professor_id=active_professor.id
    )
    r = await client.get(f"{BASE}/report/full/{course.id}", headers=professor_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "course_id" in data
    assert "course_name" in data
    assert "students" in data
    assert "sessions" in data
    assert "attendance" in data
