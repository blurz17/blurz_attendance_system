"""
Admin service — user creation, bulk upload, course/department/section CRUD.
All functions are plain async — no class wrapper needed.
"""
import csv
import io
import uuid
import logging
from typing import Optional, List
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy import func
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from core.db.models import (
    User, Student, Professor,
    Department, Section, Course,
    Enrollment, CourseProfessor
)
from core.db.config import config
from core.auth.schema import UserRole
from core.admin.schema import CreateUserRequest, BulkUploadRowResult
from core.security import CreationSafeLink
from core.services.celery.celery_tasks import bg_send_mail
from core.errors import (
    UserAlreadyExists, UserNotFound, CourseNotFound,
    DepartmentNotFound, DataNotFound,
)

email_verification_link = CreationSafeLink(config.jwt_secret, "email_verification_link")


# ── USER MANAGEMENT ────────────────────────────

async def create_single_user(data: CreateUserRequest, session: AsyncSession) -> User:
    """Create a user + role-specific record. Sends activation email."""
    user = User(
        university_id=data.university_id,
        id_card=data.id_card,
        full_name=data.full_name,
        email=data.email.strip().lower(),
        hashed_password="NOT_SET",
        role=data.role,
        is_active=False,
    )
    session.add(user)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise UserAlreadyExists()

    # Create role-specific record
    if data.role == UserRole.student:
        year = data.year or 1
        session.add(Student(id=user.id, year=year, section_id=data.section_id, department_id=data.department_id))

        for course_id in (data.course_ids or []):
            session.add(Enrollment(student_id=user.id, course_id=course_id))

        await _auto_enroll_student(user.id, year, data.department_id, session)

    elif data.role == UserRole.professor:
        session.add(Professor(id=user.id))
        for course_id in (data.course_ids or []):
            session.add(CourseProfessor(course_id=course_id, professor_id=user.id))

    await session.commit()
    await session.refresh(user)
    _send_activation_email(user.email)
    return user


def _send_activation_email(email: str):
    """Trigger activation email via Celery."""
    try:
        token = email_verification_link.create_url({"email": email})
        link = f"{config.domain}/auth/verify/{token}"
        bg_send_mail.delay(
            rec=[email], sub="Activate Your Account",
            html_path="verify_message.html", data_var={"link": link},
        )
    except Exception as e:
        logging.error(f"Failed to send activation email to {email}: {e}")


async def bulk_upload_users(csv_content: str, session: AsyncSession) -> list[BulkUploadRowResult]:
    """Parse CSV and create users row by row. Each row is independent."""
    results = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row_num, row in enumerate(reader, start=2):
        try:
            course_ids = None
            if row.get("courseIds"):
                course_ids = [uuid.UUID(cid.strip()) for cid in row["courseIds"].split(";")]

            section_id = None
            if row.get("section"):
                sec = await session.execute(select(Section).where(Section.name == row["section"].strip()))
                section = sec.scalar_one_or_none()
                if section:
                    section_id = section.id

            department_id = uuid.UUID(row["departmentId"].strip()) if row.get("departmentId") else None

            data = CreateUserRequest(
                university_id=row["universityId"].strip(),
                id_card=row["idCard"].strip(),
                full_name=row["name"].strip(),
                email=row["email"].strip(),
                role=UserRole(row["role"].strip().lower()),
                year=int(row.get("year", 1)) if row.get("year") else None,
                section_id=section_id,
                department_id=department_id,
                course_ids=course_ids,
            )
            await create_single_user(data, session)
            results.append(BulkUploadRowResult(row_number=row_num, university_id=data.university_id, success=True))

        except Exception as e:
            await session.rollback()
            results.append(BulkUploadRowResult(
                row_number=row_num, university_id=row.get("universityId", ""), success=False, error=str(e),
            ))

    return results


async def list_users(
    session: AsyncSession, role: Optional[str] = None, skip: int = 0, limit: int = 50,
) -> tuple[list[dict], int]:
    """List users with optional role filter and pagination."""
    query = select(User)
    if role:
        query = query.where(User.role == role)

    total = (await session.execute(select(func.count()).select_from(query.subquery()))).scalar()

    result = await session.execute(query.offset(skip).limit(limit).order_by(User.created_at.desc()))
    users = result.scalars().all()

    user_list = []
    for u in users:
        u_dict = u.model_dump()
        if u.role == UserRole.student:
            student = (await session.execute(select(Student).where(Student.id == u.id))).scalar_one_or_none()
            if student:
                u_dict.update({"year": student.year, "section_id": student.section_id, "department_id": student.department_id})
        user_list.append(u_dict)

    return user_list, total


async def get_user(user_id: uuid.UUID, session: AsyncSession) -> dict:
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFound()

    user_dict = user.model_dump()
    if user.role == UserRole.student:
        student = await session.get(Student, user_id)
        if student:
            user_dict.update({"year": student.year, "section_id": student.section_id, "department_id": student.department_id})
    return user_dict


async def update_user(user_id: uuid.UUID, update_data: dict, session: AsyncSession) -> dict:
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFound()

    student_fields = {"year", "section_id", "department_id"}
    old_role = user.role

    # Update base user fields
    for key, value in update_data.items():
        if key not in student_fields and value is not None:
            setattr(user, key, value)

    # Handle role change
    if "role" in update_data and update_data["role"] != old_role:
        new_role = update_data["role"]
        if new_role == UserRole.student and not await session.get(Student, user_id):
            session.add(Student(id=user_id, year=1))
        elif new_role == UserRole.professor and not await session.get(Professor, user_id):
            session.add(Professor(id=user_id))

    # Update student fields
    if user.role == UserRole.student:
        student = await session.get(Student, user_id)
        if student:
            for key in student_fields:
                if key in update_data and update_data[key] is not None and getattr(student, key) != update_data[key]:
                    setattr(student, key, update_data[key])
            await _auto_enroll_student(user_id, student.year, student.department_id, session)

    await session.commit()
    return await get_user(user_id, session)


async def _auto_enroll_student(
    student_id: uuid.UUID, year: int, department_id: Optional[uuid.UUID], session: AsyncSession
):
    """Enroll student in all courses matching their year and department."""
    if not department_id and year in [1, 2]:
        gen = (await session.execute(select(Department).where(Department.name == "General"))).scalar_one_or_none()
        if gen:
            department_id = gen.id
            student = await session.get(Student, student_id)
            if student:
                student.department_id = department_id

    if not department_id:
        return

    courses = (await session.execute(
        select(Course).where(and_(Course.year == year, Course.department_id == department_id))
    )).scalars().all()

    existing = set((await session.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == student_id)
    )).scalars().all())

    for c in courses:
        if c.id not in existing:
            session.add(Enrollment(student_id=student_id, course_id=c.id))


async def deactivate_user(user_id: uuid.UUID, session: AsyncSession) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFound()
    user.is_active = False
    await session.commit()
    return user


# ── DEPARTMENT MANAGEMENT ──────────────────────

async def create_department(name: str, session: AsyncSession) -> Department:
    dept = Department(name=name)
    session.add(dept)
    try:
        await session.commit()
        await session.refresh(dept)
    except IntegrityError:
        await session.rollback()
        raise UserAlreadyExists()
    return dept


async def list_departments(session: AsyncSession) -> list[Department]:
    return (await session.execute(select(Department))).scalars().all()


async def get_department(dept_id: uuid.UUID, session: AsyncSession) -> Department:
    dept = await session.get(Department, dept_id)
    if not dept:
        raise DepartmentNotFound()
    return dept


async def update_department(dept_id: uuid.UUID, name: str, session: AsyncSession) -> Department:
    dept = await session.get(Department, dept_id)
    if not dept:
        raise DepartmentNotFound()
    dept.name = name
    await session.commit()
    await session.refresh(dept)
    return dept


async def delete_department(dept_id: uuid.UUID, session: AsyncSession) -> None:
    dept = await session.get(Department, dept_id)
    if not dept:
        raise DepartmentNotFound()
    await session.delete(dept)
    await session.commit()


# ── SECTION MANAGEMENT ─────────────────────────

async def create_section(name: str, session: AsyncSession) -> Section:
    section = Section(name=name)
    session.add(section)
    try:
        await session.commit()
        await session.refresh(section)
    except IntegrityError:
        await session.rollback()
        raise DataNotFound("Section with this name already exists")
    return section


async def list_sections(session: AsyncSession) -> list[Section]:
    return (await session.execute(select(Section))).scalars().all()


async def get_section(section_id: uuid.UUID, session: AsyncSession) -> Section:
    section = await session.get(Section, section_id)
    if not section:
        raise DataNotFound("Section not found")
    return section


async def update_section(section_id: uuid.UUID, name: str, session: AsyncSession) -> Section:
    section = await session.get(Section, section_id)
    if not section:
        raise DataNotFound("Section not found")
    section.name = name
    await session.commit()
    await session.refresh(section)
    return section


async def delete_section(section_id: uuid.UUID, session: AsyncSession) -> None:
    section = await session.get(Section, section_id)
    if not section:
        raise DataNotFound("Section not found")
    await session.delete(section)
    await session.commit()


# ── COURSE MANAGEMENT ──────────────────────────

async def create_course(
    name: str, year: int, department_id: uuid.UUID = None,
    professor_ids: List[uuid.UUID] = None, session: AsyncSession = None,
) -> dict:
    """Create a course. Year 1&2 → General dept. Year 3&4 → department required."""
    if year in (1, 2):
        general = await _get_or_create_general_dept(session)
        department_id = general.id
    elif year in (3, 4) and not department_id:
        raise DataNotFound("Department is required for year 3 and 4 courses")

    course = Course(name=name, year=year, department_id=department_id)
    session.add(course)
    await session.flush()

    for p_id in (professor_ids or []):
        session.add(CourseProfessor(course_id=course.id, professor_id=p_id))

    await session.commit()

    result = await session.execute(
        select(Course).where(Course.id == course.id).options(selectinload(Course.professors))
    )
    course = result.scalar_one()
    c_dict = course.model_dump()
    c_dict["professor_ids"] = [p.id for p in course.professors]
    return c_dict


async def _get_or_create_general_dept(session: AsyncSession) -> Department:
    dept = (await session.execute(select(Department).where(Department.name == "General"))).scalar_one_or_none()
    if not dept:
        dept = Department(name="General")
        session.add(dept)
        await session.flush()
    return dept


async def list_courses(
    session: AsyncSession, year: int = None, department_id: uuid.UUID = None,
) -> list[dict]:
    query = select(Course).options(selectinload(Course.professors))
    if year:
        query = query.where(Course.year == year)
    if department_id:
        query = query.where(Course.department_id == department_id)

    courses = (await session.execute(query)).scalars().all()
    return [
        {**c.model_dump(), "professor_ids": [p.id for p in c.professors]}
        for c in courses
    ]


async def get_course(course_id: uuid.UUID, session: AsyncSession) -> dict:
    result = await session.execute(
        select(Course).where(Course.id == course_id).options(selectinload(Course.professors))
    )
    course = result.scalar_one_or_none()
    if not course:
        raise CourseNotFound()
    c_dict = course.model_dump()
    c_dict["professor_ids"] = [p.id for p in course.professors]
    return c_dict


async def update_course(course_id: uuid.UUID, update_data: dict, session: AsyncSession) -> dict:
    result = await session.execute(
        select(Course).where(Course.id == course_id).options(selectinload(Course.professors))
    )
    course = result.scalar_one_or_none()
    if not course:
        raise CourseNotFound()

    professor_ids = update_data.pop("professor_ids", None)
    for key, value in update_data.items():
        if value is not None:
            setattr(course, key, value)

    if professor_ids is not None:
        await session.execute(sa.delete(CourseProfessor).where(CourseProfessor.course_id == course_id))
        for p_id in professor_ids:
            session.add(CourseProfessor(course_id=course_id, professor_id=p_id))

    await session.commit()

    result = await session.execute(
        select(Course).where(Course.id == course_id).options(selectinload(Course.professors))
    )
    course = result.scalar_one()
    return {**course.model_dump(), "professor_ids": [p.id for p in course.professors]}


async def delete_course(course_id: uuid.UUID, session: AsyncSession) -> None:
    course = await session.get(Course, course_id)
    if not course:
        raise CourseNotFound()
    await session.delete(course)
    await session.commit()


# ── ENROLLMENT ─────────────────────────────────

async def enroll_student(student_id: uuid.UUID, course_id: uuid.UUID, session: AsyncSession) -> Enrollment:
    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    session.add(enrollment)
    try:
        await session.commit()
        await session.refresh(enrollment)
    except IntegrityError:
        await session.rollback()
        raise DataNotFound("Student is already enrolled in this course")
    return enrollment
