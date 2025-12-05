"""
Authentication router for OAuth-based authentication.
Handles OAuth login flows and JWT token generation.
"""
import secrets
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt
from .. import config, google
from ..dependencies import get_db, get_current_user
from ..schemas import OAuthTokenResponse, UserResponse
from db import models

router = APIRouter()

# In-memory state storage (use Redis/cache in production)
oauth_states: dict[str, datetime] = {}

def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the user."""
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

def get_or_create_user(db: Session, google_user_info: dict) -> models.User:
    """Get existing user or create new user from Google OAuth info."""
    email = google_user_info.get("email", "")
    name = google_user_info.get("name", "")
    google_id = google_user_info.get("id", "")
    
    # Use email as username, or generate from name
    username = email.split("@")[0] if email else name.lower().replace(" ", "_")
    
    # Check if user exists by username
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        # Create new user
        user = models.User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

@router.get("/google/login")
async def login_google():
    """Initiate Google OAuth login flow."""
    if not config.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID."
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = datetime.utcnow()
    
    # Build the Google login URL with proper URL encoding
    params = {
        "response_type": "code",
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "state": state,
        "access_type": "online"
    }
    
    auth_url = f"{config.GOOGLE_AUTHORIZATION_URL}?{urlencode(params)}"
    
    return {"url": auth_url}

@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback and create/login user."""
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    if not state:
        raise HTTPException(status_code=400, detail="No state parameter provided")
    
    # Validate state (CSRF protection)
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Check state hasn't expired (5 minutes)
    if datetime.utcnow() - oauth_states[state] > timedelta(minutes=5):
        del oauth_states[state]
        raise HTTPException(status_code=400, detail="State parameter expired")
    
    # Remove used state
    del oauth_states[state]
    
    try:
        # Exchange code for user info
        result = google.get_user_infos_from_google_token_url(code)
        
        if not result.get('status') or not result.get('user_infos'):
            raise HTTPException(
                status_code=400,
                detail="Failed to get user information from Google"
            )
        
        google_user_info = result['user_infos']
        
        # Get or create user in database
        user = get_or_create_user(db, google_user_info)
        
        # Generate JWT token
        access_token = create_access_token(int(user.id))  # type: ignore
        
        # Redirect to frontend with token
        frontend_url = config.FRONTEND_URL
        redirect_url = f"{frontend_url}/auth/callback?token={access_token}"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me")
async def get_me(user: models.User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=int(user.id),  # type: ignore
        username=str(user.username),  # type: ignore
        created_at=None
    )

