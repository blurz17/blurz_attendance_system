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
        
        # 1. Create 10 System Admins (for Admin Panel)
        for i in range(1, 11):
            admin_email = f"admin{i}@blurz.com" if i > 1 else "admin@blurz.com"
            result = await session.exec(select(SystemAdmin).where(SystemAdmin.email == admin_email))
            admin = result.one_or_none()
            if not admin:
                admin = SystemAdmin(
                    email=admin_email,
                    full_name=f"System Administrator {i}",
                    hashed_password=generate_hashed_password("Admin123!")
                )
                session.add(admin)
                print(f"✅ Created System Admin: {admin_email} / Admin123!")
            else:
                admin.hashed_password = generate_hashed_password("Admin123!")
                session.add(admin)
                print(f"🔄 Reset System Admin: {admin_email} / Admin123!")

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

        # 3. Create 10 Professors (for Instructor Panel)
        for i in range(1, 11):
            prof_email = f"prof{i}@blurz.com" if i > 1 else "prof@blurz.com"
            result = await session.exec(select(User).where(User.email == prof_email))
            prof_user = result.one_or_none()
            if not prof_user:
                prof_user = User(
                    university_id=f"P12345{i}",
                    id_card=f"CARD_P12345{i}",
                    full_name=f"Dr. Professor {i}",
                    email=prof_email,
                    hashed_password=generate_hashed_password("Prof123!"),
                    role=UserRole.professor,
                    is_active=True
                )
                session.add(prof_user)
                await session.flush()
                
                prof = Professor(id=prof_user.id)
                session.add(prof)
                print(f"✅ Created Professor: {prof_email} / Prof123!")
                
                # Create a course for the professor
                course = Course(
                    name=f"Intro to Programming {i}",
                    year=1,
                    department_id=dept.id
                )
                session.add(course)
                await session.flush()
                
                # Link course to professor
                session.add(CourseProfessor(course_id=course.id, professor_id=prof.id))
                print(f"✅ Created Course: {course.name}")
            else:
                prof_user.hashed_password = generate_hashed_password("Prof123!")
                prof_user.is_active = True
                session.add(prof_user)
                print(f"🔄 Reset Professor: {prof_email} / Prof123!")

        # 4. Create 10 Students (for Student Panel)
        for i in range(1, 11):
            student_email = f"student{i}@blurz.com" if i > 1 else "student@blurz.com"
            result = await session.exec(select(User).where(User.email == student_email))
            student_user = result.one_or_none()
            if not student_user:
                student_user = User(
                    university_id=f"S12345{i}",
                    id_card=f"CARD_S12345{i}",
                    full_name=f"Student Name {i}",
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
                print(f"✅ Created Student: {student_email} / Student123!")
            else:
                student_user.hashed_password = generate_hashed_password("Student123!")
                student_user.is_active = True
                session.add(student_user)
                print(f"🔄 Reset Student: {student_email} / Student123!")

        await session.commit()
        print("🎉 Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_database())
