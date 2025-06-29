"""
Python Audio Merge - WAV 파일 병합 라이브러리

여러 개의 .wav 파일을 지정한 순서대로 이어 붙여 하나의 .wav 파일로 합치는 프로그램입니다.
무손실(PCM) 병합과 포맷 불일치 시 자동 변환 기능을 제공합니다.

패키지 구조:
- core: 핵심 오디오 처리 로직
- cli: 명령행 인터페이스 관련 기능
- utils: 공통 유틸리티 및 예외 클래스
"""

__version__ = "1.0.0"
__author__ = "Audio Merge Team"

from .core import WaveValidator, WaveConverter, WaveConcatenator, WaveWriter
from .utils import (
    AudioMergeError,
    ValidationError,
    ConversionError,
    ConcatenationError,
    ChunkOverflowError,
    WriteError,
    WaveFormat,
)

__all__ = [
    # Core classes
    "WaveValidator",
    "WaveConverter", 
    "WaveConcatenator",
    "WaveWriter",
    
    # Exceptions
    "AudioMergeError",
    "ValidationError",
    "ConversionError",
    "ConcatenationError", 
    "ChunkOverflowError",
    "WriteError",
    
    # Data types
    "WaveFormat",
]