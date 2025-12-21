"""
Route/encounter management router.
Handles route progression and encounter data.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import PokemonCreate
from .pokemon import add_pokemon as add_pokemon_to_game


router = APIRouter()


# find version through game file
@router.get("/game-files/{game_file_id}/routes", status_code=200)
async def ordered_route_list(game_file_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)

    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot find version name associated with game file!")
    
    return {"data": version.locations_ordered}
    
# get encounter data from a route
# allow route name and route_id 
@router.get("/{version_id}/{route_}", status_code=200)
async def get_route_encounters(version_id: int, route_: str, db: Session = Depends(get_db)):
    """Get route encounters by route_id (integer) or route_name (string)."""
    # Try to parse as integer first (route_id)
    try:
        route_id = int(route_)
        route = db.query(models.Route).filter(models.Route.id == route_id, models.Route.version_id == version_id).first()
    except ValueError:
        # If not a number, treat as route_name
        route = db.query(models.Route).filter(models.Route.name == route_.lower(), models.Route.version_id == version_id).first()
    
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found!")
    
    return {"route": route.name, "data": route.data}

    
    
@router.get("/game-files/{game_file_id}/route-progress")
async def get_route_progress(game_file_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)

    return {"routes_discovered": game_file.route_progress}

def get_upcoming_routes_list(game_file: models.GameFiles, db: Session) -> list[str]:
    """Helper function to get upcoming routes list."""
    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")
    
    # Get locations_ordered from version (ensure it's a list)
    locations_ordered_value = getattr(version, 'locations_ordered', None)
    if locations_ordered_value is None:
        locations_ordered = []
    else:
        locations_ordered = list(locations_ordered_value)
    
    # Get route_progress from game_file
    route_progress_value = getattr(game_file, 'route_progress', None)
    route_progress = list(route_progress_value) if route_progress_value else []
    
    # Calculate difference: locations_ordered minus route_progress
    # This gives us routes that haven't been discovered yet
    upcoming_routes = locations_ordered.copy()
    for route in route_progress:
        if route in upcoming_routes:
            upcoming_routes.remove(route)
    
    return upcoming_routes

@router.get("/game-files/{game_file_id}/upcoming_routes")
async def get_upcoming_routes(game_file_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get upcoming routes by finding the difference between ordered locations and route progress."""
    
    game_file = verify_game_file(game_file_id, user, db)
    upcoming_routes = get_upcoming_routes_list(game_file, db)
    
    return {"upcoming_routes": upcoming_routes}

# confirm route has been 'complete'
@router.post("/game-files/{game_file_id}/route-progressed/{route}", status_code=201)
async def add_route(game_file_id: int, route: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a route to route_progress only if it's in upcoming_routes."""
    
    game_file = verify_game_file(game_file_id, user, db)

    # 1. get upcoming routes
    upcoming_routes = get_upcoming_routes_list(game_file, db)

    # 2. evaluate whether route is in upcoming_routes
    if route not in upcoming_routes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Route '{route}' is not in upcoming routes. Cannot add duplicate or invalid route."
        )
    
    # Get current route_progress
    route_progress_value = getattr(game_file, 'route_progress', None)
    route_progress = list(route_progress_value) if route_progress_value is not None else []
    
    # Add route (it's already validated to be in upcoming_routes, so it won't be a duplicate)
    route_progress.append(route)
    setattr(game_file, 'route_progress', route_progress)
    db.commit()
    db.refresh(game_file)
    
    return {"message": f"Route '{route}' added to progress", "route_progress": route_progress}



# used in unision with add_route
# TODO: function should work in unision from add_route
# ex if a user adds a route with pokemon, then they'll have the option to add pokemon from route
# if we want to check route_progress do we assume route has already been added or that it hasnt?
# OR does adding a pokemon from route also adds the route
@router.post("/game-files/{game_file_id}/route-pokemon/{route_name}", status_code=201)
async def add_pokemon_from_route(
    game_file_id: int,
    route_name: str,
    pokemon: PokemonCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a pokemon that was encountered on a specific route.
    Validates that the pokemon exists in that route's encounter data,
    then delegates creation to the pokemon router logic.
    """
    # Verify game file belongs to user
    game_file = verify_game_file(game_file_id, user, db)

    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found for this game.",
        )

    # Look up route by id
    route = (
        db.query(models.Route)
        .filter(models.Route.name == route_name.lower(), models.Route.version_id == version.version_id)
        .first()
    )

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found for this game.",
        )

    # Look up full pokemon data
    full_data_pokemon = (
        db.query(models.AllPokemon)
        .filter(models.AllPokemon.poke_id == pokemon.poke_id)
        .first()
    )

    if full_data_pokemon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error finding pokemon details! Ensure poke_id is accurate.",
        )

    # Ensure this pokemon can actually be encountered on this route
    # route.data entries look like: [pokemon_name, min_level, max_level, region, ...]
    route_data_value = getattr(route, "data", None)
    encounter_names = {enc[0] for enc in (route_data_value or [])}
    if full_data_pokemon.name not in encounter_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pokemon '{full_data_pokemon.name}' is not an encounter on this route.",
        )

    # Delegate creation to pokemon router logic
    return add_pokemon_to_game(game_file_id, pokemon, db)