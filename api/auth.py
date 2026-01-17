import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from .models import LoginRequest, TokenResponse, RefreshRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "15"))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Usuários em memória (substitua por DB se quiser)
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),
        "role": "admin",
    },
    "user": {
        "username": "user",
        "password_hash": pwd_context.hash("user123"),
        "role": "user",
    }
}

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

def create_token(*, subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,   # access / refresh
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/login", summary="Login para obter tokens JWT", response_model=TokenResponse)
def login(data: LoginRequest):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MIN)
    refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)

    access = create_token(subject=user["username"], role=user["role"], token_type="access", expires_delta=access_expires)
    refresh = create_token(subject=user["username"], role=user["role"], token_type="refresh", expires_delta=refresh_expires)

    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=int(access_expires.total_seconds()))

@router.post("/refresh", summary="Renova tokens usando refresh token", response_model=TokenResponse)
def refresh(data: RefreshRequest):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role or username not in USERS_DB:
        raise HTTPException(status_code=401, detail="Token malformado")

    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MIN)
    refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)

    new_access = create_token(subject=username, role=role, token_type="access", expires_delta=access_expires)
    new_refresh = create_token(subject=username, role=role, token_type="refresh", expires_delta=refresh_expires)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=int(access_expires.total_seconds()))
