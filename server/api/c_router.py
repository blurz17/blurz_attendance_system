"""
Central API router — wires all sub-routers under /api/v1.
"""
from fastapi import APIRouter

from core.auth.routes import auth_router
from core.admin.router import admin_router
from core.admin.auth.router import admin_auth_router
from core.client.router import client_router

# Central router
api_router = APIRouter(prefix="/api/v1")

# Auth endpoints: /api/v1/auth/*
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Admin Auth endpoints: /api/v1/admin/auth/*
api_router.include_router(admin_auth_router, prefix="/admin/auth", tags=["Admin Auth"])

# Admin endpoints: /api/v1/admin/*
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

# Client endpoints include attendance, quiz, student, instructor
# /api/v1/attendance/*, /api/v1/quiz/*, /api/v1/student/*, /api/v1/instructor/*
api_router.include_router(client_router, tags=["Client"])
