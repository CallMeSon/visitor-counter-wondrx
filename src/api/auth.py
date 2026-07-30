import os
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from google.oauth2 import id_token
from google.auth.transport import requests

# Load .env file automatically
load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

class GoogleTokenRequest(BaseModel):
    token: str

def is_email_allowed(email: str, allowed_str: str) -> bool:
    if not email or not allowed_str:
        return False
    allowed_emails = [e.strip().lower() for e in allowed_str.split(",") if e.strip()]
    return email.strip().lower() in allowed_emails

def create_session_token(email: str, secret_key: str) -> str:
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps({"email": email}, salt="auth-session")

def verify_session_token(token: str, secret_key: str, max_age: int = 86400 * 7) -> Optional[str]:
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        data = serializer.loads(token, salt="auth-session", max_age=max_age)
        return data.get("email")
    except (BadSignature, SignatureExpired):
        return None

def verify_google_id_token(id_token_str: str, client_id: str) -> Optional[dict]:
    try:
        id_info = id_token.verify_oauth2_token(id_token_str, requests.Request(), client_id)
        return id_info
    except Exception:
        return None

def get_current_user(request: Request) -> str:
    session_token = request.cookies.get("session")
    secret_key = os.environ.get("SESSION_SECRET_KEY", "secret_random_visitor_counter_wondrx_2026_key")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = verify_session_token(session_token, secret_key)
    if not email:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return email

@router.get("/config")
async def get_auth_config():
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    return {"google_client_id": client_id}

@router.post("/google")
async def google_login(payload: GoogleTokenRequest, response: Response):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    allowed_emails = os.environ.get("ALLOWED_EMAILS", "")
    secret_key = os.environ.get("SESSION_SECRET_KEY", "secret_random_visitor_counter_wondrx_2026_key")

    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured on server")

    id_info = verify_google_id_token(payload.token, client_id)
    if not id_info:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = id_info.get("email")
    if not email or not is_email_allowed(email, allowed_emails):
        raise HTTPException(status_code=403, detail="Email is not authorized to access this application")

    session_token = create_session_token(email, secret_key)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400 * 7
    )
    return {"message": "Login successful", "email": email}

@router.get("/me")
async def get_me(user_email: str = Depends(get_current_user)):
    return {"authenticated": True, "email": user_email}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session")
    return {"message": "Logged out successfully"}
