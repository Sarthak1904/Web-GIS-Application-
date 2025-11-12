"""Enterprise Geospatial Intelligence Platform — FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from app.api.v1 import auth, datasets, features, process, upload, admin
from app.core.database import engine, Base
from app.models import User, Role, Dataset, DatasetVersion, Feature, ProcessingJob, AuditLog

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    yield
    # Cleanup if needed


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade geospatial data platform for government and utility GIS",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health and metrics
@app.get("/health")
def health():
    """Health check for load balancers and orchestration."""
    return {"status": "healthy", "service": "geospatial-api"}


@app.get("/metrics-ready")
def metrics_ready():
    """Kubernetes-style readiness probe. Extend with DB/Redis checks."""
    return {"ready": True}


# API v1 routes
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(datasets.router, prefix=settings.api_v1_prefix)
app.include_router(features.router, prefix=settings.api_v1_prefix)
app.include_router(process.router, prefix=settings.api_v1_prefix)
app.include_router(upload.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
