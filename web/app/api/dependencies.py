from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer
import redis.asyncio as redis
import psutil
import os
from typing import Dict, List, cast

from ..config import settings


security = HTTPBearer(auto_error=False)


async def get_redis(request: Request) -> redis.Redis:
    """Redis 클라이언트 인스턴스를 반환합니다."""
    return cast(redis.Redis, request.app.state.redis)


async def check_disk_space() -> bool:
    """디스크 공간을 확인하고 임계값을 초과하면 예외를 발생시킵니다."""
    # settings.upload_dir 경로를 기준으로 디스크 사용률을 계산합니다.
    # 업로드 경로가 존재하지 않을 수 있으므로, 사전에 디렉터리 생성이 필요합니다.
    ensure_upload_directory()
    disk_usage = psutil.disk_usage(settings.upload_dir)
    usage_percent = disk_usage.used / disk_usage.total
    
    if usage_percent > settings.disk_usage_threshold:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"디스크 사용률이 {usage_percent:.1%}로 임계값을 초과했습니다."
        )
    return True


async def check_memory_usage() -> bool:
    """메모리 사용량을 확인하고 임계값을 초과하면 예외를 발생시킵니다."""
    memory = psutil.virtual_memory()
    
    if memory.percent > 90:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"메모리 사용률이 {memory.percent:.1f}%로 높습니다."
        )
    return True


def ensure_upload_directory():
    """업로드 디렉토리가 존재하는지 확인하고 필요시 생성합니다."""
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    
    # 하위 디렉토리들도 생성
    for subdir in ['uploads', 'converted', 'results']:
        os.makedirs(os.path.join(upload_dir, subdir), exist_ok=True)


def validate_file_constraints(file_size: int, total_size: int, file_count: int):
    """파일 업로드 제약 조건을 검증합니다."""
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기가 {settings.max_file_size / (1024*1024):.0f}MB를 초과합니다."
        )
    
    if total_size > settings.max_total_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"전체 파일 크기가 {settings.max_total_size / (1024*1024*1024):.1f}GB를 초과합니다."
        )
    
    if file_count > settings.max_files_count:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 개수가 최대 {settings.max_files_count}개를 초과합니다."
        )


class RateLimiter:
    """간단한 rate limiter 구현"""
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        import time
        current_time = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 윈도우 밖의 요청들 제거
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # 현재 요청 추가
        self.requests[client_ip].append(current_time)
        
        return len(self.requests[client_ip]) <= self.max_requests


rate_limiter = RateLimiter()


def check_rate_limit(request: Request):
    """Rate limiting을 확인합니다."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
        )
