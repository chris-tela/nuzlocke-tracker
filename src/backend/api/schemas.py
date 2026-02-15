"""
Pydantic schemas for request/response validation.
These replace input() calls from CLI and provide JSON serialization.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from ..db import models
from ..db.models import Nature, Status

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    oauth_provider: Optional[str] = None  # e.g., "google"
    oauth_provider_id: Optional[str] = None  # Provider's user ID

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for updating user profile. All fields are optional for partial updates."""
    username: Optional[str] = None
    email: Optional[str] = None

# Game File Schemas
class GameFileBase(BaseModel):
    trainer_name: str
    game_name: str
    starter_pokemon: Optional[str] = None

class GameFileCreate(GameFileBase):
    pass

class GameFileUpdate(BaseModel):
    """Schema for partial update of a game file."""
    trainer_name: Optional[str] = None
    game_name: Optional[str] = None
    starter_pokemon: Optional[str] = None

class GameFileResponse(GameFileBase):
    id: int
    user_id: int
    starter_selected: Optional[str] = None
    starter_pokemon: Optional[str] = None
    gym_progress: Optional[List[Dict[str, Any]]] = None
    route_progress: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Pokemon Schemas
class PokemonBase(BaseModel):
    id: int
    game_file_id: int
    poke_id: int
    name: str
    nickname: Optional[str] = None
    nature: Optional[Nature] = None
    ability: Optional[str] = None
    types: List[str]
    level: int = Field(ge=1, le=100)
    gender: Optional[str] = None
    status: Status
    caught_on: Optional[str] = None
    evolution_data: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PokemonCreate(BaseModel):
    poke_id: int
    nickname: Optional[str] = None
    nature: Optional[Nature] = None
    ability: Optional[str] = None
    level: int = Field(ge=1, le=100)
    gender: Optional[str] = None
    status: Status = Status.UNKNOWN
    caught_on: Optional[str] = None
    
    @field_validator('nature', mode='before')
    @classmethod
    def validate_nature(cls, v):
        """Default invalid nature values to None instead of raising validation error."""
        if v is None:
            return None
        # Try to convert string to Nature enum
        if isinstance(v, str):
            try:
                return Nature(v)
            except (ValueError, KeyError):
                return None
        # If it's already a Nature enum, return it
        if isinstance(v, Nature):
            return v
        # For any other invalid type, default to None
        return None
    
    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Default invalid status values to UNKNOWN instead of raising validation error."""
        if v is None:
            return Status.UNKNOWN
        # Try to convert string to Status enum
        if isinstance(v, str):
            try:
                return Status(v)
            except (ValueError, KeyError):
                return Status.UNKNOWN
        # If it's already a Status enum, return it
        if isinstance(v, Status):
            return v
        # For any other invalid type, default to UNKNOWN
        return Status.UNKNOWN

class PokemonUpdate(BaseModel):
    level: Optional[int] = Field(None, ge=1, le=100)
    nickname: Optional[str] = None
    status: Optional[Status] = None
    nature: Optional[Nature] = None
    ability: Optional[str] = None

class PokemonResponse(PokemonBase):
    pass  # Inherits everything from PokemonBase including Config

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

# Team Synergy Schemas
class TeamSynergyEntry(BaseModel):
    type: str
    multiplier: float
    contributors: List[str]


class TeamSynergySection(BaseModel):
    strengths: List[TeamSynergyEntry]
    weaknesses: List[TeamSynergyEntry]
    immunities: List[TeamSynergyEntry]


class TeamSynergySummary(BaseModel):
    generation: int
    team_types: List[str]
    offense: TeamSynergySection
    defense: TeamSynergySection

# Trainer Schemas
class TrainerPokemonStats(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

class TrainerPokemon(BaseModel):
    name: str
    poke_id: Optional[int] = None
    index: Optional[str] = None
    level: int
    types: List[str] = []
    ability: Optional[str] = None
    item: Optional[str] = None
    nature: Optional[str] = None
    ivs: Optional[Dict[str, int]] = None
    dvs: Optional[Dict[str, int]] = None
    evs: Optional[Dict[str, int]] = None
    moves: List[str] = []
    stats: Optional[TrainerPokemonStats] = None

class TrainerMatchupResponse(BaseModel):
    score_percent: int

class TrainerResponse(BaseModel):
    id: int
    generation: int
    game_names: List[str]
    trainer_name: str
    trainer_image: str
    location: str
    route_id: Optional[int] = None
    is_important: bool
    importance_reason: Optional[str] = None
    starter_filter: Optional[str] = None
    battle_order: int
    pokemon: List[TrainerPokemon]

    class Config:
        from_attributes = True

# Authentication Schemas
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

