"""
Game file management router.
Handles game file CRUD operations.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import GameFileCreate, GameFileResponse, GameFileUpdate
from ..utils import to_game_file_response

router = APIRouter()

@router.post("", response_model=GameFileResponse, status_code=status.HTTP_201_CREATED)
async def create_game_file(
    gamefile: GameFileCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new game file for the current user."""
    # Validate trainer name
    trainer_name = gamefile.trainer_name.strip()
    if not trainer_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trainer name cannot be empty"
        )
    
    # Validate game name
    game_name = gamefile.game_name.strip()
    if not game_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game name cannot be empty"
        )
    
    # Create new game file
    new_game_file = models.GameFiles(
        user_id=user.id,
        trainer_name=trainer_name,
        game_name=game_name,
        starter_selected=gamefile.starter_pokemon,
        gym_progress=[],
        route_progress=[]
    )
    
    db.add(new_game_file)
    db.commit()
    db.refresh(new_game_file)
    
    return to_game_file_response(new_game_file)

# get list of game files for a given user
@router.get("", response_model = list[GameFileResponse], status_code = status.HTTP_200_OK)
async def get_game_files(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # get current users list of game files
    game_files = db.query(models.GameFiles).filter(models.GameFiles.user_id == user.id).all()

    if game_files is None:
        raise HTTPException(404, "No game files associated with user!")
    # return list of game files
    return [to_game_file_response(gf) for gf in game_files]

# get game file 
@router.get("/{game_file_id}", response_model = GameFileResponse, status_code = status.HTTP_200_OK)
async def get_game_file(game_file_id: int, user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()

    if game_file is None:
        raise HTTPException(404, "Game File ID not found!")

    if game_file.user_id is not user.id:
        raise HTTPException(403, "Game File ID not associated with User's account!")
    
    return to_game_file_response(game_file)
        

@router.put("/{game_file_id}", response_model=GameFileResponse, status_code=status.HTTP_200_OK)
async def update_game_file(
    game_file_id: int,
    update: GameFileUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a game file (trainer name, game name, or starter_pokemon)."""
    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()
    if game_file is None:
        raise HTTPException(status_code=404, detail="Game File Not Found!")
    if game_file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Game File not associated with user!")
    if update.trainer_name is not None:
        game_file.trainer_name = update.trainer_name.strip()
    if update.game_name is not None:
        game_file.game_name = update.game_name.strip()
    if update.starter_pokemon is not None:
        game_file.starter_selected = update.starter_pokemon.strip() or None
    db.commit()
    db.refresh(game_file)
    return to_game_file_response(game_file)


@router.delete("/{game_file_id}")
async def delete_game_file(game_file_id: int, user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    # make sure game file exists

    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()

    if game_file is None:
        raise HTTPException(status_code=404, detail="Game File Not Found!")
    
    if game_file.user_id is not user.id:
        raise HTTPException(status_code = 403, detail="File ID does not belong to user!")
    
    db.delete(game_file)
    db.commit()


    return status.HTTP_200_OK

