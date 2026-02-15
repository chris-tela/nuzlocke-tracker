"""
Trainer data router.
Serves precomputed trainer data from the Trainer table.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from ...db import models
from ...team_synergy import score_team_matchup
from ..dependencies import get_current_user, get_db
from ..schemas import TrainerMatchupResponse, TrainerResponse
from ..utils import verify_game_file

router = APIRouter()


def _hydrate_trainer_pokemon_types(trainers: list[models.Trainer], db: Session) -> list[models.Trainer]:
    """
    Ensure each trainer pokemon entry has a `types` array.
    Falls back to AllPokemon lookup by poke_id when missing in trainer JSON.
    """
    missing_type_ids: set[int] = set()
    for trainer in trainers:
        for pokemon in (trainer.pokemon or []):
            if not isinstance(pokemon, dict):
                continue
            poke_id = pokemon.get("poke_id")
            types = pokemon.get("types")
            if poke_id is not None and (not isinstance(types, list) or len(types) == 0):
                missing_type_ids.add(poke_id)

    type_map: dict[int, list[str]] = {}
    if missing_type_ids:
        type_map = {
            row.poke_id: row.types
            for row in db.query(models.AllPokemon.poke_id, models.AllPokemon.types).filter(
                models.AllPokemon.poke_id.in_(missing_type_ids)
            ).all()
        }

    if not type_map:
        return trainers

    for trainer in trainers:
        pokemon_list = trainer.pokemon or []
        updated = False
        hydrated_list = []

        for pokemon in pokemon_list:
            if not isinstance(pokemon, dict):
                hydrated_list.append(pokemon)
                continue

            poke_id = pokemon.get("poke_id")
            types = pokemon.get("types")
            if poke_id in type_map and (not isinstance(types, list) or len(types) == 0):
                hydrated_list.append({**pokemon, "types": type_map[poke_id]})
                updated = True
            else:
                hydrated_list.append(pokemon)

        if updated:
            trainer.pokemon = hydrated_list

    return trainers


@router.get("/matchup/{trainer_id}", response_model=TrainerMatchupResponse)
async def get_trainer_matchup_synergy(
    trainer_id: int,
    game_file_id: int = Query(..., alias="gameFileId"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get matchup synergy % between party team and one trainer's team."""
    game_file = verify_game_file(game_file_id, user, db)
    trainer = db.query(models.Trainer).filter(models.Trainer.id == trainer_id).first()

    if trainer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found.",
        )

    version = db.query(models.Version).filter(
        models.Version.version_name == game_file.game_name
    ).first()
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version for game file not found.",
        )

    party_pokemon = db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file.id,
        models.OwnedPokemon.status == models.Status.PARTY,
    ).all()
    if len(party_pokemon) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No PARTY pokemon available to evaluate.",
        )

    team1 = [pokemon.types for pokemon in party_pokemon if pokemon.types]
    trainer_team = trainer.pokemon or []
    trainer_poke_ids = [
        pokemon.get("poke_id")
        for pokemon in trainer_team
        if isinstance(pokemon, dict) and pokemon.get("poke_id") is not None
    ]

    trainer_by_id = {}
    if trainer_poke_ids:
        trainer_by_id = {
            row.poke_id: row.types
            for row in db.query(models.AllPokemon.poke_id, models.AllPokemon.types).filter(
                models.AllPokemon.poke_id.in_(trainer_poke_ids)
            ).all()
        }

    team2 = []
    for pokemon in trainer_team:
        if not isinstance(pokemon, dict):
            continue

        types = pokemon.get("types")
        if not types and pokemon.get("poke_id") in trainer_by_id:
            types = trainer_by_id[pokemon.get("poke_id")]
        if not types:
            continue
        team2.append(types)

    if len(team2) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trainer team has no type data available.",
        )

    types_data = db.query(models.Type).all()
    if not types_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Type data not available.",
        )

    result = score_team_matchup(team1, team2, version.generation_id, types_data)
    return {"score_percent": result["score_percent"]}


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
    return _hydrate_trainer_pokemon_types(trainers, db)


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
    return _hydrate_trainer_pokemon_types(trainers, db)


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
    return _hydrate_trainer_pokemon_types(trainers, db)
