"""
Pydantic schemas for request/response validation.
These replace input() calls from CLI and provide JSON serialization.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    oauth_provider: Optional[str] = None  # e.g., "google", "github"
    oauth_provider_id: Optional[str] = None  # Provider's user ID

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Game File Schemas
class GameFileBase(BaseModel):
    trainer_name: str
    game_name: str

class GameFileCreate(GameFileBase):
    pass

class GameFileResponse(GameFileBase):
    id: int
    user_id: int
    gym_progress: Optional[List[Dict[str, Any]]] = None
    route_progress: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Pokemon Schemas
class PokemonBase(BaseModel):
    poke_id: int
    name: str
    nickname: Optional[str] = None
    nature: Optional[str] = None
    ability: Optional[str] = None
    types: List[str]
    level: int = Field(ge=1, le=100)
    gender: Optional[str] = None
    status: str
    sprite: str
    evolution_data: Optional[List[Dict[str, Any]]] = None

class PokemonCreate(PokemonBase):
    game_file_id: int

class PokemonUpdate(BaseModel):
    level: Optional[int] = Field(None, ge=1, le=100)
    nickname: Optional[str] = None
    status: Optional[str] = None

class PokemonResponse(PokemonBase):
    id: int
    game_file_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Route Schemas
class RouteProgressUpdate(BaseModel):
    location_name: str

class RouteProgressResponse(BaseModel):
    route_progress: List[str]
    upcoming_routes: List[str]

# Gym Schemas
class GymProgressUpdate(BaseModel):
    gym_number: str
    location: str
    badge_name: str

class GymProgressResponse(BaseModel):
    gym_progress: List[Dict[str, Any]]
    upcoming_gyms: List[Dict[str, Any]]

# OAuth Schemas
class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

