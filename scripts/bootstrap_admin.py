#!/usr/bin/env python3
"""Bootstrap initial admin user. Run after migrations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings
from app.core.security import get_password_hash
from app.models.user import User, Role

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    if db.query(User).filter(User.username == "admin").first():
        print("Admin user already exists.")
        sys.exit(0)

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        print("Roles not found. Run alembic upgrade head first.")
        sys.exit(1)

    admin = User(
        email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
        username=os.getenv("ADMIN_USERNAME", "admin"),
        hashed_password=get_password_hash(os.getenv("ADMIN_PASSWORD", "admin")),
        full_name="System Administrator",
        role_id=admin_role.id,
        is_superuser=True,
    )
    db.add(admin)
    db.commit()
    print("Admin user created. Change password in production.")
finally:
    db.close()
