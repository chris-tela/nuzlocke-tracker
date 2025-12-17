"""
Version/Generation router.
Handles public endpoints for game versions and generation data.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..utils import verify_game_file
from ...db import models
from ..dependencies import get_db

router = APIRouter()

# Version endpoints will be implemented in Phase 2.7
# @router.get("/versions")
# @router.get("/versions/{version_name}")
# @router.get("/generations/{generation_id}")
# @router.get("/versions/{version_name}/starters")

@router.get("/")
async def get_versions(db: Session = Depends(get_db)):

    return db.query(models.Version).all()

@router.get("/{version_name}")
async def get_version(version_name: str, db: Session = Depends(get_db)):
    
    version = db.query(models.Version).filter(models.Version.version_name == version_name).first()

    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="Version cannot be found!")
    
    return version

@router.get("/generations")
async def get_generations(db: Session = Depends(get_db)):
    return db.query(models.Generation).all()

@router.get("/generations/{generation_id}")
async def get_generation(generation_id: int, db: Session = Depends(get_db)):
    
    generation = db.query(models.Generation).filter(models.Generation.generation_id == generation_id).first()

    if generation is None:        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="Generation cannot be found!")
    
    return generation

@router.get("/generations/{generation_id}/starters")
async def get_starters(generation_id: int, db: Session = Depends(get_db)):
     
    generation = db.query(models.Generation).filter(models.Generation.generation_id == generation_id).first()

    if generation is None:        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail ="Generation cannot be found!")
    
    starters = []

    # outlier case
    if generation_id == 5:
        starters = generation.pokemon[1:4]
    else:
        starters = generation.pokemon[0:3]

    return starters
