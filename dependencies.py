"""FastAPI dependencies for authentication and authorization.

Provides reusable dependencies for protecting routes and checking permissions.
"""

import logging
from typing import Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole

logger = logging.getLogger(__name__)


def get_current_user_html(
    request: Request,
    db: Session = Depends(get_db),
) -> Union[User, RedirectResponse]:
    """Get current authenticated user for HTML routes.
    
    Args:
        request: FastAPI request object.
        db: Database session dependency.
        
    Returns:
        User object if authenticated, RedirectResponse to login if not.
        
    Example:
        ```python
        @router.get("/dashboard")
        def dashboard(user: User = Depends(get_current_user_html)):
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "user": user
            })
        ```
    """
    user_id = request.session.get("user_id")
    
    if not user_id:
        logger.warning("Unauthenticated access attempt to protected route")
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND,
        )
    
    user = db.get(User, user_id)
    
    if not user:
        logger.warning(f"Invalid user_id in session: {user_id}")
        request.session.clear()
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND,
        )
    
    if not user.ativo:
        logger.warning(f"Inactive user access attempt: {user.email}")
        request.session.clear()
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND,
        )
    
    return user


def get_current_user_api(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user for API routes.
    
    Args:
        request: FastAPI request object.
        db: Database session dependency.
        
    Returns:
        User object if authenticated.
        
    Raises:
        HTTPException: 401 if not authenticated or user invalid.
        
    Example:
        ```python
        @router.get("/api/profile")
        def get_profile(user: User = Depends(get_current_user_api)):
            return {"name": user.nome, "email": user.email}
        ```
    """
    user_id = request.session.get("user_id")
    
    if not user_id:
        logger.warning("Unauthenticated API access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    user = db.get(User, user_id)
    
    if not user:
        logger.warning(f"Invalid user_id in API session: {user_id}")
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )
    
    if not user.ativo:
        logger.warning(f"Inactive user API access attempt: {user.email}")
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive",
        )
    
    return user


def require_lider_html(
    current_user: Union[User, RedirectResponse] = Depends(get_current_user_html),
) -> Union[User, RedirectResponse]:
    """Require lider role for HTML routes.
    
    Args:
        current_user: Current user from authentication dependency.
        
    Returns:
        User if they are a lider, RedirectResponse otherwise.
        
    Example:
        ```python
        @router.get("/admin")
        def admin_panel(user: User = Depends(require_lider_html)):
            return templates.TemplateResponse("admin.html", {
                "request": request,
                "user": user
            })
        ```
    """
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    if current_user.role != UserRole.lider:
        logger.warning(
            f"Unauthorized lider access attempt by: {current_user.email}"
        )
        return RedirectResponse(
            url="/propostas",
            status_code=status.HTTP_302_FOUND,
        )
    
    return current_user


def require_lider_api(
    current_user: User = Depends(get_current_user_api),
) -> User:
    """Require lider role for API routes.
    
    Args:
        current_user: Current user from API authentication dependency.
        
    Returns:
        User if they are a lider.
        
    Raises:
        HTTPException: 403 if user is not a lider.
        
    Example:
        ```python
        @router.delete("/api/users/{user_id}")
        def delete_user(
            user_id: int,
            admin: User = Depends(require_lider_api)
        ):
            # Only lideres can delete users
            ...
        ```
    """
    if current_user.role != UserRole.lider:
        logger.warning(
            f"Unauthorized API lider access attempt by: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    return current_user


def require_vendedor_html(
    current_user: Union[User, RedirectResponse] = Depends(get_current_user_html),
) -> Union[User, RedirectResponse]:
    """Require vendedor or lider role for HTML routes.
    
    Args:
        current_user: Current user from authentication dependency.
        
    Returns:
        User if they are vendedor or lider, RedirectResponse otherwise.
    """
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    if current_user.role not in [UserRole.vendedor, UserRole.lider]:
        logger.warning(
            f"Unauthorized vendedor access attempt by: {current_user.email}"
        )
        return RedirectResponse(
            url="/propostas",
            status_code=status.HTTP_302_FOUND,
        )
    
    return current_user


def require_vendedor_api(
    current_user: User = Depends(get_current_user_api),
) -> User:
    """Require vendedor or lider role for API routes.
    
    Args:
        current_user: Current user from API authentication dependency.
        
    Returns:
        User if they are vendedor or lider.
        
    Raises:
        HTTPException: 403 if user is not vendedor or lider.
    """
    if current_user.role not in [UserRole.vendedor, UserRole.lider]:
        logger.warning(
            f"Unauthorized API vendedor access attempt by: {current_user.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    return current_user
