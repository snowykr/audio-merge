from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import redis.asyncio as redis
from celery import Celery

from .config import settings
from .api.routes import router as api_router


def create_celery() -> Celery:
    celery_app = Celery(
        "audio_merge_worker",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_time_limit=settings.task_time_limit,
        task_soft_time_limit=settings.task_soft_time_limit,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )
    
    return celery_app


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
    
    # Static files
    app.mount("/static", StaticFiles(directory="web/app/static"), name="static")
    
    # Templates
    templates = Jinja2Templates(directory="web/app/templates")
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Redis connection
    @app.on_event("startup")
    async def startup_event():
        app.state.redis = redis.from_url(settings.redis_url)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await app.state.redis.close()
    
    # Root route
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    return app


# Global instances
celery = create_celery()
app = create_app()
