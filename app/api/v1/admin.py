"""Admin endpoints — user creation, seed data."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.api.deps import require_role

router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    """Create user request."""

    email: str
    username: str
    password: str
    full_name: str | None = None
    role_name: str = "analyst"


@router.post("/users", response_model=dict)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin"))] = None,
):
    """Create a new user (admin only)."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{payload.role_name}' not found")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "username": user.username, "role": payload.role_name}


@router.post("/seed")
def seed_initial_data(
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin"))] = None,
):
    """Seed initial admin user if none exists (admin only)."""
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        return {"message": "Admin user already exists"}

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        return {"message": "Roles not seeded. Run migrations first."}

    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin"),
        full_name="System Administrator",
        role_id=admin_role.id,
        is_superuser=True,
    )
    db.add(admin)
    db.commit()
    return {"message": "Admin user created. Change password immediately."}
