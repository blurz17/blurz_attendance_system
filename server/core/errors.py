"""
Custom HTTP exceptions for the Smart Attendance System.
"""
from fastapi import HTTPException, status


# ── AUTH ERRORS ─────────────────────────────────

class InvalidToken(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Invalid or malformed token")

class TokenExpired(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Token has expired")

class InvalidCredentials(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

class RefreshTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Please provide a refresh token, not an access token")

class AccessTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Please provide an access token, not a refresh token")

class InsufficientPermission(HTTPException):
    def __init__(self, detail="You do not have permission to perform this action"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)

class AccountNotActive(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Account is not activated. Check your email for the activation link.")


# ── USER ERRORS ────────────────────────────────

class UserNotFound(HTTPException):
    def __init__(self, detail="User not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)

class UserAlreadyExists(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "User with this email or university ID already exists")

class UserAlreadyActive(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "User account is already activated")

class PasswordAlreadyReset(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "This password reset link has already been used")


# ── DATA ERRORS ────────────────────────────────

class DataNotFound(HTTPException):
    def __init__(self, detail="Requested data not found"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)

class CourseNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Course not found")

class DepartmentNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Department not found")

class QuizNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Quiz not found")


# ── ATTENDANCE ERRORS ──────────────────────────

class NotEnrolled(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Student is not enrolled in this course")

class SectionMismatch(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Student's section does not match the QR code section")

class DuplicateAttendance(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "Attendance already recorded for this QR code")

class QRCodeExpired(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_410_GONE, "QR code has expired")

class QRCodeInvalid(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "QR code is invalid or has been tampered with")

class NotCourseInstructor(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "You are not an instructor for this course")


# ── QUIZ ERRORS ────────────────────────────────

class QuizAlreadySubmitted(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "You have already submitted this quiz")

class QuizExpired(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_410_GONE, "Quiz submission deadline has passed")
