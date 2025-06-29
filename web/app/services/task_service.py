import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, cast
from celery import Celery
import redis

from ..config import settings
from .merge_service import MergeService
from .file_service import FileService

# Celery 앱 생성
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

# Redis 클라이언트 (동기식)
redis_client = redis.from_url(settings.redis_url)
merge_service = MergeService()
file_service = FileService()


@celery_app.task(bind=True)
def start_merge_task(self, task_id: str, file_paths: List[str], options: Dict):
    """
    오디오 병합 작업을 시작합니다.
    이 함수는 Celery worker에서 실행됩니다.
    """
    
    async def progress_callback(progress: int, step: str, message: str):
        """진행률을 Redis에 업데이트합니다."""
        task_data = {
            "task_id": task_id,
            "celery_task_id": self.request.id,
            "status": "processing",
            "progress": progress,
            "current_step": step,
            "message": message,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Redis에 상태 업데이트
        redis_client.setex(
            f"task:{task_id}",
            86400,  # 24시간 TTL
            json.dumps(task_data)
        )
    
    try:
        # 출력 파일 경로 설정
        result_dir = os.path.join(settings.upload_dir, "results", task_id)
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, "merged_output.wav")
        
        # 비동기 병합 작업 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                merge_service.merge_audio_files(
                    file_paths=file_paths,
                    output_path=output_path,
                    options=options,
                    progress_callback=progress_callback
                )
            )
        finally:
            loop.close()
        
        if result["success"]:
            # 성공 상태 업데이트
            task_data = {
                "task_id": task_id,
                "celery_task_id": self.request.id,
                "status": "completed",
                "progress": 100,
                "current_step": "완료",
                "message": result["message"],
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "result": result
            }
        else:
            # 실패 상태 업데이트
            task_data = {
                "task_id": task_id,
                "celery_task_id": self.request.id,
                "status": "failed",
                "progress": 0,
                "current_step": "실패",
                "message": result["message"],
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "error": result.get("error", "Unknown")
            }
        
        # 최종 상태를 Redis에 저장
        redis_client.setex(
            f"task:{task_id}",
            86400,  # 24시간 TTL
            json.dumps(task_data)
        )
        
        # 임시 파일 정리
        merge_service.cleanup_temporary_files(task_id)
        
        return result
        
    except Exception as e:
        # 예외 발생 시 실패 상태 업데이트
        error_data = {
            "task_id": task_id,
            "celery_task_id": self.request.id,
            "status": "failed",
            "progress": 0,
            "current_step": "오류 발생",
            "message": f"작업 중 오류가 발생했습니다: {str(e)}",
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "error": "TaskExecutionError"
        }
        
        redis_client.setex(
            f"task:{task_id}",
            86400,
            json.dumps(error_data)
        )
        
        # 임시 파일 정리
        try:
            merge_service.cleanup_temporary_files(task_id)
        except Exception:
            pass
        
        raise


def get_task_status(task_id: str) -> Dict:
    """작업 상태를 조회합니다."""
    try:
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "작업을 찾을 수 없습니다."
            }
        
        return cast(Dict[str, Any], json.loads(task_data))
        
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "error",
            "message": f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        }


@celery_app.task
def cleanup_expired_files():
    """만료된 파일들을 정리하는 정기 작업입니다."""
    try:
        upload_base_dir = settings.upload_dir
        current_time = datetime.now()
        
        # 각 하위 디렉토리 검사
        for subdir_name in ['uploads', 'converted', 'results']:
            subdir_path = os.path.join(upload_base_dir, subdir_name)
            
            if not os.path.exists(subdir_path):
                continue
            
            for item_name in os.listdir(subdir_path):
                item_path = os.path.join(subdir_path, item_name)
                
                if not os.path.isdir(item_path):
                    continue
                
                # 디렉토리 생성 시간 확인
                created_time = datetime.fromtimestamp(os.path.getctime(item_path))
                age_hours = (current_time - created_time).total_seconds() / 3600
                
                # TTL 확인 및 삭제
                should_delete = False
                
                if subdir_name == 'uploads' and age_hours > 1:  # 1시간
                    should_delete = True
                elif subdir_name == 'converted' and age_hours > 1:  # 1시간
                    should_delete = True
                elif subdir_name == 'results' and age_hours > 24:  # 24시간
                    should_delete = True
                
                if should_delete:
                    try:
                        import shutil
                        shutil.rmtree(item_path)
                        print(f"만료된 디렉토리 삭제: {item_path}")
                    except Exception as e:
                        print(f"디렉토리 삭제 실패 {item_path}: {e}")
        
        return {"cleaned": True, "message": "만료된 파일 정리 완료"}
        
    except Exception as e:
        return {"cleaned": False, "message": f"정리 작업 실패: {str(e)}"}


@celery_app.task
def cleanup_redis_tasks():
    """만료된 Redis 작업 데이터를 정리합니다."""
    try:
        # TTL이 적용되어 있어서 자동으로 정리되지만, 
        # 필요시 수동으로 정리할 수 있는 함수
        
        pattern = "task:*"
        keys = redis_client.keys(pattern)
        
        cleaned_count = 0
        for key in keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    data = json.loads(task_data)
                    
                    # 완료된 지 24시간이 지난 작업들 삭제
                    if data.get("status") in ["completed", "failed"]:
                        completed_at = data.get("completed_at")
                        if completed_at:
                            completed_time = datetime.fromisoformat(completed_at)
                            age_hours = (datetime.now() - completed_time).total_seconds() / 3600
                            
                            if age_hours > 24:
                                redis_client.delete(key)
                                cleaned_count += 1
                                
            except Exception as e:
                print(f"Redis 키 정리 실패 {key}: {e}")
        
        return {
            "cleaned": True, 
            "message": f"{cleaned_count}개의 만료된 작업 데이터 정리 완료"
        }
        
    except Exception as e:
        return {"cleaned": False, "message": f"Redis 정리 작업 실패: {str(e)}"}


def get_system_stats() -> Dict:
    """시스템 통계 정보를 반환합니다."""
    try:
        import psutil
        
        # 디스크 사용량
        disk_usage = psutil.disk_usage(settings.upload_dir)
        
        # 메모리 사용량
        memory = psutil.virtual_memory()
        
        # Redis 작업 수 확인
        task_keys = redis_client.keys("task:*")
        active_tasks = 0
        pending_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        
        for key in task_keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    data = json.loads(task_data)
                    status = data.get("status")
                    
                    if status == "processing":
                        active_tasks += 1
                    elif status == "pending":
                        pending_tasks += 1
                    elif status == "completed":
                        completed_tasks += 1
                    elif status == "failed":
                        failed_tasks += 1
            except Exception:
                pass
        
        return {
            "disk_usage": {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": disk_usage.used / disk_usage.total * 100
            },
            "memory_usage": {
                "total": memory.total,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent
            },
            "task_stats": {
                "active": active_tasks,
                "pending": pending_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "total": len(task_keys)
            }
        }
        
    except Exception as e:
        return {"error": str(e)}
