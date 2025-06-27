"""
WAV 파일 처리 공통 유틸리티

이 모듈은 WAV 파일의 헤더 파싱, chunk 처리 등의 공통 기능을 제공합니다.
validator.py와 concatenator.py의 중복 로직을 통합합니다.
"""

import wave
import struct
from pathlib import Path
from typing import Union, Optional, NamedTuple, BinaryIO
from .exceptions import ValidationError, ConcatenationError


class WaveFormat(NamedTuple):
    """WAV 파일의 포맷 정보"""
    sample_rate: int
    channels: int
    sample_width: int  # 바이트 단위 (1=8bit, 2=16bit, 3=24bit, 4=32bit)
    frames: int
    duration: float  # 초 단위


class ChunkInfo(NamedTuple):
    """WAV chunk 정보"""
    chunk_id: bytes
    size: int
    position: int


def parse_wave_format(file_path: Union[str, Path]) -> WaveFormat:
    """
    WAV 파일의 fmt chunk를 파싱하여 포맷 정보를 추출합니다.
    
    Args:
        file_path: WAV 파일 경로
        
    Returns:
        WaveFormat 객체
        
    Raises:
        ValidationError: 유효하지 않은 WAV 파일
    """
    try:
        with wave.open(str(file_path), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frames = wav_file.getnframes()

            if sample_rate <= 0:
                raise ValidationError(f"잘못된 샘플레이트: {sample_rate}")
            if channels <= 0:
                raise ValidationError(f"잘못된 채널 수: {channels}")
            if sample_width <= 0:
                raise ValidationError(f"잘못된 샘플 폭: {sample_width}")

            duration = frames / sample_rate if sample_rate > 0 else 0.0

            return WaveFormat(
                sample_rate=sample_rate,
                channels=channels,
                sample_width=sample_width,
                frames=frames,
                duration=duration,
            )

    except wave.Error as e:
        raise ValidationError(f"WAV 파일 파싱 오류 ({file_path}): {e}")
    except Exception as e:
        raise ValidationError(f"파일 읽기 오류 ({file_path}): {e}")


def find_chunk_position(file_handle: BinaryIO, chunk_id: bytes) -> Optional[int]:
    """
    파일에서 특정 chunk의 위치를 찾습니다.
    
    Args:
        file_handle: 열린 파일 핸들
        chunk_id: 찾을 chunk ID (예: b"data", b"fmt ")
        
    Returns:
        chunk 시작 위치 또는 None
    """
    # RIFF 헤더 건너뛰기
    file_handle.seek(12)
    
    while True:
        chunk_header = file_handle.read(8)
        if len(chunk_header) < 8:
            return None
            
        current_chunk_id = chunk_header[:4]
        chunk_size = struct.unpack("<I", chunk_header[4:8])[0]
        
        if current_chunk_id == chunk_id:
            # chunk 시작 위치 반환 (chunk ID 위치)
            return file_handle.tell() - 8
            
        # 다른 chunk는 건너뛰기 (패딩 바이트 고려)
        skip_size = chunk_size + (chunk_size % 2)
        file_handle.seek(skip_size, 1)


def extract_wave_header(file_path: Union[str, Path]) -> tuple[bytes, int]:
    """
    WAV 파일에서 RIFF/fmt/data 헤더를 추출합니다.
    
    Args:
        file_path: WAV 파일 경로
        
    Returns:
        (헤더 바이트, data chunk 시작 위치)
        
    Raises:
        ConcatenationError: 헤더 추출 실패
    """
    # wave 모듈로 기본 정보 확인 (유효성 검증용)
    try:
        with wave.open(str(file_path), "rb") as wav_file:
            wav_file.getnframes()
            wav_file.getsampwidth() 
            wav_file.getnchannels()
            wav_file.getframerate()
    except wave.Error as e:
        raise ConcatenationError(f"유효하지 않은 WAV 파일: {file_path}")

    # 원본 파일에서 헤더 직접 추출
    with open(file_path, "rb") as f:
        # RIFF 헤더 확인
        riff_header = f.read(12)
        if (
            len(riff_header) != 12
            or riff_header[:4] != b"RIFF"
            or riff_header[8:12] != b"WAVE"
        ):
            raise ConcatenationError(f"유효하지 않은 WAV 파일: {file_path}")

        # fmt chunk와 data chunk 찾기
        fmt_chunk = None
        data_pos = None

        f.seek(12)  # RIFF 헤더 다음부터 시작
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break

            chunk_id = chunk_header[:4]
            chunk_size = struct.unpack("<I", chunk_header[4:8])[0]

            if chunk_id == b"fmt ":
                fmt_data = f.read(chunk_size)
                fmt_chunk = chunk_header + fmt_data
                # 패딩 바이트 처리 (홀수 크기인 경우)
                if chunk_size % 2:
                    f.read(1)

            elif chunk_id == b"data":
                data_pos = f.tell()
                break
            else:
                # 다른 chunk는 건너뛰기
                f.seek(chunk_size + (chunk_size % 2), 1)

        if not fmt_chunk or data_pos is None:
            raise ConcatenationError(
                f"fmt 또는 data chunk를 찾을 수 없습니다: {file_path}"
            )

        # 새로운 헤더 구성 (RIFF + fmt + data chunk header)
        # data chunk 크기는 나중에 업데이트됨
        data_header = b"data" + struct.pack("<I", 0)  # 크기는 임시로 0
        header = riff_header + fmt_chunk + data_header

        return header, data_pos


def get_chunks_info(file_path: Union[str, Path]) -> list[ChunkInfo]:
    """
    WAV 파일의 모든 chunk 정보를 반환합니다.
    
    Args:
        file_path: WAV 파일 경로
        
    Returns:
        ChunkInfo 객체들의 리스트
        
    Raises:
        ValidationError: 파일 읽기 오류
    """
    chunks = []
    
    try:
        with open(file_path, "rb") as f:
            # RIFF 헤더 건너뛰기
            f.seek(12)
            
            while True:
                chunk_start = f.tell()
                chunk_header = f.read(8)
                
                if len(chunk_header) < 8:
                    break
                    
                chunk_id = chunk_header[:4]
                chunk_size = struct.unpack("<I", chunk_header[4:8])[0]
                
                chunks.append(ChunkInfo(
                    chunk_id=chunk_id,
                    size=chunk_size,
                    position=chunk_start
                ))
                
                # 다음 chunk로 이동 (패딩 고려)
                skip_size = chunk_size + (chunk_size % 2)
                f.seek(skip_size, 1)
                
    except Exception as e:
        raise ValidationError(f"chunk 정보 읽기 실패 ({file_path}): {e}")
        
    return chunks


def validate_wav_structure(file_path: Union[str, Path]) -> bool:
    """
    WAV 파일의 기본 구조를 검증합니다.
    
    Args:
        file_path: 검증할 WAV 파일 경로
        
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(file_path, "rb") as f:
            # RIFF 헤더 확인
            riff_header = f.read(12)
            if (
                len(riff_header) != 12
                or riff_header[:4] != b"RIFF"
                or riff_header[8:12] != b"WAVE"
            ):
                return False
                
            # fmt와 data chunk 존재 확인
            has_fmt = find_chunk_position(f, b"fmt ") is not None
            has_data = find_chunk_position(f, b"data") is not None
            
            return has_fmt and has_data
            
    except Exception:
        return False