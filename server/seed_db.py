import asyncio
from sqlmodel import select
from core.db.main import async_session
from core.db.models import (
    SystemAdmin, User, Professor, Student, 
    Department, Section, Course, CourseProfessor
)
from core.auth.schema import UserRole
from core.security import generate_hashed_password

async def seed_database():
    async with async_session() as session:
        print("🌱 Seeding database...")
        
        # 1. Create a System Admin (for Admin Panel)
        admin_email = "admin@blurz.com"
        result = await session.exec(select(SystemAdmin).where(SystemAdmin.email == admin_email))
        if not result.one_or_none():
            admin = SystemAdmin(
                email=admin_email,
                full_name="System Administrator",
                hashed_password=generate_hashed_password("Admin123!")
            )
            session.add(admin)
            print("✅ Created System Admin: admin@blurz.com / Admin123!")

        # 2. Create Department & Section
        dept_name = "Computer Science"
        result = await session.exec(select(Department).where(Department.name == dept_name))
        dept = result.one_or_none()
        if not dept:
            dept = Department(name=dept_name)
            session.add(dept)
            await session.flush()
            
        section_name = "CS-A"
        result = await session.exec(select(Section).where(Section.name == section_name))
        section = result.one_or_none()
        if not section:
            section = Section(name=section_name)
            session.add(section)
            await session.flush()

        # 3. Create a Professor (for Instructor Panel)
        prof_email = "prof@blurz.com"
        result = await session.exec(select(User).where(User.email == prof_email))
        if not result.one_or_none():
            prof_user = User(
                university_id="P12345",
                id_card="CARD_P12345",
                full_name="Dr. John Doe",
                email=prof_email,
                hashed_password=generate_hashed_password("Prof123!"),
                role=UserRole.professor,
                is_active=True
            )
            session.add(prof_user)
            await session.flush()
            
            prof = Professor(id=prof_user.id)
            session.add(prof)
            print("✅ Created Professor: prof@blurz.com / Prof123!")
            
            # Create a course for the professor
            course = Course(
                name="Intro to Programming",
                year=1,
                department_id=dept.id
            )
            session.add(course)
            await session.flush()
            
            # Link course to professor
            session.add(CourseProfessor(course_id=course.id, professor_id=prof.id))
            print("✅ Created Course: CS101 - Intro to Programming")

        # 4. Create a Student (for Student Panel)
        student_email = "student@blurz.com"
        result = await session.exec(select(User).where(User.email == student_email))
        if not result.one_or_none():
            student_user = User(
                university_id="S12345",
                id_card="CARD_S12345",
                full_name="Alice Smith",
                email=student_email,
                hashed_password=generate_hashed_password("Student123!"),
                role=UserRole.student,
                is_active=True
            )
            session.add(student_user)
            await session.flush()
            
            student = Student(
                id=student_user.id,
                year=1,
                department_id=dept.id,
                section_id=section.id
            )
            session.add(student)
            print("✅ Created Student: student@blurz.com / Student123!")

        await session.commit()
        print("🎉 Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
