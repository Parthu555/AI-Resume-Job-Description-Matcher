import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .schemas.analysis import HealthResponse
from .routes.analyze import router as analyze_router
from .services.similarity_engine import (
    get_embedding_model,
    is_model_loaded,
    is_model_initializing,
    get_model_load_error,
    get_model_status
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.main")


import threading

def _warmup_model_worker():
    """Warm up embedding model in background thread."""
    try:
        model = get_embedding_model(settings.embedding_model_name, allow_blocking=True)
        if model is not None:
            logger.info("SentenceTransformer model successfully initialized in background.")
        else:
            logger.warning("Embedding model could not be loaded; TF-IDF fallback will be active.")
    except Exception as e:
        logger.warning(f"Embedding model background warmup encountered error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm embedding model asynchronously on startup."""
    logger.info("Initializing AI Resume Matcher backend services...")
    # Launch background thread for model resolution
    warmup_thread = threading.Thread(target=_warmup_model_worker, daemon=True)
    warmup_thread.start()
    yield
    logger.info("Shutting down AI Resume Matcher backend services...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Production-grade AI microservice for semantic resume & job description matching, skill gap discovery, and explainable recommendations.",
    lifespan=lifespan
)

# CORS configuration restricted to configured trusted frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include analysis routes
app.include_router(analyze_router)


@app.get("/", summary="Root Status", tags=["General"])
async def root_endpoint():
    """Returns basic service information and API status."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", response_model=HealthResponse, summary="Health Check", tags=["General"])
async def health_endpoint():
    """Returns service health, model readiness, and configuration parameters."""
    model_loaded = is_model_loaded()
    model_status = get_model_status()
    model_error = get_model_load_error()
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        model_status=model_status,
        model_name=settings.embedding_model_name,
        model_error=model_error,
        fallback_active=not model_loaded,
        supported_formats=["PDF (.pdf)", "Word (.docx)"]
    )
