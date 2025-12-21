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

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from routers import fit_check
from routers import prompts
from routers import examples
from services.metrics import PROMETHEUS_AVAILABLE

if PROMETHEUS_AVAILABLE:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Load environment variables from .env file
load_dotenv()


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs log records as JSON objects for easy parsing by log aggregators
    (e.g., ELK Stack, CloudWatch Logs, Datadog).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (e.g., session_id)
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "phase"):
            log_data["phase"] = record.phase
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


def configure_logging(json_format: bool = False):
    """
    Configure application logging.
    
    Args:
        json_format: If True, use JSON format (for production).
                     If False, use human-readable format (for development).
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
    
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.INFO)
    
    return root_logger


# Call in module-level initialization
USE_JSON_LOGS = os.getenv("LOG_FORMAT", "text").lower() == "json"
logger = configure_logging(json_format=USE_JSON_LOGS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.
    
    Handles initialization and cleanup of resources.
    """
    logger.info("Portfolio Backend API starting up...")
    logger.info(f"Log level: {os.getenv('LOG_LEVEL', 'INFO').upper()}")
    logger.info(f"Log format: {'JSON' if USE_JSON_LOGS else 'Text'}")
    
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
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3003")
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


if PROMETHEUS_AVAILABLE:
    @app.get(
        "/metrics",
        tags=["Monitoring"],
        summary="Prometheus metrics",
        description="Exposes application metrics in Prometheus format.",
    )
    async def metrics():
        """Expose Prometheus metrics."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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

# Register the prompts router for transparency endpoints
app.include_router(prompts.router)
logger.info("Registered prompts router at /api/prompts")

# Register the examples router for demo example generation
app.include_router(examples.router)
logger.info("Registered examples router at /api/examples")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,  # Disable auto-reload for stability in this environment
        log_level=log_level.lower(),
    )
