"""
Route/encounter management router.
Handles route progression and encounter data.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import PokemonCreate
from .. import schemas
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

@router.get("/game-files/{game_file_id}/derived-routes/{route_name}", status_code=200)
async def get_derived_routes(game_file_id: int, route_name: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all routes that are derived from a given route name (which is in locations_ordered)."""
    
    game_file = verify_game_file(game_file_id, user, db)
    
    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()
    
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")
    
    # Find all routes where derives_from matches the route_name (case-insensitive) and version_id matches
    derived_routes = (
        db.query(models.Route)
        .filter(
            func.lower(models.Route.derives_from) == route_name.lower(),
            models.Route.version_id == version.version_id
        )
        .all()
    )
    
    # Return just the route names
    route_names = [route.name for route in derived_routes]
    
    return {"derived_routes": route_names}

@router.get("/game-files/{game_file_id}/parent-route/{route_name}", status_code=200)
async def get_parent_route(game_file_id: int, route_name: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the parent route (from locations_ordered) for a derived route."""
    
    game_file = verify_game_file(game_file_id, user, db)
    
    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()
    
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")
    
    # Find the route by name (case-insensitive)
    route = (
        db.query(models.Route)
        .filter(
            func.lower(models.Route.name) == route_name.lower(),
            models.Route.version_id == version.version_id
        )
        .first()
    )
    
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found!")
    
    # If the route has a derives_from value, return it as the parent route
    derives_from_value = getattr(route, 'derives_from', None)
    if derives_from_value is not None and derives_from_value != "":
        # Check if the parent route is in locations_ordered
        locations_ordered_value = getattr(version, 'locations_ordered', None)
        locations_ordered = list(locations_ordered_value) if locations_ordered_value else []
        
        # Find the parent route in locations_ordered (case-insensitive)
        parent_route = next(
            (loc for loc in locations_ordered if loc.lower() == route.derives_from.lower()),
            None
        )
        
        if parent_route:
            return {"parent_route": parent_route, "is_derived": True}
    
    # If no route found or no derives_from, it's not a derived route
    return {"parent_route": None, "is_derived": False}

# confirm route has been 'complete'
@router.post("/game-files/{game_file_id}/route-progressed/{route}", status_code=201)
async def add_route(game_file_id: int, route: str, include_parent: bool = False, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a route to route_progress. If the route is a derived route and include_parent is True, also add the parent route."""
    
    game_file = verify_game_file(game_file_id, user, db)
    version = db.query(models.Version).filter(models.Version.version_name == game_file.game_name).first()
    
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")

    # Get current route_progress
    route_progress_value = getattr(game_file, 'route_progress', None)
    route_progress = list(route_progress_value) if route_progress_value is not None else []
    
    routes_to_add = []
    parent_route = None
    
    # Check if this is a derived route
    route_obj = (
        db.query(models.Route)
        .filter(
            func.lower(models.Route.name) == route.lower(),
            models.Route.version_id == version.version_id
        )
        .first()
    )
    
    derives_from_value = None
    if route_obj is not None:
        derives_from_value = getattr(route_obj, 'derives_from', None)
    
    if route_obj is not None and derives_from_value is not None and derives_from_value != "":
        # This is a derived route
        locations_ordered_value = getattr(version, 'locations_ordered', None)
        locations_ordered = list(locations_ordered_value) if locations_ordered_value else []
        
        # Find the parent route in locations_ordered (case-insensitive)
        parent_route = next(
            (loc for loc in locations_ordered if loc.lower() == derives_from_value.lower()),
            None
        )
        
        if include_parent and parent_route and parent_route not in route_progress:
            # Add parent route first
            routes_to_add.append(parent_route)
        
        # Add the derived route (it's validated to exist)
        if route not in route_progress:
            routes_to_add.append(route)
    else:
        # For regular routes, validate it's in upcoming_routes
        upcoming_routes = get_upcoming_routes_list(game_file, db)
        if route not in upcoming_routes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Route '{route}' is not in upcoming routes. Cannot add duplicate or invalid route."
            )
        if route not in route_progress:
            routes_to_add.append(route)
    
    # Add all routes (avoiding duplicates)
    for route_to_add in routes_to_add:
        if route_to_add not in route_progress:
            route_progress.append(route_to_add)
    
    setattr(game_file, 'route_progress', route_progress)
    db.commit()
    db.refresh(game_file)
    
    message = f"Route '{route}' added to progress"
    if include_parent and parent_route:
        message += f", and parent route '{parent_route}' added to progress"
    
    return {"message": message, "route_progress": route_progress}



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
    # route.data format: [[{"name": pokemon_name}, {"min_level": min_level}, {"max_level": max_level}, {"game_name": game_name}, {"region_name": region_name}, [encounter_details...]], ...]
    route_data_value = getattr(route, "data", None)
    encounter_names = {enc[0].get("name") for enc in (route_data_value or []) if enc and len(enc) > 0 and isinstance(enc[0], dict) and "name" in enc[0]}
    if full_data_pokemon.name not in encounter_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pokemon '{full_data_pokemon.name}' is not an encounter on this route.",
        )

    # Set caught_on to the route name
    # Create a new PokemonCreate with caught_on set to the route name
    route_name = str(route.name)  # Get the actual string value
    pokemon_with_route = schemas.PokemonCreate(
        poke_id=pokemon.poke_id,
        nickname=pokemon.nickname,
        nature=pokemon.nature,
        ability=pokemon.ability,
        level=pokemon.level,
        gender=pokemon.gender,
        status=pokemon.status,
        caught_on=route_name
    )
    
    # Delegate creation to pokemon router logic
    return add_pokemon_to_game(game_file_id, pokemon_with_route, db)