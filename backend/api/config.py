from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # FastAPI Configuration
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "Audio Merge Web UI"
    description: str = "Python Audio Merge Tool Web Interface"
    version: str = "1.0.0"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # File Upload Settings
    max_file_size: int = 500 * 1024 * 1024  # 500MB per file
    max_total_size: int = 2 * 1024 * 1024 * 1024  # 2GB total
    max_files_count: int = 20
    upload_dir: str = "/tmp/audio_merge"
    
    # Security Settings
    secret_key: str = "dev-secret-key"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Task Settings
    max_concurrent_tasks: int = 5
    task_time_limit: int = 1800  # 30 minutes
    task_soft_time_limit: int = 1500  # 25 minutes
    disk_usage_threshold: float = 0.95
    # 디스크 절대 여유 공간 하한 (GB)
    min_free_space_gb: int = 10
    
    # File Settings
    allowed_extensions: set = {'.wav', '.mp3'}
    allowed_mime_types: set = {'audio/wav', 'audio/x-wav', 'audio/mpeg'}
    
    class Config:
        env_prefix = "FASTAPI_"
        env_file = ".env"


settings = Settings()
