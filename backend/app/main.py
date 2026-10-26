import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.seed_data import seed_demo_data
from app.routers import demo, requests, quotations, events, comparison, ranking, approvals

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    # If DEMO_MODE is enabled, automatically seed realistic baseline data
    if settings.DEMO_MODE:
        try:
            seed_demo_data()
            print("🚀 [ProcureSense] DEMO_MODE active: Seeded baseline procurement data.")
        except Exception as e:
            print(f"⚠️ [ProcureSense] Seed data initialization warning: {e}")
    yield

app = FastAPI(
    title="ProcureSense AI API",
    description="Deterministic Multi-Stage Procurement Prototype with What-If Sensitivity Ranking & Offline Heuristic Fallback",
    version=settings.VERSION,
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(demo.router)
app.include_router(requests.router)
app.include_router(quotations.router)
app.include_router(events.router)
app.include_router(comparison.router)
app.include_router(ranking.router)
app.include_router(approvals.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "database": "SQLite (Connected)",
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
