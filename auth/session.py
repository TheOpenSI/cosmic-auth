from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, Response

from auth import config
from auth.providers.base import NormalizedClaims


def _cookie_kwargs(max_age: int | None = None) -> dict:
    secure = config.AUTH_PUBLIC_URL.startswith("https://")
    kwargs = {
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "path": "/",
    }
    if max_age is not None:
        kwargs["max_age"] = max_age
    return kwargs


def issue_session_token(claims: NormalizedClaims) -> str:
    """Build a Cosmic JWT from normalized IdP claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": claims.sub,
        "email": claims.email,
        "name": claims.name,
        "roles": claims.roles,
        "provider": claims.provider,
        # "user_id": ...  # Phase 3 — Postgres user id
        "iat": now,
        "exp": now + timedelta(seconds=config.SESSION_MAX_AGE),
    }
    return jwt.encode(payload, config.SESSION_SECRET, algorithm="HS256")


def set_session_cookie(response: Response, claims: NormalizedClaims) -> None:
    token = issue_session_token(claims)
    response.set_cookie(
        config.SESSION_COOKIE_NAME,
        token,
        **_cookie_kwargs(config.SESSION_MAX_AGE),
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(config.SESSION_COOKIE_NAME, path="/")


def read_session(request: Request) -> dict:
    """Decode + verify Cosmic session cookie. Raises 401 if missing/invalid."""
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        return jwt.decode(
            token,
            config.SESSION_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp","iat","sub"]}
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired session"
        ) from exc