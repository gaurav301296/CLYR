import os
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from app.services.supabase_client import get_supabase_admin

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


async def get_current_user(request: Request) -> dict:
    """Extract and verify JWT from Authorization header. Returns user dict."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header[7:]
    try:
        # Verify JWT with Supabase
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return {
            "id": payload["sub"],
            "email": payload.get("email", ""),
            "role": payload.get("role", "authenticated"),
        }
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_optional_user(request: Request) -> dict | None:
    """Try to get current user, return None if not authenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
