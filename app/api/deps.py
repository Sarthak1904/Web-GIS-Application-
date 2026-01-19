"""FastAPI dependencies for database, auth, and RBAC."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, Role

security = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    """Get current user from JWT if present; otherwise None (for public endpoints)."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id), User.is_active).first()
    return user


def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> User:
    """Require authenticated user; raise 401 if not present."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        role_name = "public"
        if current_user.role_id:
            role = db.query(Role).filter(Role.id == current_user.role_id).first()
            if role:
                role_name = role.name

        if current_user.is_superuser:
            return current_user
        if role_name in allowed_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}",
        )

    return role_checker


# Convenience dependencies
RequireAdmin = Depends(require_role("admin"))
RequireAnalyst = Depends(require_role("admin", "analyst"))
RequirePublic = Depends(require_role("admin", "analyst", "public"))
