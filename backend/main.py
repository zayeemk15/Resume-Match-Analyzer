"""
main.py — FastAPI application entry point
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging_config import setup_logging, get_logger
from backend.db.database import create_tables
from backend.api.routes import analyze, upload, rank, history

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    logger.info("Starting AI Resume Analyzer API", version=settings.version)
    await create_tables()
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Resume–JD Matching & Skill Gap Analyzer",
    description=(
        "An intelligent NLP system that computes match scores between resumes and "
        "job descriptions using TF-IDF, Sentence-BERT, and BERT. Provides ATS scores, "
        "skill gap analysis, and LLM-powered resume improvement suggestions."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(analyze.router)
app.include_router(upload.router)
app.include_router(rank.router)
app.include_router(history.router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": settings.version, "app": settings.app_name}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Resume Analyzer API is running 🚀",
        "docs":    "/docs",
        "version": settings.version,
    }


# ── Global exception handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )
