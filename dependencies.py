from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole


# ======================================================
# USO EM ROTAS HTML (TEMPLATES)
# ======================================================
def get_current_user_html(
    request: Request,
    db: Session = Depends(get_db),
) -> User | RedirectResponse:
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND,
        )

    user = db.get(User, user_id)

    if not user:
        request.session.clear()
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND,
        )

    return user


def require_lider_html(
    current_user: User | RedirectResponse = Depends(get_current_user_html),
) -> User | RedirectResponse:
    if isinstance(current_user, RedirectResponse):
        return current_user

    if current_user.role != UserRole.lider:
        return RedirectResponse(
            url="/propostas",
            status_code=status.HTTP_302_FOUND,
        )

    return current_user


# ======================================================
# USO EM ROTAS API (JSON)
# ======================================================
def get_current_user_api(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    return user


def require_lider_api(
    current_user: User = Depends(get_current_user_api),
) -> User:
    if current_user.role != UserRole.lider:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para líderes",
        )

    return current_user
