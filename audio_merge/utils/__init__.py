"""
오디오 병합 프로그램 공통 유틸리티 패키지

이 패키지는 프로젝트 전반에서 사용되는 공통 기능들을 제공합니다:
- 예외 클래스들 (exceptions.py)
- WAV 파일 처리 유틸리티 (wav_utils.py)  
- 공통 유틸리티 함수들 (common.py)
"""

from .exceptions import (
    AudioMergeError,
    ValidationError,
    ConversionError,
    ConcatenationError,
    ChunkOverflowError,
    WriteError,
)

from .wav_utils import (
    WaveFormat,
    ChunkInfo,
    parse_wave_format,
    find_chunk_position,
    extract_wave_header,
    get_chunks_info,
    validate_wav_structure,
)

from .common import (
    validate_file_path,
    validate_output_path,
    format_file_size,
    format_duration,
    get_logger,
    safe_file_operation,
    calculate_audio_duration,
    calculate_data_size,
    cleanup_temp_files,
    ensure_directory,
)

__all__ = [
    # 예외 클래스
    "AudioMergeError",
    "ValidationError", 
    "ConversionError",
    "ConcatenationError",
    "ChunkOverflowError",
    "WriteError",
    
    # WAV 유틸리티
    "WaveFormat",
    "ChunkInfo",
    "parse_wave_format",
    "find_chunk_position",
    "extract_wave_header",
    "get_chunks_info",
    "validate_wav_structure",
    
    # 공통 유틸리티
    "validate_file_path",
    "validate_output_path",
    "format_file_size",
    "format_duration",
    "get_logger",
    "safe_file_operation",
    "calculate_audio_duration",
    "calculate_data_size",
    "cleanup_temp_files",
    "ensure_directory",
]