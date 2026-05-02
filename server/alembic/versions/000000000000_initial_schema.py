"""initial_schema

Revision ID: 000000000000
Revises:
Create Date: 2026-02-25 12:00:00.000000

This is the true initial migration for fresh deployments.
It creates all base tables that the subsequent migrations expect to exist.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000000000000'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all base tables."""

    # Enable pgcrypto for gen_random_uuid()
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    # departments
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False, unique=True),
    )

    # sections
    op.create_table(
        'sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False, unique=True),
    )

    # system_admins
    op.create_table(
        'system_admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_system_admins_email', 'system_admins', ['email'])

    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('university_id', sa.String(), nullable=False, unique=True),
        sa.Column('id_card', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_university_id', 'users', ['university_id'])
    op.create_index('ix_users_id_card', 'users', ['id_card'])
    op.create_index('ix_users_email', 'users', ['email'])

    # professors
    op.create_table(
        'professors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ondelete='CASCADE'),
    )

    # students
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.CheckConstraint('year BETWEEN 1 AND 4', name='ck_students_year'),
    )

    # courses
    op.create_table(
        'courses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
    )

    # course_professors
    op.create_table(
        'course_professors',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('professor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['professor_id'], ['professors.id']),
        sa.UniqueConstraint('course_id', 'professor_id', name='uq_course_professor'),
    )

    # enrollments
    op.create_table(
        'enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enrolled_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.UniqueConstraint('student_id', 'course_id', name='uq_enrollment_student_course'),
    )

    # qr_codes
    op.create_table(
        'qr_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('token', sa.String(), nullable=False, unique=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id']),
    )

    # attendance
    op.create_table(
        'attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('qr_code_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scanned_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['qr_code_id'], ['qr_codes.id']),
        sa.UniqueConstraint('student_id', 'qr_code_id', name='uq_attendance_student_qr'),
    )

    # quizzes
    op.create_table(
        'quizzes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('creator_role', sa.String(), nullable=False),
        sa.Column('target_section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('due_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['target_section_id'], ['sections.id']),
    )

    # questions
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id']),
    )

    # choices
    op.create_table(
        'choices',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
    )

    # quiz_submissions
    op.create_table(
        'quiz_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submitted_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
    )

    # submission_answers
    op.create_table(
        'submission_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chosen_choice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['quiz_submissions.id']),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['chosen_choice_id'], ['choices.id']),
    )

    # Legacy tables (dropped by migration 00fa352db6f0, kept here for history)
    op.create_table(
        'assistants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_table(
        'course_assistants',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True, nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assistant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistants.id']),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id']),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('submission_answers')
    op.drop_table('quiz_submissions')
    op.drop_table('choices')
    op.drop_table('questions')
    op.drop_table('quizzes')
    op.drop_table('attendance')
    op.drop_table('qr_codes')
    op.drop_table('enrollments')
    op.drop_table('course_professors')
    op.drop_table('courses')
    op.drop_table('students')
    op.drop_table('professors')
    op.drop_table('users')
    op.drop_table('system_admins')
    op.drop_table('sections')
    op.drop_table('departments')
    op.drop_table('course_assistants')
    op.drop_table('assistants')
