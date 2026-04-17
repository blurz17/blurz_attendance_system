"""
Admin schemas — Pydantic models for admin user/course/department management.
"""
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional, List
from core.auth.schema import UserRole


# ──────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    university_id: str
    id_card: str
    full_name: str
    email: str = Field(max_length=100)
    role: UserRole
    year: Optional[int] = Field(default=None, ge=1, le=4)
    section_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    course_ids: Optional[List[uuid.UUID]] = None  # For professors (assign to courses)


class UpdateUserRequest(BaseModel):
    university_id: Optional[str] = None
    id_card: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    year: Optional[int] = Field(default=None, ge=1, le=4)
    section_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    university_id: str
    id_card: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    year: Optional[int] = None
    section_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


# ──────────────────────────────────────────────
# Bulk Upload
# ──────────────────────────────────────────────

class BulkUploadRowResult(BaseModel):
    row_number: int
    university_id: Optional[str] = None
    success: bool
    error: Optional[str] = None


class BulkUploadResponse(BaseModel):
    total_rows: int
    succeeded: int
    failed: int
    results: List[BulkUploadRowResult]


# ──────────────────────────────────────────────
# Department Management
# ──────────────────────────────────────────────

class CreateDepartmentRequest(BaseModel):
    name: str


class UpdateDepartmentRequest(BaseModel):
    name: str


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Section Management
# ──────────────────────────────────────────────

class CreateSectionRequest(BaseModel):
    name: str


class UpdateSectionRequest(BaseModel):
    name: str


class SectionResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Course Management
# ──────────────────────────────────────────────

class CreateCourseRequest(BaseModel):
    name: str
    year: int = Field(ge=1, le=4)
    department_id: Optional[uuid.UUID] = None  # Auto-set to General for year 1&2
    professor_ids: Optional[List[uuid.UUID]] = Field(default_factory=list)


class UpdateCourseRequest(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1, le=4)
    department_id: Optional[uuid.UUID] = None
    professor_ids: Optional[List[uuid.UUID]] = None


class CourseResponse(BaseModel):
    id: uuid.UUID
    name: str
    year: int
    department_id: Optional[uuid.UUID] = None
    professor_ids: List[uuid.UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Enrollment & Course Assignment
# ──────────────────────────────────────────────

class EnrollStudentRequest(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID


