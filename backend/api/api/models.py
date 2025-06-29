from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class UploadOptions(BaseModel):
    auto_convert: bool = Field(default=True, description="포맷 불일치 시 자동 변환 여부")
    fade_duration_ms: int = Field(default=0, ge=0, le=5000, description="Cross-fade 길이 (ms)")
    buffer_size: int = Field(default=131072, description="버퍼 크기")
    output_format: str = Field(default="wav", description="출력 포맷")


class FileInfo(BaseModel):
    filename: str
    size: int
    content_type: str
    is_valid: bool
    validation_message: Optional[str] = None


class UploadResponse(BaseModel):
    upload_id: str
    files: List[FileInfo]
    validation_results: List[str]


class MergeRequest(BaseModel):
    upload_id: str
    options: UploadOptions = UploadOptions()


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = Field(ge=0, le=100, description="진행률 (0-100)")
    current_step: str
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str


class ProgressEvent(BaseModel):
    progress: int
    step: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    status: str = "ok"
    queue_size: int = 0
    active_tasks: int = 0
    redis_status: str = "connected"


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


class CleanupResponse(BaseModel):
    cleaned: bool
    message: str
