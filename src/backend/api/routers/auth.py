"""
Authentication router for JWT and OAuth-based authentication.
Handles both JWT (username/password) and Google OAuth login flows.
"""
import secrets
from typing import Optional
from urllib.parse import urlencode
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt
import bcrypt
import hashlib
from .. import config, google
from ..dependencies import get_db, get_current_user
from ..schemas import TokenResponse, UserRegister, UserLogin, UserResponse, UserUpdate
from ...db import models

router = APIRouter()


# In-memory state storage (use Redis/cache in production)
oauth_states: dict[str, datetime] = {}

def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the user."""
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

# Password hashing functions
def _truncate_to_72_bytes(password: str) -> bytes:
    """Truncate password to 72 bytes, handling UTF-8 encoding safely."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password_bytes
    # Truncate to 72 bytes, but ensure we don't break UTF-8 sequences
    truncated = password_bytes[:72]
    # Remove any incomplete UTF-8 sequences at the end
    while truncated and truncated[-1] & 0b11000000 == 0b10000000:
        truncated = truncated[:-1]
    return truncated

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Truncate password to 72 bytes to avoid bcrypt's limit
    # This is safe because we do the same truncation when hashing
    password_bytes = _truncate_to_72_bytes(plain_password)
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes to avoid bcrypt's limit
    # This ensures passwords of any length can be hashed
    password_bytes = _truncate_to_72_bytes(password)
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def get_or_create_user(db: Session, google_user_info: dict) -> models.User:
    """Get existing user or create new user from Google OAuth info."""
    email = google_user_info.get("email", "")
    name = google_user_info.get("name", "")
    google_id = str(google_user_info.get("id", ""))
    
    # Check if user exists by OAuth provider ID or email
    user = None
    if google_id:
        user = db.query(models.User).filter(
            models.User.oauth_provider == "google",
            models.User.oauth_provider_id == google_id
        ).first()
    
    if not user and email:
        user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Use email as username, or generate from name
        username = email.split("@")[0] if email else name.lower().replace(" ", "_")
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Create new user with OAuth metadata
        user = models.User(
            username=username,
            email=email if email else None,
            oauth_provider="google",
            oauth_provider_id=google_id if google_id else None,
            hashed_password=None  # OAuth users don't have passwords
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update OAuth metadata if missing
        if not getattr(user, 'oauth_provider', None):
            setattr(user, 'oauth_provider', "google")
            setattr(user, 'oauth_provider_id', google_id if google_id else None)
            if email and not getattr(user, 'email', None):
                setattr(user, 'email', email)
            db.commit()
            db.refresh(user)
    
    return user

async def update_current_user_profile(
    update_data: UserUpdate,
    user: models.User,
    db: Session
):
    if update_data.username is not None:
        new_username = update_data.username.strip() # removes whitespace

        if not new_username:
            raise HTTPException(status_code=400, detail="New username is empty!")
        
        # check if username already exists
        existing_user = db.query(models.User).filter(models.User.username == new_username,
                                                     models.User.id != user.id).first()
        
        if existing_user:
            raise HTTPException(status_code=409, detail="Username is taken!")
        
        # no existing user
        user.username = new_username # type: ignore

    if update_data.email is not None:
        new_email = update_data.email.strip()

        if not new_email:
            raise HTTPException(status_code=400, detail="New email is empty!")
        
        existing_email = db.query(models.User).filter(models.User.email == new_email,
                                                      models.User.id != user.id).first()
        
        if existing_email:
            raise HTTPException(status_code=409, detail="Username is taken!")
        
        user.email = new_email # type: ignore 
    
    if update_data.email is None and update_data.username is None:
        raise HTTPException(status_code=400, detail="No field provided!")
    else:
        db.commit()
        db.refresh(user) # updated data

    # returns json formatted of updated user
    return UserResponse.model_validate(user)



# JWT Authentication Endpoints
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with username and password."""
    # Check if username already exists
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate username
    if not user_data.username or len(user_data.username.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty"
        )
    
    # Validate password
    if not user_data.password or len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Hash password and create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(
        username=user_data.username.strip(),
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(int(new_user.id))  # type: ignore
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login with username and password."""
    # Find user by username
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has a password (OAuth users don't have passwords)
    hashed_pwd = getattr(user, 'hashed_password', None)
    if not hashed_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account was created with OAuth. Please use OAuth to login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_data.password, hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(int(user.id))  # type: ignore
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token discard)."""
    # For now, logout is handled client-side by removing the token
    # In production, you might want to maintain a token blacklist
    return {"message": "Logged out successfully"}

# Google OAuth Endpoints
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
    return UserResponse.model_validate(user)

