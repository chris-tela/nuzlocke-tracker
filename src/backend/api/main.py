"""
Main FastAPI application for Nuzlocke Tracker API.
Separate from populate.py and cli.py - this is the web API layer.
"""
import os
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers (package-relative imports)
from .routers import auth, users, game_files, pokemon, routes, gyms, versions, trainers

app = FastAPI(
    title="Nuzlocke Tracker API",
    description="API for Pokemon Nuzlocke Tracker application",
    version="1.0.0",
)

# Request logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        full_path = f"{path}?{query_params}" if query_params else path
        
        print(f"[REQUEST] {method} {full_path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        status_code = response.status_code
        status_emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
        print(f"[RESPONSE] {status_emoji} {method} {full_path} - {status_code} ({process_time:.3f}s)")
        
        return response

# Add logging middleware (before CORS so it logs all requests)
app.add_middleware(LoggingMiddleware)

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


# Mount static files for assets (sprites, etc.)
# Get the backend directory path (parent of api directory)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_path = os.path.join(backend_dir, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

data_sprites_path = os.path.join(os.path.dirname(backend_dir), "data", "sprites")
if os.path.exists(data_sprites_path):
    app.mount("/data-sprites", StaticFiles(directory=data_sprites_path), name="data-sprites")

data_badges_path = os.path.join(os.path.dirname(backend_dir), "data", "badges")
if os.path.exists(data_badges_path):
    app.mount("/data-badges", StaticFiles(directory=data_badges_path), name="data-badges")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(game_files.router, prefix="/api/game-files", tags=["game-files"])
app.include_router(pokemon.router, prefix="/api/pokemon", tags=["pokemon"])
app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
app.include_router(gyms.router, prefix="/api/gyms", tags=["gyms"])
app.include_router(versions.router, prefix="/api/versions", tags=["versions"])
app.include_router(trainers.router, prefix="/api/trainers", tags=["trainers"])

