"""
Admin Auth service — system administrator lookup and creation.
"""
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from core.db.models import SystemAdmin
from core.security import generate_hashed_password


async def get_admin_by_email(email: str, session: AsyncSession) -> SystemAdmin | None:
    """Fetch a system admin by email."""
    result = await session.execute(
        select(SystemAdmin).where(SystemAdmin.email == email)
    )
    return result.scalar_one_or_none()


async def create_initial_admin(
    email: str, full_name: str, password: str, session: AsyncSession
) -> SystemAdmin:
    """Create an initial admin (for setup/dev)."""
    admin = SystemAdmin(
        email=email,
        full_name=full_name,
        hashed_password=generate_hashed_password(password),
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin
