import logging
import asyncio
from sqlmodel import select
from core.db.main import async_session, init_db
from core.db.models import SystemAdmin
from core.security import generate_hashed_password

# Disable SQL logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

async def add_or_update_admin(email: str, full_name: str, password: str):
    log_file = "add_admin_result.log"
    try:
        async with async_session() as session:
            # Check if admin already exists
            statement = select(SystemAdmin).where(SystemAdmin.email == email)
            result = await session.execute(statement)
            admin = result.scalar_one_or_none()

            hashed_password = generate_hashed_password(password)
            
            if admin:
                # Update existing admin
                admin.full_name = full_name
                admin.hashed_password = hashed_password
                message = f"Admin {email} already exists. Updated details (full_name: {full_name}, password: [UPDATED])."
                session.add(admin)
            else:
                # Create new admin
                admin = SystemAdmin(
                    email=email,
                    full_name=full_name,
                    hashed_password=hashed_password
                )
                session.add(admin)
                message = f"Admin {full_name} ({email}) created successfully."
            
            await session.commit()
            print(message)
            with open(log_file, "a") as f: f.write(message + "\n")
    except Exception as e:
        import traceback
        error_msg = f"Error adding/updating admin: {e}\n{traceback.format_exc()}"
        print(error_msg)
        with open(log_file, "a") as f: f.write(error_msg + "\n")

if __name__ == "__main__":
    EMAIL = "blurz@gmail.com"
    FULL_NAME = "blurz_admin"
    PASSWORD = "blurzblurz"
    
    async def main():
        await init_db()
        await add_or_update_admin(EMAIL, FULL_NAME, PASSWORD)
        
    asyncio.run(main())
