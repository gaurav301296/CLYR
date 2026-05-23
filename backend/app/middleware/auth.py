"""
CLYR Auth Middleware
Verifies access tokens from the local auth service.
"""
from fastapi import Request, HTTPException
from app.services.auth_service import _verify_access_token, get_user_by_id


async def get_current_user(request: Request) -> dict:
    """Extract and verify token from Authorization header. Returns user dict."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header[7:]
    payload = _verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
    }


async def get_optional_user(request: Request) -> dict | None:
    """Try to get current user, return None if not authenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
