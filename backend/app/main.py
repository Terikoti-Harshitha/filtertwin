"""
FilterTwin FastAPI Application Entry Point.
Explainable Filter Diagnostics and Guided Maintenance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import settings
from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.models.entities import PurifierProfile, FilterProfile, SimulationRun
from app.api.routes import purifiers, simulations, diagnostics, evaluations, maintenance, models, health
from app.services.purifier_service import create_purifier
from app.services.simulation_service import create_and_run_simulation
from app.schemas.purifier import PurifierCreate
from app.schemas.simulation import SimulationCreate
from app.services.diagnostic_service import get_ml_models

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML models into memory
    get_ml_models()

    db = SessionLocal()
    try:
        count = db.query(PurifierProfile).count()
        if count == 0:
            default_purifier = create_purifier(
                db,
                PurifierCreate(
                    name="CoreCraft Aquaguard RO (Virtual)",
                    location="Kitchen Countertop",
                    initial_inlet_tds=550.0,
                    daily_consumption_l=18.0,
                    initial_flow_rate_lpm=2.1,
                    filter_capacity_l=5000.0,
                    nominal_lifetime_days=365.0,
                    degradation_type="linear",
                    degradation_speed=1.0,
                    sensor_noise=0.02,
                    sensor_drift=0.005,
                )
            )
            # Create initial 60-day baseline simulation
            create_and_run_simulation(
                db,
                default_purifier,
                SimulationCreate(
                    purifier_profile_id=default_purifier.id,
                    degradation_type="linear",
                    degradation_speed=1.0,
                    fault_type="none",
                    random_seed=42,
                    duration_days=60.0,
                )
            )
    finally:
        db.close()
    yield

app = FastAPI(
    title="FilterTwin API",
    description="Explainable Filter Diagnostics and Guided Maintenance for Virtual Water Purifiers",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health.router)
app.include_router(purifiers.router, prefix=settings.API_V1_STR)
app.include_router(simulations.router, prefix=settings.API_V1_STR)
app.include_router(diagnostics.router, prefix=settings.API_V1_STR)
app.include_router(evaluations.router, prefix=settings.API_V1_STR)
app.include_router(maintenance.router, prefix=settings.API_V1_STR)
app.include_router(models.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
