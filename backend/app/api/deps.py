"""Shared request dependencies: the signed-in user and role checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models import Role, User

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

# Read-only screens a farmer may open for the fields linked to them. The field filter
# (``visible_to``) does the scoping; writes keep their staff-only dependencies.
READER_ROLES = (Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER, Role.FARMER)


def require_roles(*roles: Role) -> Callable[[User], User]:
    """Dependency factory. Permissions are enforced here, not only in the interface."""

    def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted")
        return user

    return checker


ReaderUser = Annotated[User, Depends(require_roles(*READER_ROLES))]
