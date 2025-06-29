import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from .config import settings
from .celery_app import celery
from .api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.title,
        description=settings.description,
        version=settings.version,
        debug=settings.debug,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Redis connection
    @app.on_event("startup")
    async def startup_event():
        app.state.redis = redis.from_url(settings.redis_url)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await app.state.redis.close()
    
    # Root route - API health check
    @app.get("/")
    async def root():
        return {
            "service": "Audio Merge API",
            "status": "ok",
            "frontend": "http://localhost:3000"
        }
    
    return app


# Global instances
app = create_app()
