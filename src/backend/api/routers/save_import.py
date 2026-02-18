"""Save file import router.
Handles parsing .sav files and creating/updating game files from them.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from ...db import models
from ..dependencies import get_db, get_current_user
from ..schemas import (
    GameFileResponse,
    ParsedSavePreview,
    ParsedPokemonPreview,
    CreateFromSaveRequest,
    UpdateFromSaveRequest,
)
from ..save_import import parse_save_file
from ..utils import verify_game_file, to_game_file_response
from .gyms import get_trainer_data_filename, get_game_names_for_trainer_data

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB


@router.post("/parse-save", response_model=ParsedSavePreview)
async def parse_save(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    """Parse a .sav file and return a preview without writing to DB."""
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 1 MB.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty.",
        )

    try:
        preview = parse_save_file(contents)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse save file: {e}",
        )
    except Exception as e:
        logger.exception("Unexpected error parsing save file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse save file. Make sure it's a valid .sav from Pokemon Gen 1-5.",
        )

    return preview


@router.post("/create-from-save", response_model=GameFileResponse, status_code=status.HTTP_201_CREATED)
async def create_from_save(
    request: CreateFromSaveRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new game file from a parsed save preview."""
    preview = request.parsed_preview

    if request.game_name not in preview.compatible_versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Game name '{request.game_name}' is not compatible with this save file. "
                   f"Compatible versions: {preview.compatible_versions}",
        )

    gym_progress = _build_gym_progress(request.game_name, preview.badges, db)

    new_game_file = models.GameFiles(
        user_id=user.id,
        trainer_name=preview.trainer_name,
        game_name=request.game_name,
        starter_selected=None,
        gym_progress=gym_progress,
        route_progress=[],
    )
    db.add(new_game_file)
    db.flush()

    _create_pokemon_from_preview(new_game_file.id, preview.pokemon, db)

    db.commit()
    db.refresh(new_game_file)

    return to_game_file_response(new_game_file)


@router.put("/{game_file_id}/update-from-save", response_model=GameFileResponse)
async def update_from_save(
    game_file_id: int,
    request: UpdateFromSaveRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing game file's pokemon roster from a parsed save preview."""
    game_file = verify_game_file(game_file_id, user, db)
    preview = request.parsed_preview

    if game_file.game_name not in preview.compatible_versions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This save file is from {preview.game} but this game file is "
                   f"'{game_file.game_name}'. Upload a save from the correct game.",
        )

    db.query(models.OwnedPokemon).filter(
        models.OwnedPokemon.game_file_id == game_file_id
    ).delete()

    _create_pokemon_from_preview(game_file_id, preview.pokemon, db)

    gym_progress = _build_gym_progress(game_file.game_name, preview.badges, db)
    game_file.gym_progress = gym_progress

    db.commit()
    db.refresh(game_file)

    return to_game_file_response(game_file)


def _build_gym_progress(game_name: str, badges: list[str], db: Session) -> list[dict]:
    """Build gym_progress array by looking up badge names in the Gym table.

    Returns a list of {"gym_number": str, "location": str, "badge_name": str} dicts,
    ordered by gym_number. Badges not found in the Gym table are skipped.
    """
    if not badges:
        return []

    trainer_data_filename = get_trainer_data_filename(game_name)
    shared_game_names = get_game_names_for_trainer_data(trainer_data_filename)

    gym_progress = []
    for badge in badges:
        badge_full = f"{badge} Badge"
        gym = db.query(models.Gym).filter(
            models.Gym.game_name.in_(shared_game_names),
            models.Gym.badge_name == badge_full,
        ).first()

        if gym is None:
            logger.warning(f"Badge '{badge}' not found in Gym table for games {shared_game_names}")
            continue

        gym_progress.append({
            "gym_number": str(gym.gym_number),
            "location": str(gym.location),
            "badge_name": str(gym.badge_name),
        })

    # Sort by gym_number to ensure correct order
    gym_progress.sort(key=lambda g: int(g["gym_number"]))
    return gym_progress


def _create_pokemon_from_preview(
    game_file_id: int,
    pokemon_list: list[ParsedPokemonPreview],
    db: Session,
) -> None:
    """Create OwnedPokemon records from parsed pokemon preview data.

    Looks up types and evolution_data from AllPokemon table.
    Skips pokemon whose species_id is not found in the DB.
    """
    for pkmn_data in pokemon_list:
        poke_id = pkmn_data.poke_id
        name = pkmn_data.name
        nickname = pkmn_data.nickname
        nature_str = pkmn_data.nature
        ability = pkmn_data.ability
        level = pkmn_data.level
        status_str = pkmn_data.status
        caught_on = pkmn_data.caught_on

        base_pokemon = db.query(models.AllPokemon).filter(
            models.AllPokemon.poke_id == poke_id
        ).first()

        if base_pokemon is None:
            logger.warning(f"Skipping pokemon with poke_id={poke_id} ({name}): not found in AllPokemon table")
            continue

        nature_enum = None
        if nature_str:
            try:
                nature_enum = models.Nature(nature_str)
            except (ValueError, KeyError):
                nature_enum = None

        try:
            status_enum = models.Status(status_str)
        except (ValueError, KeyError):
            status_enum = models.Status.UNKNOWN

        owned = models.OwnedPokemon(
            game_file_id=game_file_id,
            poke_id=base_pokemon.poke_id,
            name=base_pokemon.name,
            nickname=nickname,
            nature=nature_enum,
            ability=ability,
            types=base_pokemon.types,
            level=level,
            gender=None,
            status=status_enum,
            caught_on=caught_on,
            evolution_data=base_pokemon.evolution_data,
        )
        db.add(owned)
