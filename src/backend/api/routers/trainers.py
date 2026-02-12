"""
Trainer data router.
Serves precomputed trainer data from the Trainer table.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from ...db import models
from ..dependencies import get_db
from ..schemas import TrainerResponse

router = APIRouter()


@router.get("/by-route/{route_id}", response_model=list[TrainerResponse])
async def get_trainers_by_route(
    route_id: int,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all trainers matched to a specific route."""
    query = db.query(models.Trainer).filter(
        models.Trainer.route_id == route_id
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers


@router.get("/{game_name}/important", response_model=list[TrainerResponse])
async def get_important_trainers(
    game_name: str,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get only important trainers for a game."""
    query = db.query(models.Trainer).filter(
        models.Trainer.game_names.any(game_name.lower()),
        models.Trainer.is_important == True,  # noqa: E712
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers


@router.get("/{game_name}", response_model=list[TrainerResponse])
async def get_trainers_by_game(
    game_name: str,
    starter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all trainers for a game, ordered by battle_order."""
    query = db.query(models.Trainer).filter(
        models.Trainer.game_names.any(game_name.lower())
    ).order_by(asc(models.Trainer.battle_order))

    if starter:
        query = query.filter(
            (models.Trainer.starter_filter == None) |  # noqa: E711
            (func.lower(models.Trainer.starter_filter) == starter.lower())
        )

    trainers = query.all()
    return trainers
