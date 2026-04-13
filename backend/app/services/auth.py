import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.api_key import ApiKey

settings = get_settings()

# auto_error=False so we can fall through to API key auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, key_hash, key_prefix)."""
    raw = secrets.token_hex(32)
    full_key = f"gr_live_{raw}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:20]  # e.g. "gr_live_a1b2c3d4e5f6"
    return full_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def _get_user_from_token(token: str, db: AsyncSession) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def _get_user_from_api_key(key: str, db: AsyncSession) -> Optional[User]:
    key_hash = hash_api_key(key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None

    # Update last_used_at asynchronously (best-effort)
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(last_used_at=datetime.now(timezone.utc))
    )
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == api_key.user_id))
    return user_result.scalar_one_or_none()


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    # API key takes priority (for CI/programmatic use)
    if x_api_key:
        user = await _get_user_from_api_key(x_api_key, db)
        if user:
            return user
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    if token:
        return await _get_user_from_token(token, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
