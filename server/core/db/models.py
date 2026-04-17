from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import func, UniqueConstraint, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TIMESTAMP
import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum
from core.auth.schema import UserRole


# ──────────────────────────────────────────────
# 1. Core Structure & Sections
# ──────────────────────────────────────────────

class Department(SQLModel, table=True):
    __tablename__ = "departments"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    name: str = Field(unique=True, nullable=False)

    students: List["Student"] = Relationship(back_populates="department")
    courses: List["Course"] = Relationship(back_populates="department")


class Section(SQLModel, table=True):
    __tablename__ = "sections"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    name: str = Field(unique=True, nullable=False)

    students: List["Student"] = Relationship(back_populates="section")
    qr_codes: List["QRCode"] = Relationship(back_populates="section")
    quizzes: List["Quiz"] = Relationship(back_populates="target_section")


# ──────────────────────────────────────────────
# 2. User & Role Management
# ──────────────────────────────────────────────

class SystemAdmin(SQLModel, table=True):
    __tablename__ = "system_admins"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    email: str = Field(unique=True, index=True, nullable=False)
    full_name: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    university_id: str = Field(index=True, unique=True, nullable=False)
    id_card: str = Field(index=True, unique=True, nullable=False)
    full_name: str = Field(nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.student, nullable=False)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    )

    professor: Optional["Professor"] = Relationship(back_populates="user")
    student: Optional["Student"] = Relationship(back_populates="user")
    qr_codes_generated: List["QRCode"] = Relationship(back_populates="generator")
    quizzes_created: List["Quiz"] = Relationship(back_populates="creator")


class CourseProfessor(SQLModel, table=True):
    __tablename__ = "course_professors"
    __table_args__ = (
        UniqueConstraint("course_id", "professor_id", name="uq_course_professor"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    course_id: uuid.UUID = Field(foreign_key="courses.id", nullable=False)
    professor_id: uuid.UUID = Field(foreign_key="professors.id", nullable=False)
    assigned_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )


class Professor(SQLModel, table=True):
    __tablename__ = "professors"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False
        )
    )

    user: Optional[User] = Relationship(back_populates="professor")
    courses: List["Course"] = Relationship(back_populates="professors", link_model=CourseProfessor)





class Student(SQLModel, table=True):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1 AND 4", name="ck_students_year"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False
        )
    )
    year: int = Field(nullable=False)
    section_id: Optional[uuid.UUID] = Field(default=None, foreign_key="sections.id")
    department_id: Optional[uuid.UUID] = Field(default=None, foreign_key="departments.id")

    user: Optional[User] = Relationship(back_populates="student")
    section: Optional[Section] = Relationship(back_populates="students")
    department: Optional[Department] = Relationship(back_populates="students")
    enrollments: List["Enrollment"] = Relationship(back_populates="student")
    attendances: List["Attendance"] = Relationship(back_populates="student")
    quiz_submissions: List["QuizSubmission"] = Relationship(back_populates="student")


# ──────────────────────────────────────────────
# 3. Courses & Assignments
# ──────────────────────────────────────────────

class Course(SQLModel, table=True):
    __tablename__ = "courses"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    name: str = Field(nullable=False)
    year: int = Field(nullable=False)
    department_id: Optional[uuid.UUID] = Field(default=None, foreign_key="departments.id")

    department: Optional[Department] = Relationship(back_populates="courses")
    professors: List[Professor] = Relationship(back_populates="courses", link_model=CourseProfessor)


    enrollments: List["Enrollment"] = Relationship(back_populates="course")
    qr_codes: List["QRCode"] = Relationship(back_populates="course")
    quizzes: List["Quiz"] = Relationship(back_populates="course")




class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    course_id: uuid.UUID = Field(foreign_key="courses.id", nullable=False)
    enrolled_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )

    student: Optional[Student] = Relationship(back_populates="enrollments")
    course: Optional[Course] = Relationship(back_populates="enrollments")


# ──────────────────────────────────────────────
# 4. Attendance (Normalized)
# ──────────────────────────────────────────────

class QRCode(SQLModel, table=True):
    __tablename__ = "qr_codes"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    course_id: uuid.UUID = Field(foreign_key="courses.id", nullable=False)
    generated_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    week_number: int = Field(nullable=False)
    section_id: Optional[uuid.UUID] = Field(default=None, foreign_key="sections.id")
    token: str = Field(unique=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )

    course: Optional[Course] = Relationship(back_populates="qr_codes")
    generator: Optional[User] = Relationship(back_populates="qr_codes_generated")
    section: Optional[Section] = Relationship(back_populates="qr_codes")
    attendances: List["Attendance"] = Relationship(back_populates="qr_code")


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "qr_code_id", name="uq_attendance_student_qr"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    qr_code_id: uuid.UUID = Field(foreign_key="qr_codes.id", nullable=False)
    scanned_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )

    student: Optional[Student] = Relationship(back_populates="attendances")
    qr_code: Optional[QRCode] = Relationship(back_populates="attendances")


# ──────────────────────────────────────────────
# 5. Quizzes
# ──────────────────────────────────────────────

class CreatorRole(str, Enum):
    professor = "professor"


class Quiz(SQLModel, table=True):
    __tablename__ = "quizzes"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    title: str = Field(nullable=False)
    course_id: uuid.UUID = Field(foreign_key="courses.id", nullable=False)
    created_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    creator_role: CreatorRole = Field(nullable=False)
    target_section_id: Optional[uuid.UUID] = Field(default=None, foreign_key="sections.id")
    due_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )

    course: Optional[Course] = Relationship(back_populates="quizzes")
    creator: Optional[User] = Relationship(back_populates="quizzes_created")
    target_section: Optional[Section] = Relationship(back_populates="quizzes")
    questions: List["Question"] = Relationship(back_populates="quiz")
    submissions: List["QuizSubmission"] = Relationship(back_populates="quiz")


class Question(SQLModel, table=True):
    __tablename__ = "questions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    quiz_id: uuid.UUID = Field(foreign_key="quizzes.id", nullable=False)
    text: str = Field(nullable=False)
    order_index: int = Field(nullable=False)

    quiz: Optional[Quiz] = Relationship(back_populates="questions")
    choices: List["Choice"] = Relationship(back_populates="question")
    submission_answers: List["SubmissionAnswer"] = Relationship(back_populates="question")


class Choice(SQLModel, table=True):
    __tablename__ = "choices"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    question_id: uuid.UUID = Field(foreign_key="questions.id", nullable=False)
    text: str = Field(nullable=False)
    is_correct: bool = Field(default=False)

    question: Optional[Question] = Relationship(back_populates="choices")
    submission_answers: List["SubmissionAnswer"] = Relationship(back_populates="chosen_choice")


class QuizSubmission(SQLModel, table=True):
    __tablename__ = "quiz_submissions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    quiz_id: uuid.UUID = Field(foreign_key="quizzes.id", nullable=False)
    student_id: uuid.UUID = Field(foreign_key="students.id", nullable=False)
    submitted_at: datetime = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), nullable=False)
    )
    score: Optional[float] = Field(default=None)

    quiz: Optional[Quiz] = Relationship(back_populates="submissions")
    student: Optional[Student] = Relationship(back_populates="quiz_submissions")
    answers: List["SubmissionAnswer"] = Relationship(back_populates="submission")


class SubmissionAnswer(SQLModel, table=True):
    __tablename__ = "submission_answers"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), nullable=False)
    )
    submission_id: uuid.UUID = Field(foreign_key="quiz_submissions.id", nullable=False)
    question_id: uuid.UUID = Field(foreign_key="questions.id", nullable=False)
    chosen_choice_id: Optional[uuid.UUID] = Field(default=None, foreign_key="choices.id")

    submission: Optional[QuizSubmission] = Relationship(back_populates="answers")
    question: Optional[Question] = Relationship(back_populates="submission_answers")
    chosen_choice: Optional[Choice] = Relationship(back_populates="submission_answers")