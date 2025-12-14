from ..db import models
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


# helper functions

def verify_game_file(game_file_id: int, user: models.User, db: Session) -> models.GameFiles:

    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()

    if game_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Game File not found!")
    
    if game_file.user_id is not user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Game File not associated with User!")
    
    return game_file