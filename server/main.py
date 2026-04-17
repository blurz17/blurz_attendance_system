"""
Smart Attendance & Quiz Management System — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.db.main import init_db
from core.db.redis import check_redis_connection
from api.c_router import api_router
from api.middleware.auth import AuthMiddleware
from api.middleware.logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 Starting Smart Attendance System...")
    await init_db()
    await check_redis_connection()
    print("✅ Server is ready")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Smart Attendance & Quiz Management System",
    description="University platform for QR-based attendance and quiz management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Routes
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "smart-attendance"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)