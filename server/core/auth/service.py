"""
Auth service — user lookup, activation, password management.
User creation is handled by the admin service.
"""
import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from core.db.models import User
from core.security import generate_hashed_password
from core.errors import UserNotFound, UserAlreadyActive


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    """Find a user by their email address."""
    result = await session.execute(
        select(User).where(User.email == email.strip().lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(user_id, session: AsyncSession) -> User | None:
    """Find a user by their UUID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def activate_user(email: str, password: str, session: AsyncSession) -> User:
    """Activate a user account — sets password and marks is_active = True."""
    user = await get_user_by_email(email, session)
    if not user:
        raise UserNotFound()
    if user.is_active:
        raise UserAlreadyActive()

    user.hashed_password = generate_hashed_password(password)
    user.is_active = True
    await session.commit()
    await session.refresh(user)
    logging.info(f"User activated: {email}")
    return user


async def change_password(user: User, new_password: str, session: AsyncSession) -> None:
    """Change a user's password (must already be authenticated)."""
    user.hashed_password = generate_hashed_password(new_password)
    await session.commit()


async def reset_password(email: str, new_password: str, session: AsyncSession) -> User:
    """Reset a user's password via the forgot-password flow."""
    user = await get_user_by_email(email, session)
    if not user:
        raise UserNotFound()

    user.hashed_password = generate_hashed_password(new_password)
    await session.commit()
    return user