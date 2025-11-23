from fastapi import APIRouter
from app.api.v1.endpoints import game, comparison

api_router = APIRouter()
api_router.include_router(game.router, prefix="/game", tags=["game"])
api_router.include_router(comparison.router, prefix="/comparison", tags=["comparison"])