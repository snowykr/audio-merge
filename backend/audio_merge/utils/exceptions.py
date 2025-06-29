"""
오디오 병합 프로그램의 공통 예외 클래스들

모든 예외는 AudioMergeError를 기본 클래스로 하는 계층 구조를 가집니다.
"""


class AudioMergeError(Exception):
    """오디오 병합 프로그램의 기본 예외 클래스"""
    pass


class ValidationError(AudioMergeError):
    """파일 검증 관련 예외"""
    pass


class ConversionError(AudioMergeError):
    """파일 변환 관련 예외"""
    pass


class ConcatenationError(AudioMergeError):
    """파일 병합 관련 예외"""
    pass


class ChunkOverflowError(AudioMergeError):
    """WAV RIFF 4GB 크기 한계 초과 예외"""
    pass


class WriteError(AudioMergeError):
    """파일 쓰기 관련 예외"""
    pass