from ..db import models
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .schemas import GameFileResponse


# helper functions

def verify_game_file(game_file_id: int, user: models.User, db: Session) -> models.GameFiles:

    game_file = db.query(models.GameFiles).filter(models.GameFiles.id == game_file_id).first()

    if game_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Game File not found!")

    if game_file.user_id is not user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Game File not associated with User!")

    return game_file


def to_game_file_response(game_file: models.GameFiles) -> GameFileResponse:
    """Map legacy DB column starter_selected to starter_pokemon response field."""
    response = GameFileResponse.model_validate(game_file)
    if response.starter_pokemon is None:
        response.starter_pokemon = game_file.starter_selected
    return response