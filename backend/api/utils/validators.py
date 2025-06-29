from typing import List, Tuple, Optional
from pathlib import Path

from ..config import settings


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """파일 확장자를 검증합니다."""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in settings.allowed_extensions:
        return False, f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.allowed_extensions)}"
    
    return True, "유효한 파일 확장자입니다."


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> Tuple[bool, str]:
    """파일 크기를 검증합니다."""
    max_size = max_size or settings.max_file_size
    
    if file_size > max_size:
        max_size_mb = max_size // (1024 * 1024)
        file_size_mb = file_size // (1024 * 1024)
        return False, f"파일 크기가 제한을 초과합니다. (최대: {max_size_mb}MB, 현재: {file_size_mb}MB)"
    
    return True, "유효한 파일 크기입니다."


def validate_total_file_size(file_sizes: List[int], max_total: Optional[int] = None) -> Tuple[bool, str]:
    """전체 파일 크기를 검증합니다."""
    max_total = max_total or settings.max_total_size
    total_size = sum(file_sizes)
    
    if total_size > max_total:
        max_total_gb = max_total // (1024 * 1024 * 1024)
        total_size_gb = total_size / (1024 * 1024 * 1024)
        return False, f"전체 파일 크기가 제한을 초과합니다. (최대: {max_total_gb}GB, 현재: {total_size_gb:.1f}GB)"
    
    return True, "유효한 전체 파일 크기입니다."


def validate_file_count(file_count: int, max_count: Optional[int] = None) -> Tuple[bool, str]:
    """파일 개수를 검증합니다."""
    max_count = max_count or settings.max_files_count
    
    if file_count > max_count:
        return False, f"파일 개수가 제한을 초과합니다. (최대: {max_count}개, 현재: {file_count}개)"
    
    if file_count < 2:
        return False, "병합하려면 최소 2개의 파일이 필요합니다."
    
    return True, "유효한 파일 개수입니다."


def validate_filename(filename: str) -> Tuple[bool, str]:
    """파일명을 검증합니다."""
    if not filename:
        return False, "파일명이 비어있습니다."
    
    # 위험한 문자 검사
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            return False, f"파일명에 사용할 수 없는 문자가 포함되어 있습니다: {char}"
    
    # 파일명 길이 검사
    if len(filename) > 255:
        return False, "파일명이 너무 깁니다. (최대 255자)"
    
    # 빈 확장자 검사
    if not Path(filename).suffix:
        return False, "파일 확장자가 없습니다."
    
    return True, "유효한 파일명입니다."


def validate_system_resources() -> Tuple[bool, List[str]]:
    """시스템 리소스를 검증합니다."""
    errors = []
    warnings = []
    
    try:
        import psutil
        
        # 디스크 공간 검사
        disk_usage = psutil.disk_usage(settings.upload_dir)
        usage_percent = disk_usage.used / disk_usage.total
        
        if usage_percent > settings.disk_usage_threshold:
            errors.append(f"디스크 사용률이 {usage_percent:.1%}로 임계값을 초과했습니다.")
        elif usage_percent > 0.7:  # 70% 이상이면 경고
            warnings.append(f"디스크 사용률이 {usage_percent:.1%}입니다.")
        
        # 메모리 사용량 검사
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            errors.append(f"메모리 사용률이 {memory.percent:.1f}%로 높습니다.")
        elif memory.percent > 70:
            warnings.append(f"메모리 사용률이 {memory.percent:.1f}%입니다.")
        
        return len(errors) == 0, errors + warnings
        
    except Exception as e:
        errors.append(f"시스템 리소스 확인 중 오류 발생: {str(e)}")
        return False, errors
