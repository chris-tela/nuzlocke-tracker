"""
Route/encounter management router.
Handles route progression and encounter data.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from h11 import Data
from sqlalchemy.orm import Session
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db, get_current_user


router = APIRouter()

### 2.5 Route / Encounter API
# - Endpoints:
#   - `GET /api/versions/{version_name}/routes` – ordered route list (from `Version.locations_ordered`).
#   - `GET /api/routes/{route_name}` – encounter data for a route (from `Route.data`).
#   - `GET /api/game-files/{game_file_id}/route-progress` – current route progression.
#   - `GET /api/game-files/{game_file_id}/upcoming-routes` – derive from version’s ordered list minus discovered routes.
#   - `POST /api/game-files/{game_file_id}/route-progress` – confirm/viewed/completed route (like `confirm_location_view`).
#   - `POST /api/game-files/{game_file_id}/catch-pokemon` – catch from route (tying into Pokemon endpoints).
# - Reference CLI functions: `encounters`, `find_route_progress`, `find_upcoming_locations`, `view_location`, `confirm_location_view`.

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
@router.get("/{route_}", status_code=200)
async def get_route_encounters(route_: str, db: Session = Depends(get_db)):
    """Get route encounters by route_id (integer) or route_name (string)."""
    
    # Try to parse as integer first (route_id)
    try:
        route_id = int(route_)
        route = db.query(models.Route).filter(models.Route.id == route_id).first()
    except ValueError:
        # If not a number, treat as route_name
        route = db.query(models.Route).filter(models.Route.name == route_.lower()).first()
    
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


#redirect route from add_pokemon
@router.post("/game-files/{game_file_id}/route-pokemon/{route}", status_code=201)
async def add_pokemon(game_file_id: int, route: str):
    # add pokemonCreate schema
    # if body is empty --> add route with no pokemon added
    # if body is filled --> identify pokemon to add by id
    # things like level min max & ability --> handled by frontend
    pass