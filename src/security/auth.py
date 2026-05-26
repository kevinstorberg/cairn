from fastapi import Depends, HTTPException, Request


async def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    return parts[1]


async def require_auth(token: str | None = Depends(extract_token)) -> str:
    if token is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return token
