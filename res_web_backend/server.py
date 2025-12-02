"""
Portfolio Backend API - FastAPI Application Entry Point

This server provides the backend for the "See if I'm fit for you!" feature,
streaming AI agent analysis of employer queries via Server-Sent Events (SSE).

Endpoints:
    GET  /health              - Health check endpoint
    POST /api/fit-check/stream - SSE streaming endpoint for AI fit analysis

Usage:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import fit_check

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.
    
    Handles initialization and cleanup of resources.
    """
    logger.info("Portfolio Backend API starting up...")
    logger.info(f"Log level: {log_level}")
    
    # Startup: Initialize any resources here (e.g., database connections, caches)
    yield
    
    # Shutdown: Clean up resources here
    logger.info("Portfolio Backend API shutting down...")


# Initialize FastAPI application
app = FastAPI(
    title="Portfolio Backend API",
    description=(
        "Backend API for the 'See if I'm fit for you!' feature. "
        "Provides AI-powered analysis of employer queries via SSE streaming."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
# Parse allowed origins from environment variable
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured for origins: {allowed_origins}")


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the health status of the API server.",
    response_description="Health status object",
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancer health probes.
    
    Returns:
        dict: Status information including server health.
    """
    return {
        "status": "healthy",
        "service": "portfolio-backend-api",
        "version": "1.0.0",
    }


# =============================================================================
# API Information Endpoint
# =============================================================================

@app.get(
    "/",
    tags=["Info"],
    summary="API information",
    description="Returns basic information about the API.",
)
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API name, version, and documentation links.
    """
    return {
        "name": "Portfolio Backend API",
        "version": "1.0.0",
        "description": "AI-powered fit analysis for employers",
        "docs": "/docs",
        "health": "/health",
    }


# =============================================================================
# Router Registration
# =============================================================================

# Register the fit_check router for SSE streaming endpoints
app.include_router(fit_check.router)

logger.info("Registered fit_check router at /api/fit-check")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level=log_level.lower(),
    )
