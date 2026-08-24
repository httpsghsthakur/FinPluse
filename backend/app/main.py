"""
FinPilot Backend — Main Application Entry Point

FastAPI application with lifespan management for database initialization.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.base import Base
from app.db.session import engine, async_session_factory
from app.api.v1.router import api_router

# Import all models so they are registered with the Base metadata
import app.db.models  # noqa: F401

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    setup_logging()
    logger.info("Finpluse backend starting up...")

    # Create tables & verify schema with graceful fallback
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Database table verification note: {e}")

    # Seed demo data if configured
    if settings.seed_demo_data:
        try:
            from app.api.v1.admin import seed_database
            async with async_session_factory() as session:
                try:
                    await seed_database(session)
                    await session.commit()
                    logger.info("Demo data seeded successfully")
                except Exception as e:
                    await session.rollback()
                    logger.warning(f"Demo seed note: {e}")
        except Exception as e:
            logger.warning(f"Seed skipped: {e}")

    logger.info(f"Finpluse backend ready — env={settings.app_env}")
    yield

    # Shutdown
    await engine.dispose()
    logger.info("Finpluse backend shut down.")


app = FastAPI(
    title="Finpluse — AI Financial Copilot API",
    description=(
        "Complete financial intelligence backend for Finpluse.\n\n"
        "Provides transaction management, ML-powered categorization, "
        "cash-flow forecasting, anomaly detection, what-if simulation, "
        "goal tracking, and an AI copilot with grounded financial reasoning."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — Support local dev, Render, and custom domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount API v1
app.include_router(api_router, prefix="/api/v1")

# Mount API v2
from app.api.v2.router import v2_router
app.include_router(v2_router, prefix="/api/v2")


@app.get("/health", tags=["Health"])
async def health():
    from app.db.session import engine
    db_url_str = str(engine.url)
    sanitized_url = db_url_str.replace("Ghsthakur%40123", "****")
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "connected", "url": sanitized_url}
    except Exception as e:
        import traceback
        return {"status": "degraded", "db_error": str(e), "url": sanitized_url, "traceback": traceback.format_exc()}


# ── Static SPA Hosting (Unified Frontend + Backend) ──────────────────────────
# Check for built frontend in root 'dist' or 'backend/dist'
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DIST_DIR = ROOT_DIR / "dist"
if not DIST_DIR.exists():
    DIST_DIR = Path(__file__).resolve().parent.parent / "dist"

if DIST_DIR.exists() and (DIST_DIR / "index.html").exists():
    # Mount /assets directory
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve SPA index.html for all client-side routes
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = DIST_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_DIR / "index.html"))
else:
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "app": "Finpluse AI Financial Copilot",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "message": "To serve frontend from this server, run 'npm run build' in project root",
        }

