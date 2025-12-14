"""
Pokemon management router.
Handles pokemon CRUD operations, evolution, and status management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import PokemonResponse, PokemonCreate, PokemonUpdate

router = APIRouter()

### Pokemon Management API




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

    verify_game_file(game_file_id, user, db)

    return add_pokemon(game_file_id, pokemon, db)



def add_pokemon(game_file_id: int, pokemon: PokemonCreate, db: Session):
    pokemon_data = db.query(models.AllPokemon).filter(models.AllPokemon.poke_id == pokemon.poke_id).first()

    if pokemon_data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pokemon not found in database!")
    

    if pokemon.gender != "m" and pokemon.gender != "f":
        pokemon.gender = None
    

    
    party_pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.game_file_id == game_file_id, models.OwnedPokemon.status == models.Status.PARTY).all()

    if (len(party_pokemon) == 0 or len(party_pokemon) >= 6) and pokemon.status == models.Status.PARTY:
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

def perform_swap(partied_pokemon: models.OwnedPokemon, swap_pokemon: models.OwnedPokemon, db: Session):
    """Helper function to swap two pokemon between party and storage."""
    if partied_pokemon.status is not models.Status.PARTY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pokemon to swap is not in party")
    
    partied_pokemon.status = models.Status.STORED  # type: ignore
    swap_pokemon.status = models.Status.PARTY  # type: ignore
    
    db.commit()
    db.refresh(partied_pokemon)
    db.refresh(swap_pokemon)
    
    return {"message": "Successfully swapped!", "partied_pokemon": PokemonResponse.model_validate(partied_pokemon), "swap_pokemon": PokemonResponse.model_validate(swap_pokemon)}

    
# edit level, nickname &/or status
@router.put("/game-files/{game_file_id}/pokemon/{id}/update")
async def update_pokemon(id: int, game_file_id: int, 
                         pokemon_update: PokemonUpdate,
                         user: models.User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    
    verify_game_file(game_file_id, user, db)
    
    
    pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.id == id,
                                                   models.OwnedPokemon.game_file_id == game_file_id).first()
    
    if pokemon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="id not found in database, or associated with user!")
    
    if pokemon_update.level is not None:
        pokemon.level = int(pokemon_update.level)  # type: ignore
    
    if pokemon_update.nickname is not None:
        pokemon.nickname = str(pokemon_update.nickname)  # type: ignore

    if pokemon_update.status is not None:
        # Check if trying to set status to PARTY and party is already full
        if pokemon_update.status == models.Status.PARTY:
            party_pokemon = db.query(models.OwnedPokemon).filter(
                models.OwnedPokemon.game_file_id == game_file_id,
                models.OwnedPokemon.status == models.Status.PARTY
            ).all()
            
            # If current pokemon is already in party, exclude it from count
            party_count = len(party_pokemon)
            if pokemon.status is models.Status.PARTY:
                # Current pokemon is already counted in party_pokemon, so subtract 1
                party_count -= 1
            
            if party_count >= 6:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Party is full (6 pokemon). Use the swap endpoint to replace a party member: POST /api/pokemon/game-files/{game_file_id}/pokemon_party/{{pokemon_party_id}}/pokemon/{id}/swap"
                )
        
        pokemon.status = pokemon_update.status  # type: ignore


    db.commit()
    db.refresh(pokemon)
    
    return PokemonResponse.model_validate(pokemon)
    
    



@router.post("/game-files/{game_file_id}/pokemon/{id}/evolve/{evolved_pokemon_name}")
async def evolve_pokemon(id: int, evolved_pokemon_name: str, game_file_id: int, 
                         user: models.User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
        
        verify_game_file(game_file_id, user, db)

        pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.id == id,
                                                   models.OwnedPokemon.game_file_id == game_file_id).first()
        
        if pokemon is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="id not found in database, or associated with user!")
        
        evolved_pokemon = db.query(models.AllPokemon).filter(models.AllPokemon.name == evolved_pokemon_name).first()

        if evolved_pokemon is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="Evolved pokemon not found in database! Please input correct name")

    
        evolution_data = pokemon.evolution_data

        if evolution_data is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="pokemon does not have an evolution!")
        
        for evolution in evolution_data:
            if evolution["evolves_to"]["species"] == evolved_pokemon_name.lower(): # type: ignore
                evolution_details = evolution["evolves_to"]["evolution_details"]
                for evo_detail in evolution_details:
                    if evo_detail["min_level"] is not None and str(evo_detail["trigger"]["name"]) == "level-up": # type: ignore
                        if pokemon.level >= evo_detail["min_level"]: # type: ignore
                            return evolve(pokemon, evolved_pokemon, db)
                        # throw error
                        else:
                            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pokemon hasn't reached the level requirement yet!")


                    # evolve
                    if evo_detail["min_level"] is None:
                        return evolve(pokemon, evolved_pokemon, db)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evolution not found!")

# TODO: update ability (if  abilities__contains__(ability) --> keep, else, ?)
def evolve(current_pokemon: models.OwnedPokemon, evolved_pokemon: models.AllPokemon, db: Session):
    
    current_pokemon.name = evolved_pokemon.name
    current_pokemon.poke_id = evolved_pokemon.poke_id
    current_pokemon.types = evolved_pokemon.types
    current_pokemon.evolution_data =evolved_pokemon.evolution_data
    current_pokemon.sprite = evolved_pokemon.sprite

    db.commit()
    db.refresh(current_pokemon)

    return PokemonResponse.model_validate(current_pokemon)

    
    



        

    
@router.post("/game-files/{game_file_id}/pokemon_party/{pokemon_party_id}/pokemon/{pokemon_switch_id}/swap", status_code=status.HTTP_200_OK)
async def swap_pokemon(pokemon_party_id: int, pokemon_switch_id: int, game_file_id: int, 
                         user: models.User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    
    verify_game_file(game_file_id, user, db)
 
   
    partied_pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.id == pokemon_party_id,
                                                   models.OwnedPokemon.game_file_id == game_file_id).first()
        
    if partied_pokemon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="id not found in database, or associated with user!")
    
    swap_pokemon = db.query(models.OwnedPokemon).filter(models.OwnedPokemon.id == pokemon_switch_id,
                                                   models.OwnedPokemon.game_file_id == game_file_id).first()
        
    if swap_pokemon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="id not found in database, or associated with user!")

    return perform_swap(partied_pokemon, swap_pokemon, db)


@router.get("/{poke_id}")
async def get_pokemon_info(
    poke_id: int,
    db: Session = Depends(get_db)
):
    """Get base pokemon information by poke_id."""
    pokemon = db.query(models.AllPokemon).filter(models.AllPokemon.poke_id == poke_id).first()
    
    if pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pokemon with poke_id {poke_id} not found in database!"
        )
    
    return {
        "poke_id": pokemon.poke_id,
        "name": pokemon.name,
        "types": pokemon.types,
        "abilities": pokemon.abilities,
        "weight": pokemon.weight,
        "base_hp": pokemon.base_hp,
        "base_attack": pokemon.base_attack,
        "base_defense": pokemon.base_defense,
        "base_special_attack": pokemon.base_special_attack,
        "base_special_defense": pokemon.base_special_defense,
        "base_speed": pokemon.base_speed,
        "evolution_data": pokemon.evolution_data,
        "sprite": pokemon.sprite
    }


@router.get("/versions/{version_name}/starters")
async def get_starters(
    version_name: str,
    db: Session = Depends(get_db)
):
    """Get starter pokemon list for a version. Handles Gen 5 special case."""
    version = db.query(models.Version).filter(models.Version.version_name == version_name).first()
    
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_name}' not found in database!"
        )
    
    gen = db.query(models.Generation).filter(
        models.Generation.generation_id == version.generation_id
    ).first()
    
    if gen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation for version '{version_name}' not found!"
        )
    
    pokedex = gen.pokemon
    
    # Gen 5 pokedex starts with victini, which breaks the pattern
    generation_id = getattr(gen, 'generation_id', None)
    if generation_id == 5:
        starters = pokedex[1:4]  # Skip index 0 (Victini), get next 3
    else:
        starters = pokedex[0:3]  # First 3 pokemon are starters
    
    return {"starters": starters}


    