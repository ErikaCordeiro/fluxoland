"""Authentication module.

Handles user authentication, password hashing, and session management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from database import SessionLocal
from models import User
from templates import templates

logger = logging.getLogger(__name__)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constants
MAX_PASSWORD_LENGTH = 72  # Bcrypt limit


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash.
        
    Returns:
        Hashed password string.
        
    Note:
        Bcrypt has a 72-byte limit. Password is truncated if longer.
    """
    if len(password) > MAX_PASSWORD_LENGTH:
        password = password[:MAX_PASSWORD_LENGTH]
        logger.warning("Password truncated to 72 characters for hashing")
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.
        
    Returns:
        True if password matches, False otherwise.
    """
    try:
        if len(plain_password) > MAX_PASSWORD_LENGTH:
            plain_password = plain_password[:MAX_PASSWORD_LENGTH]
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def _authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password.
    
    Args:
        db: Database session.
        email: User's email address.
        password: User's plain text password.
        
    Returns:
        User object if authentication successful, None otherwise.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.warning(f"Login attempt for non-existent user: {email}")
        return None
    
    if not verify_password(password, user.senha_hash):
        logger.warning(f"Invalid password attempt for user: {email}")
        return None
    
    if not user.ativo:
        logger.warning(f"Login attempt for inactive user: {email}")
        return None
    
    return user


@router.get("/login")
async def get_login(request: Request):
    """Display login page.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        Rendered login template.
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


@router.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
):
    """Process login form submission.
    
    Args:
        request: FastAPI request object.
        email: User's email from form.
        senha: User's password from form.
        
    Returns:
        Redirect to propostas on success, or login page with error.
    """
    db: Session = SessionLocal()
    
    try:
        user = _authenticate_user(db, email, senha)
        
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "erro": "Usuário ou senha inválidos",
                },
                status_code=400,
            )
        
        # Set session data
        request.session["user_id"] = user.id
        request.session["user_nome"] = user.nome
        request.session["user_role"] = user.role.value
        
        logger.info(f"User logged in successfully: {email}")
        
        return RedirectResponse(
            url="/propostas",
            status_code=HTTP_302_FOUND,
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "erro": "Erro no servidor. Tente novamente.",
            },
            status_code=500,
        )
    finally:
        db.close()


@router.get("/logout")
async def logout(request: Request):
    """Log out current user and clear session.
    
    Args:
        request: FastAPI request object.
        
    Returns:
        Redirect to login page.
    """
    user_email = request.session.get("user_nome", "Unknown")
    request.session.clear()
    
    logger.info(f"User logged out: {user_email}")
    
    return RedirectResponse(
        url="/login",
        status_code=HTTP_302_FOUND,
    )
