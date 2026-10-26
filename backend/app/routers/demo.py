from fastapi import APIRouter
from app.seed_data import seed_demo_data
from app.database import reset_db
from app.config import settings

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.get("/status")
def get_demo_status():
    return {
        "demo_mode": settings.DEMO_MODE,
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "gemini_enabled": bool(settings.GEMINI_API_KEY),
        "gemini_mode": "Online Cloud API" if settings.GEMINI_API_KEY else "Offline Heuristic Deterministic Engine"
    }

@router.post("/seed")
def seed_data():
    res = seed_demo_data()
    return res

@router.post("/reset")
def reset_data():
    reset_db()
    res = seed_demo_data()
    return {"message": "Database reset and re-seeded with realistic baseline data", "details": res}
