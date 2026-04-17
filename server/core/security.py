import bcrypt
import jwt
import uuid
import logging
from datetime import timedelta, datetime, timezone
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from core.db.config import config
from core.errors import InvalidToken, TokenExpired, QRCodeExpired


# ── PASSWORD HASHING ───────────────────────────

def generate_hashed_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd, bcrypt.gensalt(config.BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


# ── JWT TOKENS ─────────────────────────────────

def create_jwt_token(user_data: dict, expire: timedelta = None, refresh: bool = False) -> str:
    """Create a JWT access or refresh token."""
    payload = {
        "user": user_data,
        "exp": datetime.now(timezone.utc) + (expire or timedelta(minutes=30)),
        "jti": str(uuid.uuid4()),
        "refresh_token": refresh,
    }
    return jwt.encode(payload=payload, key=config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_token(token_data: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(jwt=token_data, key=config.jwt_secret, algorithms=[config.jwt_algorithm])
    except jwt.exceptions.ExpiredSignatureError:
        raise TokenExpired()
    except jwt.InvalidTokenError:
        raise InvalidToken()
    except Exception as e:
        logging.exception(f"Token decode error: {e}")
        raise InvalidToken()


# ── QR CODE TOKENS ─────────────────────────────

def generate_qr_token(course_id: str, week_number: int, expires_at: str, section_id: str = None) -> str:
    """Generate a JWT signed token for QR code attendance."""
    expires_at_dt = datetime.fromisoformat(expires_at)

    payload = {
        "course_id": course_id,
        "week_number": week_number,
        "section_id": section_id,
        "expires_at": expires_at,
        "exp": expires_at_dt,
    }

    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def verify_qr_token(token: str) -> dict:
    """Verify a JWT signed QR token. Returns decoded payload."""
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm],
            options={"verify_exp": True},
        )

        expires_at = datetime.fromisoformat(payload["expires_at"])
        if datetime.now(timezone.utc).replace(tzinfo=None) > expires_at:
            raise QRCodeExpired()

        return payload

    except jwt.ExpiredSignatureError:
        raise QRCodeExpired()
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise InvalidToken()


# ── SAFE URL LINKS (email verification, password reset) ──

class CreationSafeLink(URLSafeTimedSerializer):
    def __init__(self, secret_key: str, salt: str):
        super().__init__(secret_key=secret_key, salt=salt)

    def create_url(self, data: dict = None) -> str:
        """Create a signed URL token with a unique ID."""
        data = data or {}
        data["token_id"] = str(uuid.uuid4())
        return self.dumps(data)

    def decode(self, token: str, max_age: int = 1800) -> dict:
        """Decode and verify a signed URL token."""
        try:
            return self.loads(token, max_age=max_age)
        except SignatureExpired:
            raise TokenExpired()
        except BadSignature:
            raise InvalidToken()
        except Exception as e:
            logging.exception(f"Token decode error: {e}")
            raise InvalidToken()