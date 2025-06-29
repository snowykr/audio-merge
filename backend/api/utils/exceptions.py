from fastapi import HTTPException, status
from typing import Dict, Any, Optional

# 올바른 import 방식으로 변경 (sys.path 조작 제거)
from audio_merge.utils.exceptions import (
    AudioMergeError, ValidationError, ConversionError, 
    ConcatenationError, WriteError
)


def map_audio_merge_error_to_http(error: AudioMergeError) -> HTTPException:
    """기존 AudioMergeError를 HTTP 예외로 매핑합니다."""
    
    error_mappings = {
        ValidationError: (
            status.HTTP_400_BAD_REQUEST,
            "입력 파일 검증 실패"
        ),
        ConversionError: (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "파일 변환 실패"
        ),
        ConcatenationError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "오디오 병합 실패"
        ),
        WriteError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "파일 저장 실패"
        )
    }
    
    error_type = type(error)
    if error_type in error_mappings:
        status_code, default_message = error_mappings[error_type]
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        default_message = "오디오 처리 중 오류가 발생했습니다"
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error_type.__name__,
            "message": str(error) or default_message,
            "type": "audio_merge_error"
        }
    )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = 500,
    detail: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """표준화된 에러 응답을 생성합니다."""
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error_type,
            "message": message,
            "detail": detail or {},
            "type": "api_error"
        }
    )


def handle_file_validation_error(filename: str, error_message: str) -> HTTPException:
    """파일 검증 오류를 처리합니다."""
    return create_error_response(
        error_type="FileValidationError",
        message=f"파일 검증 실패: {filename}",
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "filename": filename,
            "validation_error": error_message
        }
    )


def handle_task_timeout_error(task_id: str, timeout_seconds: int) -> HTTPException:
    """작업 타임아웃 오류를 처리합니다."""
    return create_error_response(
        error_type="TaskTimeoutError",
        message=f"작업이 {timeout_seconds}초 내에 완료되지 않았습니다",
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        detail={
            "task_id": task_id,
            "timeout_seconds": timeout_seconds
        }
    )


def handle_disk_space_error(required_space: int, available_space: int) -> HTTPException:
    """디스크 공간 부족 오류를 처리합니다."""
    return create_error_response(
        error_type="DiskSpaceError",
        message="디스크 공간이 부족합니다",
        status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
        detail={
            "required_space_mb": required_space // (1024 * 1024),
            "available_space_mb": available_space // (1024 * 1024)
        }
    )


def handle_memory_error(current_usage_percent: float) -> HTTPException:
    """메모리 부족 오류를 처리합니다."""
    return create_error_response(
        error_type="MemoryError",
        message=f"메모리 사용률이 {current_usage_percent:.1f}%로 높습니다",
        status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
        detail={
            "memory_usage_percent": current_usage_percent,
            "threshold_percent": 80.0
        }
    )


def handle_concurrent_task_limit_error(current_tasks: int, max_tasks: int) -> HTTPException:
    """동시 작업 수 제한 오류를 처리합니다."""
    return create_error_response(
        error_type="ConcurrentTaskLimitError",
        message=f"동시 처리 가능한 작업 수를 초과했습니다 ({current_tasks}/{max_tasks})",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "current_tasks": current_tasks,
            "max_tasks": max_tasks
        }
    )


def handle_redis_connection_error() -> HTTPException:
    """Redis 연결 오류를 처리합니다."""
    return create_error_response(
        error_type="RedisConnectionError",
        message="Redis 서버에 연결할 수 없습니다",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "service": "redis",
            "action": "잠시 후 다시 시도해주세요"
        }
    )


def handle_celery_error(error_message: str) -> HTTPException:
    """Celery 관련 오류를 처리합니다."""
    return create_error_response(
        error_type="CeleryError",
        message="백그라운드 작업 처리 중 오류가 발생했습니다",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "celery_error": error_message,
            "action": "잠시 후 다시 시도해주세요"
        }
    )
