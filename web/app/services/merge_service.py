import os
from typing import List, Dict, Callable, Optional, Union
from pathlib import Path
import shutil

# 올바른 import 방식으로 변경 (sys.path 조작 제거)
from audio_merge.core.validator import WaveValidator
from audio_merge.core.converter import WaveConverter
from audio_merge.core.concatenator import WaveConcatenator
from audio_merge.core.writer import WaveWriter
from audio_merge.utils.exceptions import AudioMergeError

from ..config import settings


class MergeService:
    """기존 audio_merge core 모듈을 웹 환경에 맞게 래핑하는 서비스 (중복 로직 제거)"""
    
    def __init__(self):
        self.validator = WaveValidator()
        self.writer = WaveWriter()
    
    async def merge_audio_files(
        self, 
        file_paths: List[str], 
        output_path: str,
        options: Dict,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        오디오 파일들을 병합합니다.
        기존 audio_merge core 모듈의 기능을 그대로 활용합니다.
        
        Args:
            file_paths: 병합할 오디오 파일 경로 리스트
            output_path: 출력 파일 경로
            options: 병합 옵션
            progress_callback: 진행률 콜백 함수
        
        Returns:
            병합 결과 정보
        """
        try:
            if progress_callback:
                await progress_callback(0, "파일 검증 시작", "파일들을 검증하고 있습니다...")
            
            # 1. 파일 검증 (기존 WaveValidator 사용)
            formats, stats = self.validator.validate_files(file_paths)
            
            if progress_callback:
                await progress_callback(20, "포맷 변환", "필요한 경우 파일 포맷을 변환하고 있습니다...")
            
            # 2. 필요시 포맷 변환 (기존 WaveConverter 사용)
            converted_files = file_paths
            if not stats["is_consistent"] and options.get("auto_convert", True):
                with WaveConverter(temp_dir=settings.upload_dir) as converter:
                    converted_files = converter.convert_files(file_paths, formats, stats)
                    converted_files = [str(path) for path in converted_files]
            
            if progress_callback:
                await progress_callback(50, "오디오 병합", "오디오 파일들을 병합하고 있습니다...")
            
            # 3. 오디오 파일 병합 (기존 WaveConcatenator 사용)
            concatenator = WaveConcatenator(buffer_size=options.get("buffer_size", 131072))
            data_size, duration = concatenator.concatenate_to_file(
                file_paths=[Path(f) for f in converted_files],
                output_path=output_path,
                fade_duration_ms=options.get("fade_duration_ms", 0)
            )
            
            if progress_callback:
                await progress_callback(90, "파일 최적화", "최종 파일을 최적화하고 있습니다...")
            
            # 4. 최종 파일 처리 (기존 WaveWriter 사용)
            file_info = self.writer.finalize_wav_file(output_path, data_size)
            
            if progress_callback:
                await progress_callback(100, "완료", "오디오 병합이 완료되었습니다.")
            
            return {
                "success": True,
                "output_path": output_path,
                "output_info": file_info,
                "input_files": len(file_paths),
                "duration": duration,
                "message": "오디오 병합이 성공적으로 완료되었습니다."
            }
            
        except AudioMergeError as e:
            return {
                "success": False,
                "error": type(e).__name__,
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "UnexpectedError",
                "message": f"예상치 못한 오류가 발생했습니다: {str(e)}"
            }
    
    def cleanup_temporary_files(self, task_id: str):
        """임시 파일들을 정리합니다."""
        temp_dirs = [
            os.path.join(settings.upload_dir, "converted", task_id),
            os.path.join(settings.upload_dir, "temp")
        ]
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"임시 파일 정리 오류: {e}")
    
    def estimate_processing_time(self, file_paths: List[str]) -> int:
        """처리 예상 시간을 추정합니다 (초 단위)."""
        total_size = sum(
            os.path.getsize(path) for path in file_paths 
            if os.path.exists(path)
        )
        
        # 대략적인 추정: 100MB당 30초
        estimated_seconds = (total_size / (100 * 1024 * 1024)) * 30
        
        return max(30, min(1800, int(estimated_seconds)))  # 최소 30초, 최대 30분
