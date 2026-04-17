"""
conftest.py — Shared fixtures for the full E2E test suite.

Strategy
--------
• Real async PostgreSQL engine against a TEST database.
• Each test gets a rolled-back transaction → zero state leakage.
• Redis mocked via an in-memory dict → no Redis server needed.
• Celery tasks run eagerly (CELERY_TASK_ALWAYS_EAGER=True).
• Mail sending patched at the task level.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# ── 1. Point at test DB BEFORE importing anything from the app ────────────────
_TEST_DB_URL: str = os.environ.get(
    "TEST_DB_URL",
    os.environ.get(
        "DB_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/attendance_test",
    ),
)
os.environ["DB_URL"] = _TEST_DB_URL

# ── 2. In-memory Redis store (replaces the real Redis client) ─────────────────
_redis_store: dict[str, str] = {}

_fake_redis = MagicMock()
_fake_redis.ping = AsyncMock(return_value=True)
_fake_redis.set = AsyncMock(
    side_effect=lambda name, value="", ex=None: (
        _redis_store.update({name: str(value)}) or True
    )
)
_fake_redis.get = AsyncMock(side_effect=lambda name: _redis_store.get(name))
_fake_redis.delete = AsyncMock(
    side_effect=lambda *keys: sum(1 for k in keys if _redis_store.pop(k, None) is not None)
)

_redis_patcher = patch("core.db.redis.token_blacklist", _fake_redis)
_redis_patcher.start()

# ── 3. Patch mail so no SMTP is needed ───────────────────────────────────────
_mail_patcher = patch(
    "core.services.celery.celery_tasks.bg_send_mail",
    MagicMock(delay=MagicMock()),
)
_mail_patcher.start()

# ── 4. Import app AFTER patches ───────────────────────────────────────────────
from main import app  # noqa: E402
from core.db.main import get_session  # noqa: E402
from core.db.models import (  # noqa: E402
    User, Student, Professor, SystemAdmin,
    Department, Section, Course,
    Enrollment, CourseProfessor,
)
from core.auth.schema import UserRole  # noqa: E402
from core.security import generate_hashed_password, create_jwt_token  # noqa: E402

# ── 5. Test engine ────────────────────────────────────────────────────────────
_test_engine = create_async_engine(_TEST_DB_URL, echo=False, future=True)
_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ─────────────────────────────────────────────────────────────────────────────
# pytest-asyncio mode
# ─────────────────────────────────────────────────────────────────────────────
pytest_plugins = ("anyio",)


# ─────────────────────────────────────────────────────────────────────────────
# Session-scoped: create tables once, drop after entire suite
# ─────────────────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def setup_database():
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await _test_engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Function-scoped: isolated transactional session per test
# ─────────────────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Each test runs inside a SAVEPOINT that is rolled back afterward.
    The app's get_session dependency is overridden to use this session.
    """
    _redis_store.clear()

    async with _test_engine.connect() as conn:
        await conn.begin()
        # Nested savepoint for per-test isolation
        await conn.begin_nested()

        session = AsyncSession(bind=conn, expire_on_commit=False)

        async def _override():
            yield session

        app.dependency_overrides[get_session] = _override
        yield session

        await session.close()
        await conn.rollback()

    app.dependency_overrides.pop(get_session, None)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP client
# ─────────────────────────────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# Token helpers
# ─────────────────────────────────────────────────────────────────────────────
def make_access_token(user: User) -> str:
    payload = {"email": user.email, "id": str(user.id), "role": str(user.role)}
    return create_jwt_token(user_data=payload, expire=timedelta(minutes=30), refresh=False)


def make_refresh_token(user: User) -> str:
    payload = {"email": user.email, "id": str(user.id), "role": str(user.role)}
    return create_jwt_token(user_data=payload, expire=timedelta(days=7), refresh=True)


def make_admin_access_token(admin: SystemAdmin) -> str:
    payload = {"email": admin.email, "id": str(admin.id), "role": "admin"}
    return create_jwt_token(user_data=payload, expire=timedelta(minutes=30), refresh=False)


def make_admin_refresh_token(admin: SystemAdmin) -> str:
    payload = {"email": admin.email, "id": str(admin.id), "role": "admin"}
    return create_jwt_token(user_data=payload, expire=timedelta(days=7), refresh=True)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Low-level DB factory helpers  (called directly inside fixtures & tests)
# ─────────────────────────────────────────────────────────────────────────────
async def db_create_user(
    session: AsyncSession,
    *,
    university_id: str,
    id_card: str,
    full_name: str,
    email: str,
    role: UserRole,
    password: str = "TestPass@123",
    is_active: bool = True,
    year: int = 1,
    section_id=None,
    department_id=None,
) -> User:
    user = User(
        university_id=university_id,
        id_card=id_card,
        full_name=full_name,
        email=email.lower(),
        hashed_password=generate_hashed_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()

    if role == UserRole.student:
        session.add(
            Student(
                id=user.id,
                year=year,
                section_id=section_id,
                department_id=department_id,
            )
        )
    elif role == UserRole.professor:
        session.add(Professor(id=user.id))

    await session.commit()
    await session.refresh(user)
    return user


async def db_create_department(session: AsyncSession, name: str) -> Department:
    dept = Department(name=name)
    session.add(dept)
    await session.commit()
    await session.refresh(dept)
    return dept


async def db_create_section(session: AsyncSession, name: str) -> Section:
    sec = Section(name=name)
    session.add(sec)
    await session.commit()
    await session.refresh(sec)
    return sec


async def db_create_course(
    session: AsyncSession,
    name: str,
    year: int = 1,
    department_id=None,
    professor_id=None,
) -> Course:
    from sqlmodel import select

    if year in (1, 2) and department_id is None:
        result = await session.execute(
            select(Department).where(Department.name == "General")
        )
        dept = result.scalar_one_or_none()
        if not dept:
            dept = Department(name="General")
            session.add(dept)
            await session.flush()
        department_id = dept.id

    course = Course(name=name, year=year, department_id=department_id)
    session.add(course)
    await session.flush()

    if professor_id:
        session.add(CourseProfessor(course_id=course.id, professor_id=professor_id))

    await session.commit()
    await session.refresh(course)
    return course


async def db_enroll(session: AsyncSession, student_id, course_id) -> Enrollment:
    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    session.add(enrollment)
    await session.commit()
    return enrollment


async def db_create_admin(
    session: AsyncSession,
    email: str = "admin@uni.edu",
    password: str = "AdminPass@123",
) -> SystemAdmin:
    admin = SystemAdmin(
        email=email,
        full_name="System Admin",
        hashed_password=generate_hashed_password(password),
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


# ─────────────────────────────────────────────────────────────────────────────
# Reusable fixtures
# ─────────────────────────────────────────────────────────────────────────────
def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest_asyncio.fixture()
async def active_student(db_session: AsyncSession) -> User:
    uid = _uid()
    return await db_create_user(
        db_session,
        university_id=f"STU{uid}",
        id_card=f"CARD_STU_{uid}",
        full_name="Alice Student",
        email=f"alice_{uid}@uni.edu",
        role=UserRole.student,
        is_active=True,
    )


@pytest_asyncio.fixture()
async def inactive_student(db_session: AsyncSession) -> User:
    uid = _uid()
    return await db_create_user(
        db_session,
        university_id=f"ISTU{uid}",
        id_card=f"CARD_ISTU_{uid}",
        full_name="Inactive Student",
        email=f"inactive_{uid}@uni.edu",
        role=UserRole.student,
        is_active=False,
    )


@pytest_asyncio.fixture()
async def active_professor(db_session: AsyncSession) -> User:
    uid = _uid()
    return await db_create_user(
        db_session,
        university_id=f"PROF{uid}",
        id_card=f"CARD_PROF_{uid}",
        full_name="Dr. Bob Professor",
        email=f"bob_{uid}@uni.edu",
        role=UserRole.professor,
        is_active=True,
    )


@pytest_asyncio.fixture()
async def second_professor(db_session: AsyncSession) -> User:
    uid = _uid()
    return await db_create_user(
        db_session,
        university_id=f"PROF2_{uid}",
        id_card=f"CARD_PROF2_{uid}",
        full_name="Dr. Eve Professor",
        email=f"eve_{uid}@uni.edu",
        role=UserRole.professor,
        is_active=True,
    )


@pytest_asyncio.fixture()
async def system_admin(db_session: AsyncSession) -> SystemAdmin:
    uid = _uid()
    return await db_create_admin(db_session, email=f"admin_{uid}@uni.edu")


# ── Header fixtures ───────────────────────────────────────────────────────────
@pytest.fixture()
def student_headers(active_student: User) -> dict:
    return bearer(make_access_token(active_student))


@pytest.fixture()
def professor_headers(active_professor: User) -> dict:
    return bearer(make_access_token(active_professor))


@pytest.fixture()
def admin_headers(system_admin: SystemAdmin) -> dict:
    return bearer(make_admin_access_token(system_admin))


# ── Composite fixtures ────────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def course_with_professor(
    db_session: AsyncSession, active_professor: User
) -> Course:
    """A course owned by active_professor."""
    return await db_create_course(
        db_session, "Default Course", year=1, professor_id=active_professor.id
    )


@pytest_asyncio.fixture()
async def enrolled_setup(
    db_session: AsyncSession,
    active_student: User,
    active_professor: User,
    course_with_professor: Course,
):
    """Student enrolled in course_with_professor."""
    await db_enroll(db_session, active_student.id, course_with_professor.id)
    return active_student, active_professor, course_with_professor
