"""
User management router.
Handles user profile operations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import UserResponse, UserUpdate
from .auth import update_current_user_profile

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_me(user: models.User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(user)

@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    return await update_current_user_profile(update_data, user, db)


