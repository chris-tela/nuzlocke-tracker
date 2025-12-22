"""
Main FastAPI application for Nuzlocke Tracker API.
Separate from populate.py and cli.py - this is the web API layer.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers (package-relative imports)
from .routers import auth, users, game_files, pokemon, routes, gyms, versions

app = FastAPI(
    title="Nuzlocke Tracker API",
    description="API for Pokemon Nuzlocke Tracker application",
    version="1.0.0",
)

# CORS configuration for frontend communication
# Update allowed_origins in production to specific frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Nuzlocke Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount static files for assets (sprites, etc.)
# Get the backend directory path (parent of api directory)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_path = os.path.join(backend_dir, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(game_files.router, prefix="/api/game-files", tags=["game-files"])
app.include_router(pokemon.router, prefix="/api/pokemon", tags=["pokemon"])
app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
app.include_router(gyms.router, prefix="/api/gyms", tags=["gyms"])
app.include_router(versions.router, prefix="/api/versions", tags=["versions"])

