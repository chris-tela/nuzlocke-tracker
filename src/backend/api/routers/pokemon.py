"""
Pokemon management router.
Handles pokemon CRUD operations, evolution, and status management.
"""
from sqlalchemy import Column
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import PokemonResponse, PokemonCreate, PokemonBase, PokemonUpdate

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
    

    
@router.get("/game-files/{game_file_id}/pokemon/party")
async def get_party_pokemon(game_file_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    game_file = verify_game_file(game_file_id, user, db)

    owned_pokemon = db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file.id
    ).all()

    # Return list of pokemon (empty list if no pokemon)
    return [PokemonResponse.model_validate(pokemon) for pokemon in owned_pokemon if pokemon.status is models.Status.PARTY]
@router.get("/game-files/{game_file_id}/pokemon/storage")
async def get_stored_pokemon(game_file_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)
    owned_pokemon = db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file.id
    ).all()

    # Return list of pokemon (empty list if no pokemon)
    return [PokemonResponse.model_validate(pokemon) for pokemon in owned_pokemon if pokemon.status is models.Status.STORED]
 
@router.get("/game-files/{game_file_id}/pokemon/fainted")
async def get_fainted_pokemon(game_file_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)
    owned_pokemon = db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file.id
    ).all()

    # Return list of pokemon (empty list if no pokemon)
    return [PokemonResponse.model_validate(pokemon) for pokemon in owned_pokemon if pokemon.status is models.Status.FAINTED]
 

@router.post("/game-files/{game_file_id}/pokemon")
async def create_pokemon(game_file_id: int, pokemon: PokemonCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)
    if game_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="game file cannot be found!")
    else:
        return add_pokemon(game_file_id, pokemon, db)



def add_pokemon(game_file_id: int, pokemon: PokemonCreate, db: Session):
    pokemon_data = db.query(models.AllPokemon).filter(models.AllPokemon.poke_id == pokemon.poke_id).first()

    if pokemon_data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pokemon not found in database!")
    

    if pokemon.gender != "m" or pokemon.gender != "f":
        pokemon.gender = None
    

    
    party_pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.game_file_id == game_file_id, models.OwnedPokemon.status == models.Status.PARTY).all()

    if party_pokemon is not None and len(party_pokemon) >= 6 and pokemon.status == models.Status.PARTY:
         pokemon.status = models.Status.UNKNOWN

    
    pokemon_to_db = models.OwnedPokemon(
        game_file_id = game_file_id,
        poke_id = pokemon_data.poke_id,
        name = pokemon_data.name,
        nickname = pokemon.nickname,
        nature = pokemon.nature,
        types = pokemon_data.types,
        level = pokemon.level,
        gender = pokemon.gender,
        status = pokemon.status,
        evolution_data = pokemon_data.evolution_data,
        sprite = pokemon_data.sprite
    )

    db.add(pokemon_to_db)
    db.commit()
    db.refresh(pokemon_to_db)
    
    return PokemonResponse.model_validate(pokemon_to_db)

    
# edit level, nickname &/or status
@router.put("{game_file_id}/pokemon/{id}")
async def update_pokemon(id: int, game_file_id: int, 
                         pokemon_update: PokemonUpdate,
                         user: models.User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    
    game_file = verify_game_file(game_file_id, user, db)
    if game_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="game file cannot be found!")
    
    pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.id == id,
                                                   models.OwnedPokemon.game_file_id == game_file_id).first()
    
    if pokemon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="id not found in database, or associated with user!")
    
    if pokemon_update.level is not None:
        pokemon.level = int(pokemon_update.level)  # type: ignore
    
    if pokemon_update.nickname is not None:
        pokemon.nickname = str(pokemon_update.nickname)  # type: ignore

    if pokemon_update.status is not None:
        pokemon.status = pokemon_update.status  # type: ignore
    
    db.commit()
    db.refresh(pokemon)
    
    return PokemonResponse.model_validate(pokemon)
    
    



# @router.post("/{pokemon_id}/evolve")
# @router.post("/{pokemon_id}/swap")

