from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.services.auth import hash_password, verify_password, create_access_token
import uuid

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, email=user.email)


@router.get("/me")
async def me(user: User = Depends(__import__("app.services.auth", fromlist=["get_current_user"]).get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}
