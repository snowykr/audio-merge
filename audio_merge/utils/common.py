"""
공통 유틸리티 함수들

프로젝트 전반에서 사용되는 공통 기능들을 제공합니다:
- Path 처리 및 파일 검증
- 파일 크기 및 시간 포맷팅
- 로깅 유틸리티
"""

import logging
from pathlib import Path
from typing import Union, Optional
from .exceptions import ValidationError


def validate_file_path(file_path: Union[str, Path], check_wav: bool = True) -> Path:
    """
    파일 경로를 검증하고 Path 객체로 변환합니다.
    
    Args:
        file_path: 검증할 파일 경로
        check_wav: WAV 파일 확장자 검사 여부
        
    Returns:
        검증된 Path 객체
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않음
        ValueError: 유효하지 않은 파일
        PermissionError: 읽기 권한이 없음
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
        
    if not path.is_file():
        raise ValueError(f"디렉토리입니다. 파일을 지정해주세요: {path}")
        
    if check_wav and not path.suffix.lower() == ".wav":
        raise ValueError(f"WAV 파일이 아닙니다: {path}")
        
    # 읽기 권한 테스트
    try:
        with open(path, "rb") as f:
            f.read(1)
    except PermissionError:
        raise PermissionError(f"파일 읽기 권한이 없습니다: {path}")
        
    return path


def validate_output_path(file_path: Union[str, Path]) -> Path:
    """
    출력 파일 경로를 검증합니다.
    
    Args:
        file_path: 출력 파일 경로
        
    Returns:
        검증된 Path 객체
        
    Raises:
        PermissionError: 쓰기 권한이 없음
        ValueError: 유효하지 않은 경로
    """
    path = Path(file_path)
    
    # 부모 디렉토리 생성
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 쓰기 권한 테스트 (기존 파일이 있는 경우)
    if path.exists():
        try:
            with open(path, "r+b") as f:
                pass
        except PermissionError:
            raise PermissionError(f"파일 쓰기 권한이 없습니다: {path}")
    else:
        # 새 파일 생성 권한 테스트
        try:
            with open(path, "wb") as f:
                pass
            path.unlink()  # 테스트 파일 삭제
        except PermissionError:
            raise PermissionError(f"파일 생성 권한이 없습니다: {path}")
            
    return path


def format_file_size(size_bytes: int) -> str:
    """
    파일 크기를 사람이 읽기 쉬운 형태로 포맷팅합니다.
    
    Args:
        size_bytes: 바이트 단위 크기
        
    Returns:
        포맷팅된 크기 문자열
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_duration(seconds: float) -> str:
    """
    재생 시간을 사람이 읽기 쉬운 형태로 포맷팅합니다.
    
    Args:
        seconds: 초 단위 시간
        
    Returns:
        포맷팅된 시간 문자열
    """
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}분 {remaining_seconds:.1f}초"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}시간 {minutes}분 {remaining_seconds:.1f}초"


def get_logger(name: str = "audio_merge") -> logging.Logger:
    """
    기존에 설정된 로거를 가져옵니다.
    
    Args:
        name: 로거 이름
        
    Returns:
        로거 객체
    """
    return logging.getLogger(name)


def safe_file_operation(operation_name: str, file_path: Union[str, Path]):
    """
    파일 작업을 안전하게 수행하기 위한 컨텍스트 매니저 데코레이터입니다.
    
    Args:
        operation_name: 작업 이름 (로깅용)
        file_path: 대상 파일 경로
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _safe_operation():
        logger = get_logger()
        path = Path(file_path)
        
        logger.debug(f"{operation_name} 시작: {path.name}")
        
        try:
            yield path
            logger.debug(f"{operation_name} 완료: {path.name}")
        except Exception as e:
            logger.error(f"{operation_name} 실패 ({path.name}): {e}")
            raise
            
    return _safe_operation()


def calculate_audio_duration(frames: int, sample_rate: int) -> float:
    """
    오디오 프레임 수와 샘플레이트로부터 재생 시간을 계산합니다.
    
    Args:
        frames: 오디오 프레임 수
        sample_rate: 샘플레이트 (Hz)
        
    Returns:
        재생 시간 (초)
    """
    if sample_rate <= 0:
        return 0.0
    return frames / sample_rate


def calculate_data_size(frames: int, channels: int, sample_width: int) -> int:
    """
    오디오 데이터 크기를 계산합니다.
    
    Args:
        frames: 오디오 프레임 수
        channels: 채널 수
        sample_width: 샘플 폭 (바이트)
        
    Returns:
        데이터 크기 (바이트)
    """
    return frames * channels * sample_width


def cleanup_temp_files(temp_files: list[Path], logger: Optional[logging.Logger] = None):
    """
    임시 파일들을 정리합니다.
    
    Args:
        temp_files: 정리할 임시 파일 경로 리스트
        logger: 로거 객체 (None이면 기본 로거 사용)
    """
    if logger is None:
        logger = get_logger()
        
    for temp_file in temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"임시 파일 삭제: {temp_file}")
        except Exception as e:
            logger.warning(f"임시 파일 삭제 실패 ({temp_file}): {e}")
            
    temp_files.clear()


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    디렉토리가 존재하는지 확인하고 없으면 생성합니다.
    
    Args:
        dir_path: 디렉토리 경로
        
    Returns:
        Path 객체
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path