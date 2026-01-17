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
from utils.logger import logger  # Logger central


# Configurações de JWT

JWT_SECRET = os.getenv("JWT_SECRET", "MEUSEGREDOAQUI")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = int(
    os.getenv("JWT_EXP_DELTA_SECONDS", "3600"))  # access: 1h
JWT_REFRESH_DELTA_SECONDS = int(
    os.getenv("JWT_REFRESH_DELTA_SECONDS", str(7 * 24 * 3600)))  # refresh: 7d


# Configuração do Banco de Usuários
AUTH_DB_URL = os.getenv("AUTH_DB_URL", "sqlite:///./data/auth.db")
connect_args = {"check_same_thread": False} if AUTH_DB_URL.startswith(
    "sqlite") else {}

engine = create_engine(AUTH_DB_URL, echo=False, connect_args=connect_args)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Modelo de Usuário


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # admin | user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Funções auxiliares do DB


def init_auth_db() -> None:
    """Cria a tabela de usuários (se não existir)"""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(engine)
    logger.info("Banco de autenticação inicializado.")


def get_db() -> Generator[Session, None, None]:
    """Dependência de sessão de banco (usada nos endpoints)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.info("Sessão do banco de autenticação encerrada.")


def create_user_if_not_exists(db: Session, username: str, password: str, role: str) -> None:
    """Cria um usuário no DB se ele ainda não existir"""
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return
    db.add(User(username=username, password_hash=pwd_context.hash(password), role=role))
    db.commit()
    logger.info(f"Usuário criado: {username} (role={role})")


def ensure_default_users() -> None:
    """Garante que os usuários admin/user existam por padrão"""
    db = SessionLocal()
    try:
        create_user_if_not_exists(db, "admin", "admin123", "admin")
        create_user_if_not_exists(db, "user", "user123", "user")
        logger.info("Usuários padrão garantidos no banco de autenticação.")
    finally:
        db.close()
        logger.info("Sessão do banco de autenticação encerrada.")


# JWT Helpers
def create_token(username: str, role: str, exp_seconds: int, token_type: str) -> str:
    """
    Gera um token JWT com os dados do usuário e expiração definida.
    """
    payload = {
        "username": username,
        "role": role,
        "type": token_type,  # "access" ou "refresh"
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=exp_seconds),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.debug(f"Token JWT criado para {username} (type={token_type})")
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decode_token(token: str) -> dict:
    """
    Decodifica o token JWT e valida assinatura/expiração.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        logger.warning("Token expirado.")
        raise HTTPException(status_code=401, detail="Token expirado")
    except InvalidTokenError:
        logger.warning("Token inválido.")
        raise HTTPException(status_code=401, detail="Token inválido")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Verifica se o usuário e senha estão corretos.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Usuário não encontrado: {username}")
        return None
    if not pwd_context.verify(password, user.password_hash):
        logger.warning(f"Senha inválida para usuário: {username}")
        return None
    logger.info(f"Usuário autenticado: {username}")
    return user


# Dependências de segurança
def token_required(request: Request) -> dict:
    """
    Verifica se o token JWT válido foi enviado no header Authorization.
    """
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Token ausente ou malformado no header Authorization.")
        raise HTTPException(
            status_code=401,
            detail="Token ausente ou malformado (use Authorization: Bearer <token>)"
        )

    payload = decode_token(parts[1])

    if payload.get("type") != "access":
        logger.warning("Token de acesso inválido.")
        raise HTTPException(status_code=401, detail="Token de acesso inválido")

    logger.debug(f"Token válido para usuário: {payload.get('username')}")

    return payload


def require_admin(payload: dict = Depends(token_required)) -> dict:
    """
    Garante que o usuário tenha role "admin".
    """
    if payload.get("role") != "admin":
        logger.warning(
            "Usuário sem permissão de administrador tentou acessar recurso protegido.")
        raise HTTPException(
            status_code=403, detail="Acesso restrito a administradores")
    logger.debug(
        f"Usuário administrador autorizado: {payload.get('username')}")
    return payload


# Endpoints de autenticação

@router.post("/login", response_model=TokenResponse, summary="Obter token JWT")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Realiza login com username e password. Retorna tokens JWT (access + refresh).
    """
    user = authenticate_user(db, data.username, data.password)
    if not user:
        logger.warning(
            f"Tentativa de login inválida para usuário: {data.username}")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access = create_token(user.username, user.role,
                          JWT_EXP_DELTA_SECONDS, "access")
    refresh = create_token(user.username, user.role,
                           JWT_REFRESH_DELTA_SECONDS, "refresh")

    logger.info(f"Login bem-sucedido: {user.username} (role={user.role})")
    return TokenResponse(
        token_type="bearer",
        access_token=access,
        refresh_token=refresh,
        expires_in=JWT_EXP_DELTA_SECONDS,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token JWT")
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """
    Recebe um refresh token válido e gera novos tokens JWT.
    """
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        logger.warning("Refresh token inválido.")
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    username = payload.get("username")
    if not username:
        logger.warning("Token malformado: username ausente.")
        raise HTTPException(status_code=401, detail="Token malformado")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Usuário do token não existe: {username}")
        raise HTTPException(status_code=401, detail="Usuário não existe")

    new_access = create_token(user.username, user.role,
                              JWT_EXP_DELTA_SECONDS, "access")
    new_refresh = create_token(
        user.username, user.role, JWT_REFRESH_DELTA_SECONDS, "refresh")

    logger.info(f"Tokens renovados para {user.username}")
    return TokenResponse(
        token_type="bearer",
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=JWT_EXP_DELTA_SECONDS,
    )
