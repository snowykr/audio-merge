"""WAV 파일 Writer 테스트"""

import pytest
import tempfile
import struct
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import BytesIO
from audio_merge.core import WaveWriter
from audio_merge.utils import WriteError


class TestWaveWriter:
    """WaveWriter 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.writer = WaveWriter()

    def test_init(self):
        """초기화 테스트"""
        writer = WaveWriter()
        assert hasattr(writer, "logger")

    def test_update_wave_header_file_not_exists(self):
        """존재하지 않는 파일 테스트"""
        with pytest.raises(WriteError) as exc_info:
            self.writer.update_wave_header("nonexistent.wav", 1000)
        assert "파일이 존재하지 않습니다" in str(exc_info.value)

    def test_update_wave_header_success(self):
        """헤더 업데이트 성공 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            # 유효한 WAV 헤더 작성
            temp_file.write(b"RIFF")
            temp_file.write(struct.pack("<I", 36))  # RIFF chunk 크기
            temp_file.write(b"WAVE")
            temp_file.write(b"fmt ")
            temp_file.write(struct.pack("<I", 16))  # fmt chunk 크기
            temp_file.write(b"\x01\x00\x02\x00")  # PCM, 2 channels
            temp_file.write(b"\x44\xac\x00\x00")  # 44100 Hz
            temp_file.write(b"\x10\xb1\x02\x00")  # byte rate
            temp_file.write(b"\x04\x00\x10\x00")  # block align, bits per sample
            temp_file.write(b"data")
            temp_file.write(struct.pack("<I", 0))  # data chunk 크기 (업데이트 대상)
            temp_file.write(b"X" * 1000)  # 더미 데이터
            
        try:
            # data chunk 위치 찾기를 위한 Mock
            with patch("audio_merge.core.writer.find_chunk_position") as mock_find:
                mock_find.return_value = 36  # data chunk 위치
                
                self.writer.update_wave_header(temp_path, 1000)
                
                # 파일 검증
                with open(temp_path, "rb") as f:
                    f.seek(4)
                    riff_size = struct.unpack("<I", f.read(4))[0]
                    f.seek(40)  # data chunk 크기 위치
                    data_size = struct.unpack("<I", f.read(4))[0]
                
                assert riff_size == temp_path.stat().st_size - 8
                assert data_size == 1000
                
        finally:
            temp_path.unlink()

    def test_update_wave_header_invalid_riff(self):
        """유효하지 않은 RIFF 헤더 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"XXXX")  # 잘못된 헤더
            
        try:
            with pytest.raises(WriteError) as exc_info:
                self.writer.update_wave_header(temp_path, 1000)
            assert "유효하지 않은 RIFF 헤더" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_update_wave_header_invalid_wave(self):
        """유효하지 않은 WAVE 헤더 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"RIFF")
            temp_file.write(struct.pack("<I", 36))
            temp_file.write(b"XXXX")  # WAVE가 아님
            
        try:
            with pytest.raises(WriteError) as exc_info:
                self.writer.update_wave_header(temp_path, 1000)
            assert "유효하지 않은 WAVE 헤더" in str(exc_info.value)
        finally:
            temp_path.unlink()

    def test_finalize_wav_file(self):
        """WAV 파일 완성 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            # 기본 WAV 구조 작성
            temp_file.write(b"RIFF" + b"\x00" * 48)
            
        try:
            with patch.object(self.writer, "update_wave_header") as mock_update:
                with patch.object(self.writer, "validate_wav_structure") as mock_validate:
                    mock_validate.return_value = {
                        "file_size": 52,
                        "data_chunk_size": 8
                    }
                    
                    result = self.writer.finalize_wav_file(temp_path, 1000)
                    
                    mock_update.assert_called_once_with(temp_path, 1000)
                    mock_validate.assert_called_once_with(temp_path)
                    
                    assert result["path"] == str(temp_path)
                    assert result["size_bytes"] == 52
                    assert result["data_size_bytes"] == 1000
                    assert result["validated"] is True
                    
        finally:
            temp_path.unlink()

    def test_finalize_wav_file_no_validation(self):
        """검증 없이 WAV 파일 완성 테스트"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"X" * 100)
            
        try:
            with patch.object(self.writer, "update_wave_header") as mock_update:
                result = self.writer.finalize_wav_file(temp_path, 50, validate=False)
                
                mock_update.assert_called_once_with(temp_path, 50)
                
                assert result["path"] == str(temp_path)
                assert result["size_bytes"] == 100
                assert result["data_size_bytes"] == 50
                assert result["validated"] is False
                
        finally:
            temp_path.unlink() 