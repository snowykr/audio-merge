import os
import shutil
from typing import Dict, List

# 기존 audio_merge 모듈의 검증 기능 활용
from audio_merge.core.validator import WaveValidator
from audio_merge.utils.exceptions import ValidationError

from ..config import settings


class FileService:
    """웹 환경에 특화된 파일 관리 서비스 (중복 로직 제거, 기존 모듈 활용)"""
    
    def __init__(self):
        self.validator = WaveValidator()
    
    async def validate_file(self, file_path: str) -> Dict:
        """파일을 검증하고 상세 정보를 반환합니다. (기존 WaveValidator 활용)"""
        try:
            if not os.path.exists(file_path):
                return {
                    "is_valid": False,
                    "message": "파일이 존재하지 않습니다."
                }
            
            # 기존 WaveValidator를 사용하여 검증
            format_info = self.validator._parse_and_log_format(file_path)
            
            return {
                "is_valid": True,
                "message": "유효한 오디오 파일입니다.",
                "audio_info": {
                    "duration": format_info.duration,
                    "sample_rate": format_info.sample_rate,
                    "channels": format_info.channels,
                    "sample_width": format_info.sample_width,
                    "frames": format_info.frames
                }
            }
            
        except ValidationError as e:
            return {
                "is_valid": False,
                "message": str(e)
            }
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"파일 검증 중 오류가 발생했습니다: {str(e)}"
            }
    
    def cleanup_upload_directory(self, upload_id: str):
        """업로드 디렉토리를 정리합니다."""
        upload_dir = os.path.join(settings.upload_dir, "uploads", upload_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
    
    def cleanup_task_files(self, task_id: str):
        """작업 관련 모든 파일을 정리합니다."""
        # 변환된 파일들 정리
        converted_dir = os.path.join(settings.upload_dir, "converted", task_id)
        if os.path.exists(converted_dir):
            shutil.rmtree(converted_dir)
        
        # 결과 파일들 정리
        result_dir = os.path.join(settings.upload_dir, "results", task_id)
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
    
    def get_file_info_summary(self, file_paths: List[str]) -> Dict:
        """여러 파일의 정보를 요약합니다."""
        total_size = 0
        total_duration = 0
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
                
                # 기존 WaveValidator를 활용하여 duration 계산
                try:
                    format_info = self.validator._parse_and_log_format(file_path)
                    total_duration += format_info.duration
                except Exception:
                    pass
        
        return {
            "file_count": len(file_paths),
            "total_size": total_size,
            "total_duration": total_duration
        }
