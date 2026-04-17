"""
Redis client for token blacklisting and QR code token storage.
"""
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from .config import config

# Create Redis client
token_blacklist = Redis.from_url(config.Redis_Url, decode_responses=True)


# ──────────────────────────────────────────────
# Connection Check
# ──────────────────────────────────────────────

async def check_redis_connection() -> bool:
    try:
        await token_blacklist.ping()
        print("✓ Redis is working")
        return True
    except ConnectionError as e:
        print(f"✗ Redis is not working: {e}")
        return False


# ──────────────────────────────────────────────
# Token Blacklist (JWT refresh tokens)
# ──────────────────────────────────────────────

async def add_to_blacklist(jti: str, exp: int = 1800) -> bool:
    """Add a JWT token ID to the blacklist with a TTL."""
    try:
        result = await token_blacklist.set(name=jti, value="", ex=exp)
        return bool(result)
    except ConnectionError as e:
        print(f"✗ Redis error in add_to_blacklist: {e}")
        return False


async def check_blacklist(jti: str) -> bool:
    """Check if a JWT token ID is blacklisted."""
    try:
        result = await token_blacklist.get(name=jti)
        return result is not None
    except ConnectionError as e:
        print(f"✗ Redis error in check_blacklist: {e}")
        return False


# ──────────────────────────────────────────────
# QR Code Token Store (with TTL-based expiry)
# ──────────────────────────────────────────────

QR_PREFIX = "qr_token:"


async def store_qr_token(token: str, qr_code_id: str, ttl_seconds: int) -> bool:
    """Store a QR token in Redis with a TTL. The key maps to the qr_code_id."""
    try:
        result = await token_blacklist.set(
            name=f"{QR_PREFIX}{token}",
            value=qr_code_id,
            ex=ttl_seconds,
        )
        return bool(result)
    except ConnectionError as e:
        print(f"✗ Redis error storing QR token: {e}")
        return False


async def check_qr_token(token: str) -> str | None:
    """
    Check if a QR token exists in Redis (i.e., not expired).
    Returns the qr_code_id if found, None otherwise.
    """
    try:
        result = await token_blacklist.get(name=f"{QR_PREFIX}{token}")
        return result
    except ConnectionError as e:
        print(f"✗ Redis error checking QR token: {e}")
        return None


async def delete_qr_token(token: str) -> bool:
    """Manually invalidate a QR token."""
    try:
        result = await token_blacklist.delete(f"{QR_PREFIX}{token}")
        return bool(result)
    except ConnectionError as e:
        print(f"✗ Redis error deleting QR token: {e}")
        return False