"""
Admin router — user, department, section, course, and enrollment management.
"""
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db.main import get_session
from core.admin import service as admin_svc
from core.admin.schema import (
    CreateUserRequest, UpdateUserRequest, UserResponse, UserListResponse,
    BulkUploadResponse, CreateDepartmentRequest, UpdateDepartmentRequest,
    DepartmentResponse, CreateSectionRequest, UpdateSectionRequest,
    SectionResponse, CreateCourseRequest, UpdateCourseRequest,
    CourseResponse, EnrollStudentRequest,
)

admin_router = APIRouter()


# ── USER MANAGEMENT ────────────────────────────

@admin_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: CreateUserRequest, session: AsyncSession = Depends(get_session)):
    """Create a single user with role-specific record and send activation email."""
    return await admin_svc.create_single_user(data, session)


@admin_router.post("/users/bulk", response_model=BulkUploadResponse)
async def bulk_upload_users(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    """Bulk upload users from a CSV file."""
    csv_text = (await file.read()).decode("utf-8")
    results = await admin_svc.bulk_upload_users(csv_text, session)
    succeeded = sum(1 for r in results if r.success)
    return BulkUploadResponse(
        total_rows=len(results), succeeded=succeeded,
        failed=len(results) - succeeded, results=results,
    )


@admin_router.get("/users", response_model=UserListResponse)
async def list_users(
    role: str = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """List all users with optional role filter and pagination."""
    users, total = await admin_svc.list_users(session, role=role, skip=skip, limit=limit)
    return UserListResponse(users=[UserResponse.model_validate(u) for u in users], total=total)


@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await admin_svc.get_user(user_id, session)


@admin_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: uuid.UUID, data: UpdateUserRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.update_user(user_id, data.model_dump(exclude_unset=True), session)


@admin_router.delete("/users/{user_id}")
async def deactivate_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Deactivate a user account (soft delete)."""
    await admin_svc.deactivate_user(user_id, session)
    return JSONResponse(content={"message": "User deactivated"})


# ── DEPARTMENT MANAGEMENT ──────────────────────

@admin_router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(data: CreateDepartmentRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.create_department(data.name, session)


@admin_router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(session: AsyncSession = Depends(get_session)):
    return await admin_svc.list_departments(session)


@admin_router.get("/departments/{dept_id}", response_model=DepartmentResponse)
async def get_department(dept_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await admin_svc.get_department(dept_id, session)


@admin_router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(dept_id: uuid.UUID, data: UpdateDepartmentRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.update_department(dept_id, data.name, session)


@admin_router.delete("/departments/{dept_id}")
async def delete_department(dept_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await admin_svc.delete_department(dept_id, session)
    return JSONResponse(content={"message": "Department deleted"})


# ── SECTION MANAGEMENT ─────────────────────────

@admin_router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(data: CreateSectionRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.create_section(data.name, session)


@admin_router.get("/sections", response_model=list[SectionResponse])
async def list_sections(session: AsyncSession = Depends(get_session)):
    return await admin_svc.list_sections(session)


@admin_router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(section_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await admin_svc.get_section(section_id, session)


@admin_router.put("/sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: uuid.UUID, data: UpdateSectionRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.update_section(section_id, data.name, session)


@admin_router.delete("/sections/{section_id}")
async def delete_section(section_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await admin_svc.delete_section(section_id, session)
    return JSONResponse(content={"message": "Section deleted"})


# ── COURSE MANAGEMENT ──────────────────────────

@admin_router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(data: CreateCourseRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.create_course(
        name=data.name, year=data.year, department_id=data.department_id,
        professor_ids=data.professor_ids, session=session,
    )


@admin_router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    year: int = Query(default=None),
    department_id: uuid.UUID = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    return await admin_svc.list_courses(session, year=year, department_id=department_id)


@admin_router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return await admin_svc.get_course(course_id, session)


@admin_router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(course_id: uuid.UUID, data: UpdateCourseRequest, session: AsyncSession = Depends(get_session)):
    return await admin_svc.update_course(course_id, data.model_dump(exclude_unset=True), session)


@admin_router.delete("/courses/{course_id}")
async def delete_course(course_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await admin_svc.delete_course(course_id, session)
    return JSONResponse(content={"message": "Course deleted"})


# ── ENROLLMENT ─────────────────────────────────

@admin_router.post("/enrollments", status_code=status.HTTP_201_CREATED)
async def enroll_student(data: EnrollStudentRequest, session: AsyncSession = Depends(get_session)):
    enrollment = await admin_svc.enroll_student(data.student_id, data.course_id, session)
    return JSONResponse(content={"message": "Student enrolled successfully", "id": str(enrollment.id)}, status_code=201)
