"""
Pokemon management router.
Handles pokemon CRUD operations, evolution, and status management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import PokemonResponse

router = APIRouter()

### 2.4 Pokemon Management API
# - Endpoints:
#   - `GET /api/game-files/{game_file_id}/pokemon` – all pokemon, optional `status` filter.
#   - `GET /api/game-files/{game_file_id}/pokemon/party` – party only.
#   - `GET /api/game-files/{game_file_id}/pokemon/storage` – stored.
#   - `GET /api/game-files/{game_file_id}/pokemon/fainted` – fainted.
#   - `POST /api/game-files/{game_file_id}/pokemon` – add pokemon (create + party/storage decision).
#   - `PUT /api/pokemon/{pokemon_id}` – edit level/nickname/status.
#   - `POST /api/pokemon/{pokemon_id}/evolve` – perform evolution.
#   - `POST /api/pokemon/{pokemon_id}/swap` – swap party/storage.
#   - `GET /api/pokemon/all/{poke_id}` – lookup base pokemon info.
#   - `GET /api/versions/{version_name}/starters` – list starters (handles Gen 5 special‑case like CLI `starter()`).
# - Business rules reference:
#   - `add_to_team`, `add_to_party_database`, `edit_pokemon`, `evolve`, `swap_pokemon` from `cli.py`.

def verify_game_file(game_file_id: int, user: models.User, db: Session) -> models.GameFiles:

    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()

    if game_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Game File not found!")
    
    if game_file.user_id is not user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Game File not associated with User!")
    
    return game_file


@router.get("/game-files/{game_file_id}/pokemon", response_model=list[PokemonResponse])
async def get_all_pokemon(
    game_file_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pokemon for a specific game file."""
    game_file = verify_game_file(game_file_id, user, db)

    owned_pokemon = db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file.id
    ).all()

    # Return list of pokemon (empty list if no pokemon)
    return [PokemonResponse.model_validate(pokemon) for pokemon in owned_pokemon]
    
    


# @router.get("/game-files/{game_file_id}/pokemon/party")
# @router.get("/game-files/{game_file_id}/pokemon/storage")
# @router.get("/game-files/{game_file_id}/pokemon/fainted")
# @router.post("/game-files/{game_file_id}/pokemon")
# @router.put("/{pokemon_id}")
# @router.post("/{pokemon_id}/evolve")
# @router.post("/{pokemon_id}/swap")

