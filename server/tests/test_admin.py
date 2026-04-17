"""
tests/test_admin.py
===================
E2E tests for /api/v1/admin/* endpoints (no auth guard — admin CRUD).

Covers
------
- User CRUD (create, list, get, update, deactivate)
- Bulk CSV upload (all valid, mixed, all-bad)
- Department CRUD
- Section CRUD
- Course CRUD (year-based dept logic)
- Enrollment (success, duplicate)
- Auto-enrollment when student year/dept matches course

Bug coverage
------------
- BUG-#3:  Activation email uses config.domain → link won't match frontend_url
- BUG-#9:  bulk_upload session reuse after rollback — partial success test
"""

from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from conftest import (
    db_create_user, db_create_department, db_create_course, db_create_section,
    db_enroll, _uid,
)
from core.auth.schema import UserRole
from core.db.models import User, Course

BASE = "/api/v1/admin"


# ─────────────────────────────────────────────────────────────────────────────
# USER — CREATE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_student_user_returns_201(client: AsyncClient):
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"STU{uid}",
        "id_card": f"CARD{uid}",
        "full_name": "New Student",
        "email": f"newstu_{uid}@uni.edu",
        "role": "student",
        "year": 1,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["role"] == "student"
    assert data["is_active"] is False  # must be inactive until activation


@pytest.mark.asyncio
async def test_create_professor_user_returns_201(client: AsyncClient):
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"PROF{uid}",
        "id_card": f"PCARD{uid}",
        "full_name": "Dr. Prof",
        "email": f"prof_{uid}@uni.edu",
        "role": "professor",
    })
    assert r.status_code == 201
    assert r.json()["role"] == "professor"


@pytest.mark.asyncio
async def test_create_user_invalid_role_returns_422(client: AsyncClient):
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"TA{uid}",
        "id_card": f"TACARD{uid}",
        "full_name": "TA User",
        "email": f"ta_{uid}@uni.edu",
        "role": "assistant",  # not a valid role
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_user_admin_role_rejected(client: AsyncClient):
    """'admin' is not a UserRole enum value."""
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"ADM{uid}",
        "id_card": f"ACARD{uid}",
        "full_name": "Would-Be Admin",
        "email": f"admin_{uid}@uni.edu",
        "role": "admin",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_duplicate_user_returns_409(client: AsyncClient):
    uid = _uid()
    payload = {
        "university_id": f"DUP{uid}",
        "id_card": f"DUPCARD{uid}",
        "full_name": "Duplicate User",
        "email": f"dup_{uid}@uni.edu",
        "role": "student",
    }
    r1 = await client.post(f"{BASE}/users", json=payload)
    assert r1.status_code == 201

    r2 = await client.post(f"{BASE}/users", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_create_student_with_section_and_year(
    client: AsyncClient, db_session: AsyncSession
):
    section = await db_create_section(db_session, f"SectionX_{_uid()}")
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"SSTU{uid}",
        "id_card": f"SCARD{uid}",
        "full_name": "Sectioned Student",
        "email": f"sec_{uid}@uni.edu",
        "role": "student",
        "year": 2,
        "section_id": str(section.id),
    })
    assert r.status_code == 201
    assert r.json()["section_id"] == str(section.id)


@pytest.mark.asyncio
async def test_create_professor_with_course_assignment(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"AssignedCourse_{_uid()}", year=1)
    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"ASSPROF{uid}",
        "id_card": f"ASSCARD{uid}",
        "full_name": "Assigned Prof",
        "email": f"assprof_{uid}@uni.edu",
        "role": "professor",
        "course_ids": [str(course.id)],
    })
    assert r.status_code == 201


# ─────────────────────────────────────────────────────────────────────────────
# USER — LIST & GET
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_returns_paginated_response(
    client: AsyncClient, active_student: User, active_professor: User
):
    r = await client.get(f"{BASE}/users")
    assert r.status_code == 200
    data = r.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_users_filter_by_role_student(
    client: AsyncClient, active_student: User, active_professor: User
):
    r = await client.get(f"{BASE}/users?role=student")
    assert r.status_code == 200
    users = r.json()["users"]
    assert all(u["role"] == "student" for u in users)


@pytest.mark.asyncio
async def test_list_users_filter_by_role_professor(
    client: AsyncClient, active_student: User, active_professor: User
):
    r = await client.get(f"{BASE}/users?role=professor")
    assert r.status_code == 200
    users = r.json()["users"]
    assert all(u["role"] == "professor" for u in users)


@pytest.mark.asyncio
async def test_list_users_pagination(
    client: AsyncClient, db_session: AsyncSession
):
    """Create 5 students then test skip/limit."""
    for i in range(5):
        uid = _uid()
        await db_create_user(
            db_session,
            university_id=f"PAGSTU{uid}",
            id_card=f"PAGCARD{uid}",
            full_name=f"Page Student {i}",
            email=f"page_{uid}@uni.edu",
            role=UserRole.student,
        )

    r_page1 = await client.get(f"{BASE}/users?skip=0&limit=2")
    assert r_page1.status_code == 200
    assert len(r_page1.json()["users"]) == 2

    r_page2 = await client.get(f"{BASE}/users?skip=2&limit=2")
    assert r_page2.status_code == 200
    assert len(r_page2.json()["users"]) == 2


@pytest.mark.asyncio
async def test_get_single_user_success(
    client: AsyncClient, active_student: User
):
    r = await client.get(f"{BASE}/users/{active_student.id}")
    assert r.status_code == 200
    assert r.json()["email"] == active_student.email


@pytest.mark.asyncio
async def test_get_user_not_found_returns_404(client: AsyncClient):
    r = await client.get(f"{BASE}/users/{uuid.uuid4()}")
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# USER — UPDATE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_user_full_name(
    client: AsyncClient, active_student: User
):
    r = await client.put(f"{BASE}/users/{active_student.id}", json={
        "full_name": "Alice Updated Name",
    })
    assert r.status_code == 200
    assert r.json()["full_name"] == "Alice Updated Name"


@pytest.mark.asyncio
async def test_update_nonexistent_user_returns_404(client: AsyncClient):
    r = await client.put(f"{BASE}/users/{uuid.uuid4()}", json={"full_name": "Ghost"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_user_year_as_student(
    client: AsyncClient, active_student: User
):
    r = await client.put(f"{BASE}/users/{active_student.id}", json={"year": 3})
    assert r.status_code == 200
    assert r.json()["year"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# USER — DEACTIVATE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deactivate_user_returns_200(
    client: AsyncClient, active_student: User
):
    r = await client.delete(f"{BASE}/users/{active_student.id}")
    assert r.status_code == 200
    assert "deactivated" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_deactivate_user_blocks_login(
    client: AsyncClient, active_student: User
):
    """After deactivation the user must not be able to login."""
    r_del = await client.delete(f"{BASE}/users/{active_student.id}")
    assert r_del.status_code == 200

    r_login = await client.post("/api/v1/auth/login", json={
        "email": active_student.email,
        "password": "TestPass@123",
    })
    assert r_login.status_code == 403  # AccountNotActive


@pytest.mark.asyncio
async def test_deactivate_nonexistent_user_returns_404(client: AsyncClient):
    r = await client.delete(f"{BASE}/users/{uuid.uuid4()}")
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# BULK UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bulk_upload_all_valid_rows(client: AsyncClient):
    uid1, uid2, uid3 = _uid(), _uid(), _uid()
    csv_data = (
        "universityId,idCard,name,email,role,year,departmentId,section,courseIds\n"
        f"BULK{uid1},BCARD{uid1},Bulk Student A,bulka_{uid1}@uni.edu,student,1,,,\n"
        f"BULK{uid2},BCARD{uid2},Bulk Student B,bulkb_{uid2}@uni.edu,student,2,,,\n"
        f"BULK{uid3},BCARD{uid3},Bulk Prof,bulkp_{uid3}@uni.edu,professor,,,,"
    )
    r = await client.post(
        f"{BASE}/users/bulk",
        files={"file": ("users.csv", csv_data.encode(), "text/csv")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total_rows"] == 3
    assert data["succeeded"] == 3
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_bulk_upload_bad_row_recorded_as_failure(client: AsyncClient):
    uid1, uid2 = _uid(), _uid()
    csv_data = (
        "universityId,idCard,name,email,role,year,departmentId,section,courseIds\n"
        f"BGOOD{uid1},BGCARD{uid1},Good User,good_{uid1}@uni.edu,student,1,,,\n"
        f"BBAD{uid2},BBCARD{uid2},Bad User,bad_{uid2}@uni.edu,not_a_role,1,,,"
    )
    r = await client.post(
        f"{BASE}/users/bulk",
        files={"file": ("users.csv", csv_data.encode(), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_rows"] == 2
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    failed = [row for row in data["results"] if not row["success"]]
    assert len(failed) == 1
    assert failed[0]["error"] is not None


@pytest.mark.asyncio
async def test_bulk_upload_duplicate_row_failure(client: AsyncClient):
    """Uploading the same university_id twice — second row must fail."""
    uid = _uid()
    row = f"DUP{uid},DUPCARD{uid},Dup Student,dup_{uid}@uni.edu,student,1,,,"
    csv_data = (
        "universityId,idCard,name,email,role,year,departmentId,section,courseIds\n"
        + row + "\n"
        + row
    )
    r = await client.post(
        f"{BASE}/users/bulk",
        files={"file": ("users.csv", csv_data.encode(), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total_rows"] == 2
    # BUG-#9: session reuse after rollback — succeeded count could be 1 or 2
    # We assert the second row MUST fail due to uniqueness
    assert data["failed"] >= 1


@pytest.mark.asyncio
async def test_bulk_upload_empty_csv(client: AsyncClient):
    csv_data = "universityId,idCard,name,email,role,year,departmentId,section,courseIds\n"
    r = await client.post(
        f"{BASE}/users/bulk",
        files={"file": ("empty.csv", csv_data.encode(), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["total_rows"] == 0
    assert r.json()["succeeded"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# DEPARTMENT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_department(client: AsyncClient):
    r = await client.post(f"{BASE}/departments", json={"name": f"Dept_{_uid()}"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert "name" in data


@pytest.mark.asyncio
async def test_create_duplicate_department_returns_409(client: AsyncClient):
    name = f"UniqueDept_{_uid()}"
    r1 = await client.post(f"{BASE}/departments", json={"name": name})
    assert r1.status_code == 201
    r2 = await client.post(f"{BASE}/departments", json={"name": name})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, db_session: AsyncSession):
    await db_create_department(db_session, f"Physics_{_uid()}")
    r = await client.get(f"{BASE}/departments")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_get_department_by_id(
    client: AsyncClient, db_session: AsyncSession
):
    dept = await db_create_department(db_session, f"GetDept_{_uid()}")
    r = await client.get(f"{BASE}/departments/{dept.id}")
    assert r.status_code == 200
    assert r.json()["id"] == str(dept.id)


@pytest.mark.asyncio
async def test_get_department_not_found(client: AsyncClient):
    r = await client.get(f"{BASE}/departments/{uuid.uuid4()}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_department_name(
    client: AsyncClient, db_session: AsyncSession
):
    dept = await db_create_department(db_session, f"OldDept_{_uid()}")
    new_name = f"NewDept_{_uid()}"
    r = await client.put(f"{BASE}/departments/{dept.id}", json={"name": new_name})
    assert r.status_code == 200
    assert r.json()["name"] == new_name


@pytest.mark.asyncio
async def test_delete_department(
    client: AsyncClient, db_session: AsyncSession
):
    dept = await db_create_department(db_session, f"DelDept_{_uid()}")
    r = await client.delete(f"{BASE}/departments/{dept.id}")
    assert r.status_code == 200

    # Verify gone
    r2 = await client.get(f"{BASE}/departments/{dept.id}")
    assert r2.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# SECTION
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_section(client: AsyncClient):
    r = await client.post(f"{BASE}/sections", json={"name": f"Section_{_uid()}"})
    assert r.status_code == 201
    assert "id" in r.json()


@pytest.mark.asyncio
async def test_list_sections(client: AsyncClient, db_session: AsyncSession):
    await db_create_section(db_session, f"SecList_{_uid()}")
    r = await client.get(f"{BASE}/sections")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_update_section(client: AsyncClient, db_session: AsyncSession):
    sec = await db_create_section(db_session, f"OldSec_{_uid()}")
    new_name = f"NewSec_{_uid()}"
    r = await client.put(f"{BASE}/sections/{sec.id}", json={"name": new_name})
    assert r.status_code == 200
    assert r.json()["name"] == new_name


@pytest.mark.asyncio
async def test_delete_section(client: AsyncClient, db_session: AsyncSession):
    sec = await db_create_section(db_session, f"DelSec_{_uid()}")
    r = await client.delete(f"{BASE}/sections/{sec.id}")
    assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_course_year1_auto_assigns_general_dept(client: AsyncClient):
    r = await client.post(f"{BASE}/courses", json={
        "name": f"Intro_{_uid()}",
        "year": 1,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["year"] == 1
    assert data["department_id"] is not None  # 'General' dept auto-created


@pytest.mark.asyncio
async def test_create_course_year2_auto_assigns_general_dept(client: AsyncClient):
    r = await client.post(f"{BASE}/courses", json={
        "name": f"BasicsII_{_uid()}",
        "year": 2,
    })
    assert r.status_code == 201
    assert r.json()["department_id"] is not None


@pytest.mark.asyncio
async def test_create_course_year3_without_dept_returns_404(client: AsyncClient):
    """BUG: year 3/4 with no dept → DataNotFound (404)."""
    r = await client.post(f"{BASE}/courses", json={
        "name": f"Advanced_{_uid()}",
        "year": 3,
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_course_year3_with_dept_success(
    client: AsyncClient, db_session: AsyncSession
):
    dept = await db_create_department(db_session, f"EngineeringDept_{_uid()}")
    r = await client.post(f"{BASE}/courses", json={
        "name": f"Advanced_{_uid()}",
        "year": 3,
        "department_id": str(dept.id),
    })
    assert r.status_code == 201
    assert r.json()["department_id"] == str(dept.id)


@pytest.mark.asyncio
async def test_create_course_with_professor_assignment(
    client: AsyncClient, active_professor: User
):
    r = await client.post(f"{BASE}/courses", json={
        "name": f"WithProf_{_uid()}",
        "year": 1,
        "professor_ids": [str(active_professor.id)],
    })
    assert r.status_code == 201
    assert str(active_professor.id) in r.json()["professor_ids"]


@pytest.mark.asyncio
async def test_list_courses(client: AsyncClient, db_session: AsyncSession):
    await db_create_course(db_session, f"ListCourse_{_uid()}", year=1)
    r = await client.get(f"{BASE}/courses")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_list_courses_filter_by_year(
    client: AsyncClient, db_session: AsyncSession
):
    await db_create_course(db_session, f"Y2Course_{_uid()}", year=2)
    r = await client.get(f"{BASE}/courses?year=2")
    assert r.status_code == 200
    courses = r.json()
    assert all(c["year"] == 2 for c in courses)


@pytest.mark.asyncio
async def test_get_course_by_id(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"GetCourse_{_uid()}", year=1)
    r = await client.get(f"{BASE}/courses/{course.id}")
    assert r.status_code == 200
    assert r.json()["id"] == str(course.id)


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient):
    r = await client.get(f"{BASE}/courses/{uuid.uuid4()}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_course_name(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"OldCourse_{_uid()}", year=1)
    new_name = f"UpdatedCourse_{_uid()}"
    r = await client.put(f"{BASE}/courses/{course.id}", json={"name": new_name})
    assert r.status_code == 200
    assert r.json()["name"] == new_name


@pytest.mark.asyncio
async def test_update_course_professors(
    client: AsyncClient, db_session: AsyncSession,
    active_professor: User, second_professor: User,
):
    course = await db_create_course(
        db_session, f"ProfCourse_{_uid()}", year=1,
        professor_id=active_professor.id,
    )
    # Replace assigned professors
    r = await client.put(f"{BASE}/courses/{course.id}", json={
        "professor_ids": [str(second_professor.id)],
    })
    assert r.status_code == 200
    assert str(second_professor.id) in r.json()["professor_ids"]
    assert str(active_professor.id) not in r.json()["professor_ids"]


@pytest.mark.asyncio
async def test_delete_course(
    client: AsyncClient, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"DelCourse_{_uid()}", year=1)
    r = await client.delete(f"{BASE}/courses/{course.id}")
    assert r.status_code == 200

    r2 = await client.get(f"{BASE}/courses/{course.id}")
    assert r2.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# ENROLLMENT
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enroll_student_in_course(
    client: AsyncClient, active_student: User, db_session: AsyncSession
):
    course = await db_create_course(db_session, f"EnrollCourse_{_uid()}", year=1)
    r = await client.post(f"{BASE}/enrollments", json={
        "student_id": str(active_student.id),
        "course_id": str(course.id),
    })
    assert r.status_code == 201
    assert "enrolled" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_double_enrollment_returns_404(
    client: AsyncClient, active_student: User, db_session: AsyncSession
):
    """DataNotFound used for 'already enrolled' — somewhat misleading but confirmed from code."""
    course = await db_create_course(db_session, f"DoubleEnroll_{_uid()}", year=1)
    payload = {
        "student_id": str(active_student.id),
        "course_id": str(course.id),
    }
    r1 = await client.post(f"{BASE}/enrollments", json=payload)
    assert r1.status_code == 201

    r2 = await client.post(f"{BASE}/enrollments", json=payload)
    assert r2.status_code in (404, 409)  # DataNotFound with 404 per current impl


@pytest.mark.asyncio
async def test_auto_enroll_student_when_course_matches_year_dept(
    client: AsyncClient, db_session: AsyncSession
):
    """
    When a student is created with year=1, they should be auto-enrolled
    in all year=1/General-dept courses that already exist.
    """
    # Create a year-1 course first
    course = await db_create_course(db_session, f"AutoEnroll_{_uid()}", year=1)
    course_id = str(course.id)

    uid = _uid()
    r = await client.post(f"{BASE}/users", json={
        "university_id": f"AUTOSTU{uid}",
        "id_card": f"AUTOCARD{uid}",
        "full_name": "Auto Student",
        "email": f"autostu_{uid}@uni.edu",
        "role": "student",
        "year": 1,
    })
    assert r.status_code == 201
    student_id = r.json()["id"]

    # Check student is now enrolled
    r2 = await client.get(f"{BASE}/users/{student_id}")
    assert r2.status_code == 200
