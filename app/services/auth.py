"""Sesje administratora (cookie)."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Cookie, HTTPException

from app.config import settings

_active_sessions: set[str] = set()


def create_admin_session() -> str:
    token = str(uuid.uuid4())
    _active_sessions.add(token)
    return token


def destroy_admin_session(token: Optional[str]) -> None:
    if token and token in _active_sessions:
        _active_sessions.discard(token)


def is_authenticated(admin_session: Optional[str]) -> bool:
    return bool(admin_session and admin_session in _active_sessions)


def verify_credentials(username: str, password: str) -> bool:
    return username == settings.admin_user and password == settings.admin_password


def require_admin_cookie(admin_session: Optional[str] = Cookie(None)) -> str:
    """Dependency FastAPI — wymaga ważnej sesji admina."""
    if not is_authenticated(admin_session):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin_session  # type: ignore[return-value]
