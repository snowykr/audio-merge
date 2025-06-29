"""
Celery 애플리케이션 인스턴스

순환 import를 방지하기 위해 Celery 인스턴스를 별도 모듈로 분리합니다.
"""

from celery import Celery
from .config import settings


def create_celery() -> Celery:
    """Celery 애플리케이션 인스턴스를 생성합니다."""
    celery_app = Celery(
        "audio_merge_worker",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["api.services.task_service"],
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


# Global Celery instance
celery = create_celery() 