"""
Gym management router.
Handles gym progression and trainer data.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import GymProgressResponse

from sqlalchemy import asc # ascending
router = APIRouter()


def get_trainer_data_filename(game_name: str) -> str:
    """
    Map game_name to the corresponding trainer_data JSON filename.
    Uses naming convention from scrape/trainer_data directory.
    """
    game_name_lower = game_name.lower()
    
    # Map game names to trainer_data filenames
    trainer_data_map = {
        'red': 'red-blue_trainers.json',
        'blue': 'red-blue_trainers.json',
        'yellow': 'yellow_trainers.json',
        'gold': 'gold-silver_trainers.json',
        'silver': 'gold-silver_trainers.json',
        'crystal': 'crystal_trainers.json',
        'ruby': 'ruby-sapphire_trainers.json',
        'sapphire': 'ruby-sapphire_trainers.json',
        'emerald': 'ruby-sapphire_trainers.json',  # Emerald uses same as Ruby/Sapphire
        'firered': 'firered-leafgreen_trainers.json',
        'leafgreen': 'firered-leafgreen_trainers.json',
        'diamond': 'diamond-pearl_trainers.json',
        'pearl': 'diamond-pearl_trainers.json',
        'platinum': 'platinum_trainers.json',
        'heartgold': 'heartgold-soulsilver_trainers.json',
        'soulsilver': 'heartgold-soulsilver_trainers.json',
        'black': 'black-white_trainers.json',
        'white': 'black-white_trainers.json',
        'black-2': 'black-white-2_trainers.json',
        'white-2': 'black-white-2_trainers.json',
    }
    
    return trainer_data_map.get(game_name_lower, f'{game_name_lower}_trainers.json')


def get_game_names_for_trainer_data(trainer_data_filename: str) -> list[str]:
    """
    Get all game names that use the same trainer_data file.
    """
    trainer_data_to_games = {
        'red-blue_trainers.json': ['red', 'blue'],
        'yellow_trainers.json': ['yellow'],
        'gold-silver_trainers.json': ['gold', 'silver'],
        'crystal_trainers.json': ['crystal'],
        'ruby-sapphire_trainers.json': ['ruby', 'sapphire', 'emerald'],
        'firered-leafgreen_trainers.json': ['firered', 'leafgreen'],
        'diamond-pearl_trainers.json': ['diamond', 'pearl'],
        'platinum_trainers.json': ['platinum'],
        'heartgold-soulsilver_trainers.json': ['heartgold', 'soulsilver'],
        'black-white_trainers.json': ['black', 'white'],
        'black-white-2_trainers.json': ['black-2', 'white-2'],
    }
    
    return trainer_data_to_games.get(trainer_data_filename, [])



@router.get("/game-files/{game_file_id}/gym-progress")
async def get_gym_progress(game_file_id: int, user: models.User = Depends(get_current_user),  db: Session = Depends(get_db)):
    
    game_file = verify_game_file(game_file_id, user, db)

    return {"Progress": game_file.gym_progress}

@router.get("/game-files/{game_file_id}/upcoming-gyms", response_model=GymProgressResponse)
async def get_upcoming_gyms(game_file_id: int, user: models.User = Depends(get_current_user),  db: Session = Depends(get_db)):
    
    game_file = verify_game_file(game_file_id, user, db)

    gym_progress_value = getattr(game_file, 'gym_progress', None)
    gym_progress = list(gym_progress_value) if gym_progress_value is not None else []
    total_gyms = len(gym_progress)

    # Get trainer_data filename for this game
    game_name_str = str(game_file.game_name)
    trainer_data_filename = get_trainer_data_filename(game_name_str)
    # Get all game names that share this trainer_data file
    shared_game_names = get_game_names_for_trainer_data(trainer_data_filename)
    
    # Query gyms for any of the game names that share the same trainer_data
    gyms = db.query(models.Gym).filter(
        models.Gym.game_name.in_(shared_game_names),
        models.Gym.gym_number > total_gyms
    ).order_by(asc(models.Gym.gym_number)).all()
   
    # Convert gym models to dicts for the response
    upcoming_gyms = [
        {
            "gym_number": gym.gym_number,
            "gym_path": gym.gym_path,
            "badge_path": gym.badge_path,
            "location": gym.location,
            "trainer_name": gym.trainer_name,
            "trainer_image": gym.trainer_image,
            "badge_name": gym.badge_name,
            "badge_type": gym.badge_type,
            "pokemon": gym.pokemon
        }
        for gym in gyms
    ]

    progress = {
        "gym_progress": gym_progress,
        "upcoming_gyms": upcoming_gyms
    }

    return GymProgressResponse.model_validate(progress)
    

@router.post("/game-files/{game_file_id}/add-gym/{gym_number}", status_code=201)
async def add_gym(game_file_id: int, gym_number: int, user: models.User = Depends(get_current_user),  db: Session = Depends(get_db)):

    game_file = verify_game_file(game_file_id, user, db)

    # get gyms completed
    gym_progress_value = getattr(game_file, 'gym_progress', None)
    gym_progress = list(gym_progress_value) if gym_progress_value is not None else []
    total_gyms = len(gym_progress)

    if total_gyms + 1 != gym_number:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Error: Must linerally complete gyms!")
    
    if total_gyms + 1 > 8:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only 8 gyms!")

    # Get trainer_data filename for this game
    game_name_str = str(game_file.game_name)
    trainer_data_filename = get_trainer_data_filename(game_name_str)
    # Get all game names that share this trainer_data file
    shared_game_names = get_game_names_for_trainer_data(trainer_data_filename)
    
    # Query gyms for any of the game names that share the same trainer_data
    gym = db.query(models.Gym).filter(
        models.Gym.game_name.in_(shared_game_names),
        models.Gym.gym_number == gym_number
    ).first()

    if gym is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gym details not found!")
    
    new_gym = {
        "gym_number": str(gym.gym_number),
        "location": str(gym.location),
        "badge_name": str(gym.badge_name)
    }

    gym_progress.append(new_gym)
    setattr(game_file, 'gym_progress', gym_progress)
    db.commit()
    db.refresh(game_file)

    return {"created": new_gym}

    



@router.get("/version/{version_name}/gyms")
async def get_version_gyms(version_name: str, db: Session = Depends(get_db)):
    
    version = db.query(models.Version).filter(models.Version.version_name == version_name).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")
    
    # Get trainer_data filename for this version
    trainer_data_filename = get_trainer_data_filename(version_name)
    # Get all game names that share this trainer_data file
    shared_game_names = get_game_names_for_trainer_data(trainer_data_filename)
    
    # Query gyms for any of the game names that share the same trainer_data
    gyms = db.query(models.Gym).filter(
        models.Gym.game_name.in_(shared_game_names)
    ).order_by(asc(models.Gym.gym_number)).all()

    return {"gyms": gyms}






