"""
CLYR v2 — Auth Middleware (Hybrid: SQLite + JWT)
Uses local auth service instead of Supabase Auth.
Keeps the same interface so routes don't need changes.
"""
from fastapi import Request, HTTPException
from app.services.auth_service import decode_access_token, get_user_by_id


async def get_current_user(request: Request) -> dict:
    """Extract and verify JWT token from Authorization header. Returns user dict."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header[7:]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", "user"),
    }


async def get_optional_user(request: Request) -> dict | None:
    """Try to get current user, return None if not authenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
