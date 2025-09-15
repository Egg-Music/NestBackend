from fastapi import Header, HTTPException, status
from .config import settings

async def auth_dependency(authorization: str | None = Header(default=None)):
    if not settings.require_auth:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    # TODO: Verify JWT if you have a real issuer/audience
    # token = authorization.split(" ", 1)[1]
    return

