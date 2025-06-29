from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from typing import List
import uuid
import os
import json
import asyncio
from datetime import datetime
import redis.asyncio as redis

from .models import (
    UploadResponse, MergeRequest, TaskResponse, TaskStatus, 
    HealthResponse, CleanupResponse, FileInfo, UploadOptions
)
from .dependencies import (
    get_redis, check_disk_space, check_memory_usage, 
    ensure_upload_directory, validate_file_constraints, check_rate_limit
)
from ..services.file_service import FileService
from ..services.merge_service import MergeService
from ..services.task_service import start_merge_task
from ..config import settings


router = APIRouter()
file_service = FileService()
merge_service = MergeService()


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(check_rate_limit)])
async def upload_files(
    files: List[UploadFile] = File(...),
    options: str = Form(default="{}"),
    redis_client: redis.Redis = Depends(get_redis),
    _disk_check: bool = Depends(check_disk_space),
    _memory_check: bool = Depends(check_memory_usage)
):
    """파일을 업로드하고 검증합니다."""
    try:
        upload_options = UploadOptions.parse_raw(options)
    except Exception:
        upload_options = UploadOptions()
    
    ensure_upload_directory()
    
    # 1) 파일의 실제 크기를 계산하기 위해 먼저 내용을 읽어 둡니다.
    file_buffers = []  # (UploadFile, bytes, int) 튜플 목록
    for file in files:
        content = await file.read()
        size = len(content)
        file_buffers.append((file, content, size))

    # 2) 업로드 제약 조건 검증
    file_sizes = [buf[2] for buf in file_buffers]
    total_size = sum(file_sizes)
    max_size = max(file_sizes) if file_sizes else 0
    validate_file_constraints(max_size, total_size, len(file_buffers))

    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.upload_dir, "uploads", upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_infos = []
    validation_results = []

    # 3) 파일 저장 및 검증
    for file, content, size in file_buffers:
        if not file.filename:
            continue

        file_info = FileInfo(
            filename=file.filename,
            size=size,
            content_type=file.content_type or "",
            is_valid=False
        )

        try:
            # 파일 저장
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(content)

            # 파일 검증
            validation_result = await file_service.validate_file(file_path)
            file_info.is_valid = validation_result["is_valid"]
            file_info.validation_message = validation_result.get("message")

            if validation_result["is_valid"]:
                validation_results.append(f"✓ {file.filename}: 유효한 오디오 파일")
            else:
                validation_results.append(
                    f"✗ {file.filename}: {validation_result.get('message', '유효하지 않은 파일')}"
                )

        except Exception as e:
            file_info.validation_message = str(e)
            validation_results.append(f"✗ {file.filename}: 처리 중 오류 발생")

        file_infos.append(file_info)
    
    # Redis에 업로드 정보 저장 (1시간 TTL)
    upload_data = {
        "upload_id": upload_id,
        "files": [f.dict() for f in file_infos],
        "options": upload_options.dict(),
        "upload_dir": upload_dir,
        "created_at": datetime.now().isoformat()
    }
    
    await redis_client.setex(
        f"upload:{upload_id}",
        3600,  # 1시간 TTL
        json.dumps(upload_data)
    )
    
    return UploadResponse(
        upload_id=upload_id,
        files=file_infos,
        validation_results=validation_results
    )


@router.post("/merge", response_model=TaskResponse)
async def start_merge(
    request: MergeRequest,
    redis_client: redis.Redis = Depends(get_redis),
    _memory_check: bool = Depends(check_memory_usage)
):
    """오디오 파일 병합 작업을 시작합니다."""
    # 업로드 정보 조회
    upload_data = await redis_client.get(f"upload:{request.upload_id}")
    if not upload_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="업로드 정보를 찾을 수 없습니다."
        )
    
    upload_info = json.loads(upload_data)
    
    # 유효한 파일들만 필터링
    valid_files = [
        f for f in upload_info["files"] 
        if f["is_valid"]
    ]
    
    if len(valid_files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="병합하려면 최소 2개의 유효한 오디오 파일이 필요합니다."
        )
    
    # Celery 작업 시작
    task_id = str(uuid.uuid4())
    file_paths = [
        os.path.join(upload_info["upload_dir"], f["filename"])
        for f in valid_files
    ]
    
    # 작업 시작
    task = start_merge_task.delay(
        task_id=task_id,
        file_paths=file_paths,
        options=request.options.dict()
    )
    
    # 작업 상태를 Redis에 저장
    task_data = {
        "task_id": task_id,
        "celery_task_id": task.id,
        "status": "pending",
        "progress": 0,
        "current_step": "작업 대기 중",
        "message": "작업이 큐에 추가되었습니다.",
        "created_at": datetime.now().isoformat(),
        "upload_id": request.upload_id
    }
    
    await redis_client.setex(
        f"task:{task_id}",
        86400,  # 24시간 TTL
        json.dumps(task_data)
    )
    
    return TaskResponse(task_id=task_id, status="started")


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_status(
    task_id: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """작업 상태를 조회합니다."""
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업을 찾을 수 없습니다."
        )
    
    task_info = json.loads(task_data)
    
    return TaskStatus(
        task_id=task_info["task_id"],
        status=task_info["status"],
        progress=task_info["progress"],
        current_step=task_info["current_step"],
        message=task_info["message"],
        created_at=datetime.fromisoformat(task_info["created_at"]),
        completed_at=datetime.fromisoformat(task_info["completed_at"]) if task_info.get("completed_at") else None
    )


@router.get("/events/{task_id}")
async def get_events(
    task_id: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """Server-Sent Events로 실시간 진행률을 스트리밍합니다."""
    async def event_generator():
        last_status = None
        
        while True:
            try:
                task_data = await redis_client.get(f"task:{task_id}")
                if not task_data:
                    yield f"data: {json.dumps({'error': '작업을 찾을 수 없습니다.'})}\n\n"
                    break
                
                task_info = json.loads(task_data)
                current_status = task_info["status"]
                
                # 상태가 변경되었거나 진행 중인 경우에만 전송
                if current_status != last_status or current_status == "processing":
                    event_data = {
                        "progress": task_info["progress"],
                        "step": task_info["current_step"],
                        "message": task_info["message"],
                        "status": current_status,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_status = current_status
                
                # 완료 또는 실패 시 연결 종료
                if current_status in ["completed", "failed"]:
                    break
                
                await asyncio.sleep(1)  # 1초마다 확인
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/download/{task_id}")
async def download_result(
    task_id: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """병합된 결과 파일을 다운로드합니다."""
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업을 찾을 수 없습니다."
        )
    
    task_info = json.loads(task_data)
    
    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="작업이 아직 완료되지 않았습니다."
        )
    
    result_file = os.path.join(
        settings.upload_dir, "results", task_id, "merged_output.wav"
    )
    
    if not os.path.exists(result_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결과 파일을 찾을 수 없습니다."
        )
    
    return FileResponse(
        result_file,
        media_type="audio/wav",
        filename=f"merged_audio_{task_id[:8]}.wav"
    )


@router.delete("/cleanup/{task_id}", response_model=CleanupResponse)
async def cleanup_task(
    task_id: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """작업 관련 임시 파일들을 정리합니다."""
    try:
        # Redis에서 작업 정보 삭제
        await redis_client.delete(f"task:{task_id}")
        
        # 결과 파일 삭제
        result_dir = os.path.join(settings.upload_dir, "results", task_id)
        if os.path.exists(result_dir):
            import shutil
            shutil.rmtree(result_dir)
        
        return CleanupResponse(
            cleaned=True,
            message="임시 파일들이 성공적으로 정리되었습니다."
        )
        
    except Exception as e:
        return CleanupResponse(
            cleaned=False,
            message=f"정리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(redis_client: redis.Redis = Depends(get_redis)):
    """시스템 상태를 확인합니다."""
    try:
        # Redis 연결 확인
        await redis_client.ping()
        redis_status = "connected"
        
        # 큐 크기 확인 (간단한 구현)
        queue_size = 0  # 실제로는 Celery inspect를 사용해야 함
        active_tasks = 0
        
        return HealthResponse(
            status="ok",
            queue_size=queue_size,
            active_tasks=active_tasks,
            redis_status=redis_status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"서비스가 사용 불가능합니다: {str(e)}"
        )
