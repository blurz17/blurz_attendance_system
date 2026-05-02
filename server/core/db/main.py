import re
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from .config import config

def _clean_db_url(url: str) -> str:
    """Strip ssl/sslmode params from URL — asyncpg needs them via connect_args."""
    return re.sub(r'[?&]ssl(mode)?=[^&]*', '', url).rstrip('?')

engine = create_async_engine(
    _clean_db_url(config.DB_URL),
    connect_args={"ssl": True},  # Required for Neon
    echo=False,
    future=True
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_session():
    async with async_session() as session:
        yield session