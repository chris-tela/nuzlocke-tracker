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


### 2.6 Gym Management API
# - Endpoints:
#   - `GET /api/game-files/{game_file_id}/gym-progress` – completed gyms.
#   - `GET /api/game-files/{game_file_id}/upcoming-gyms` – derive from trainer JSON and completed gyms.
#   - `POST /api/game-files/{game_file_id}/gym-progress` – mark next gym as completed (enforce linear order).
#   - `GET /api/versions/{version_name}/gyms` – list gyms (1–8).
#   - `GET /api/versions/{version_name}/gyms/{gym_number}` – full details (trainers, teams).
# - Reference CLI: `gym_encounters`, `display_gym_trainers`, `update_gym_progress`, `get_trainer_data_filename`.



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

    gyms = db.query(models.Gym).filter(
        models.Gym.game_name == game_file.game_name, 
        models.Gym.gym_number > total_gyms
    ).order_by(asc(models.Gym.gym_number)).all()
   
    # Convert gym models to dicts for the response
    upcoming_gyms = [
        {
            "gym_number": gym.gym_number,
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

    gym = db.query(models.Gym).filter(models.Gym.game_name == game_file.game_name, models.Gym.gym_number == gym_number).first()

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
    
    print("test")
    version = db.query(models.Version).filter(models.Version.version_name == version_name).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found!")
    
    gyms = db.query(models.Gym).filter(models.Gym.game_name == version_name).order_by(asc(models.Gym.gym_number)).all()

    return {"gyms": gyms}






