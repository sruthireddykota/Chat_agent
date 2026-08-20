from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings


PUBLIC_PATHS = {
    "/api/v1/",
    "/api/v1/health",
    "/api/v1/user/login",
    "/api/v1/users",
}


def create_access_token(*, user_id: str, email_id: str, role: str = "user") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.JWT_ISSUER,
        "sub": user_id,
        "email": email_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            issuer=settings.JWT_ISSUER,
            options={"require": ["iss", "sub", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _token_from_request(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        user = decode_access_token(_token_from_request(request))
        request.state.user = user
    return user


def require_role(request: Request, role: str) -> dict:
    user = current_user(request)
    if user.get("role") != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def require_user_id(request: Request, user_id: str) -> dict:
    user = current_user(request)
    if user.get("sub") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User access denied")
    return user


async def require_session_owner(request: Request, session_id: str) -> dict:
    user = current_user(request)
    owner_id = await request.app.state.mongo_store.get_session_owner(session_id)
    if owner_id != user.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session access denied")
    return user


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        try:
            request.state.user = decode_access_token(_token_from_request(request))
        except HTTPException as exc:
            return await _json_error(exc)
        return await call_next(request)


async def _json_error(exc: HTTPException):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )
