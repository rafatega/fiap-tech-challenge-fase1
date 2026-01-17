import os
import datetime
from typing import Optional, Generator

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from fastapi import APIRouter, HTTPException, Depends, Request
from passlib.context import CryptContext

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .models import LoginRequest, TokenResponse, RefreshRequest


# JWT CONFIG

JWT_SECRET = os.getenv("JWT_SECRET", "MEUSEGREDOAQUI")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = int(
    os.getenv("JWT_EXP_DELTA_SECONDS", "3600"))  # access: 1h
JWT_REFRESH_DELTA_SECONDS = int(
    os.getenv("JWT_REFRESH_DELTA_SECONDS", str(7 * 24 * 3600)))  # refresh: 7d


# SQLAlchemy (users)
AUTH_DB_URL = os.getenv("AUTH_DB_URL", "sqlite:///./data/auth.db")
connect_args = {"check_same_thread": False} if AUTH_DB_URL.startswith(
    "sqlite") else {}

engine = create_engine(AUTH_DB_URL, echo=False, connect_args=connect_args)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # admin | user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_auth_db() -> None:
    # garante pasta data (porque usamos sqlite em ./data/auth.db)
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_user_if_not_exists(db: Session, username: str, password: str, role: str) -> None:
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return
    db.add(
        User(
            username=username,
            password_hash=pwd_context.hash(password),
            role=role,
        )
    )
    db.commit()


def ensure_default_users() -> None:
    """
    Igual o exemplo do professor (admin/secret), mas no DB.
    Você pode trocar as senhas depois sem mexer no JWT.
    """
    db = SessionLocal()
    try:
        create_user_if_not_exists(db, "admin", "admin123", "admin")
        create_user_if_not_exists(db, "user", "user123", "user")
    finally:
        db.close()


# JWT helpers
def create_token(username: str, role: str, exp_seconds: int, token_type: str) -> str:
    payload = {
        "username": username,
        "role": role,
        "type": token_type,  # access ou refresh
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=exp_seconds),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user


# "token_required" do FastAPI
def token_required(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()

    # Esperado: Authorization: Bearer <token>
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Token ausente ou malformado (use Authorization: Bearer <token>)")

    payload = decode_token(parts[1])

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token de acesso inválido")

    return payload


def require_admin(payload: dict = Depends(token_required)) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Acesso restrito a administradores")
    return payload


# Endpoints

@router.post("/login", response_model=TokenResponse, summary="Obter token (JWT)")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access = create_token(user.username, user.role,
                          JWT_EXP_DELTA_SECONDS, "access")
    refresh = create_token(user.username, user.role,
                           JWT_REFRESH_DELTA_SECONDS, "refresh")

    return TokenResponse(
        token_type="bearer",
        access_token=access,
        refresh_token=refresh,
        expires_in=JWT_EXP_DELTA_SECONDS,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token (refresh)")
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Token malformado")

    # Busca no DB
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não existe")

    new_access = create_token(user.username, user.role,
                              JWT_EXP_DELTA_SECONDS, "access")
    new_refresh = create_token(
        user.username, user.role, JWT_REFRESH_DELTA_SECONDS, "refresh")

    return TokenResponse(
        token_type="bearer",
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=JWT_EXP_DELTA_SECONDS,
    )
