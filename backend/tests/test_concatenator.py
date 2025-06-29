"""
WAV 파일 병합기 테스트
"""

import pytest
import tempfile
import struct
import wave
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import BytesIO
from audio_merge.core import WaveConcatenator
from audio_merge.utils import ChunkOverflowError, ConcatenationError


class TestWaveConcatenator:
    """WaveConcatenator 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.concatenator = WaveConcatenator(buffer_size=1024)  # 작은 버퍼로 테스트

    def test_init(self):
        """초기화 테스트"""
        # 기본 버퍼 크기
        concat = WaveConcatenator()
        assert concat.buffer_size == 65536
        assert concat.max_riff_size == 4294967295

        # 커스텀 버퍼 크기
        concat = WaveConcatenator(buffer_size=4096)
        assert concat.buffer_size == 4096

    @patch("audio_merge.core.concatenator.extract_wave_header")
    def test_stream_audio_data_simple(self, mock_extract_header):
        """단순 스트리밍 테스트"""
        # 테스트 데이터
        test_data = b"TEST_AUDIO_DATA" * 100
        data_size = len(test_data)
        
        # 파일 읽기 Mock
        mock_file = BytesIO()
        mock_file.write(struct.pack("<I", data_size))  # data chunk 크기
        mock_file.write(test_data)
        mock_file.seek(0)
        
        output_stream = BytesIO()
        
        with patch("builtins.open", return_value=mock_file):
            bytes_written = self.concatenator.stream_audio_data(
                "test.wav", 0, output_stream
            )
        
        assert bytes_written == data_size
        assert output_stream.getvalue() == test_data

    @patch("audio_merge.core.concatenator.AudioSegment")
    def test_stream_with_fade(self, mock_audio_segment):
        """페이드 효과 테스트"""
        # Mock 오디오
        mock_audio = Mock()
        mock_audio.raw_data = b"FADED_AUDIO_DATA"
        mock_audio.fade_in = Mock(return_value=mock_audio)
        mock_audio.fade_out = Mock(return_value=mock_audio)
        mock_audio_segment.from_wav.return_value = mock_audio
        
        output_stream = BytesIO()
        
        result = self.concatenator._stream_with_fade(
            "test.wav", 1000, output_stream, fade_in_ms=100, fade_out_ms=200
        )
        
        mock_audio.fade_in.assert_called_once_with(100)
        mock_audio.fade_out.assert_called_once_with(200)
        assert result == len(b"FADED_AUDIO_DATA")
        assert output_stream.getvalue() == b"FADED_AUDIO_DATA"

    def test_stream_audio_data_with_fade(self):
        """페이드 효과가 있는 스트리밍 테스트"""
        output_stream = BytesIO()
        
        with patch.object(self.concatenator, "_stream_with_fade") as mock_fade:
            mock_fade.return_value = 1000
            
            result = self.concatenator.stream_audio_data(
                "test.wav", 0, output_stream, fade_in_ms=50, fade_out_ms=50
            )
            
            mock_fade.assert_called_once()
            assert result == 1000

    @patch("wave.open")
    @patch("audio_merge.core.concatenator.extract_wave_header")
    def test_concatenate_files_single(self, mock_extract_header, mock_wave_open):
        """단일 파일 병합 테스트"""
        # Mock 설정
        mock_extract_header.return_value = (b"HEADER", 44)
        
        mock_wav = Mock()
        mock_wav.getframerate.return_value = 44100
        mock_wav.getnframes.return_value = 44100  # 1초
        mock_wave_open.return_value.__enter__.return_value = mock_wav
        
        output_stream = BytesIO()
        
        with patch.object(self.concatenator, "stream_audio_data") as mock_stream:
            mock_stream.return_value = 88200  # 44100 * 2 (16bit stereo)
            
            data_size, duration = self.concatenator.concatenate_files(
                [Path("test.wav")], output_stream
            )
        
        assert data_size == 88200
        assert duration == 1.0
        assert output_stream.getvalue().startswith(b"HEADER")

    @patch("wave.open") 
    @patch("audio_merge.core.concatenator.extract_wave_header")
    def test_concatenate_files_multiple(self, mock_extract_header, mock_wave_open):
        """여러 파일 병합 테스트"""
        # Mock 설정
        mock_extract_header.side_effect = [
            (b"HEADER", 44),
            (b"HEADER2", 44),
            (b"HEADER3", 44),
        ]
        
        mock_wav = Mock()
        mock_wav.getframerate.return_value = 44100
        mock_wav.getnframes.return_value = 44100  # 각 1초
        mock_wave_open.return_value.__enter__.return_value = mock_wav
        
        output_stream = BytesIO()
        
        with patch.object(self.concatenator, "stream_audio_data") as mock_stream:
            mock_stream.return_value = 88200  # 44100 * 2
            
            data_size, duration = self.concatenator.concatenate_files(
                [Path("test1.wav"), Path("test2.wav"), Path("test3.wav")],
                output_stream
            )
        
        assert data_size == 88200 * 3
        assert duration == 3.0
        assert mock_stream.call_count == 3

    def test_concatenate_files_empty_list(self):
        """빈 파일 리스트 테스트"""
        output_stream = BytesIO()
        
        with pytest.raises(ConcatenationError) as exc_info:
            self.concatenator.concatenate_files([], output_stream)
        assert "병합할 파일이 없습니다" in str(exc_info.value)

    @patch("wave.open")
    @patch("audio_merge.core.concatenator.extract_wave_header")  
    def test_concatenate_files_size_overflow(self, mock_extract_header, mock_wave_open):
        """4GB 크기 초과 테스트"""
        # Mock 설정
        mock_extract_header.side_effect = [(b"HEADER", 44), (b"HEADER2", 44)]
        
        mock_wav = Mock()
        mock_wav.getframerate.return_value = 44100
        mock_wav.getnframes.return_value = 44100
        mock_wave_open.return_value.__enter__.return_value = mock_wav
        
        output_stream = BytesIO()
        
        # 첫 번째 파일은 3GB, 두 번째 파일 처리 시 4GB 초과
        with patch.object(self.concatenator, "stream_audio_data") as mock_stream:
            mock_stream.side_effect = [3 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024]
            
            with pytest.raises(ChunkOverflowError) as exc_info:
                self.concatenator.concatenate_files(
                    [Path("big1.wav"), Path("big2.wav")], output_stream
                )
            assert "WAV RIFF 4GB 크기 한계 초과" in str(exc_info.value)

    @patch("wave.open")
    @patch("audio_merge.core.concatenator.extract_wave_header")
    def test_concatenate_files_with_fade(self, mock_extract_header, mock_wave_open):
        """Cross-fade 테스트"""
        # Mock 설정
        mock_extract_header.side_effect = [(b"HEADER", 44), (b"HEADER2", 44)]
        
        mock_wav = Mock()
        mock_wav.getframerate.return_value = 44100
        mock_wav.getnframes.return_value = 44100
        mock_wave_open.return_value.__enter__.return_value = mock_wav
        
        output_stream = BytesIO()
        
        with patch.object(self.concatenator, "stream_audio_data") as mock_stream:
            mock_stream.return_value = 88200
            
            data_size, duration = self.concatenator.concatenate_files(
                [Path("test1.wav"), Path("test2.wav")],
                output_stream,
                fade_duration_ms=500
            )
        
        # 페이드 효과 적용 확인
        assert mock_stream.call_count == 2
        # 첫 번째 파일: fade_out=500
        assert mock_stream.call_args_list[0][1]["fade_out_ms"] == 500
        assert mock_stream.call_args_list[0][1]["fade_in_ms"] == 0
        # 두 번째 파일: fade_in=500, fade_out=0
        assert mock_stream.call_args_list[1][1]["fade_in_ms"] == 500
        assert mock_stream.call_args_list[1][1]["fade_out_ms"] == 0
        
        # Cross-fade로 인한 시간 보정
        assert duration == pytest.approx(1.5, rel=1e-2)  # 2초 - 0.5초 overlap

    def test_concatenate_to_file(self):
        """파일로 저장 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.wav"
            
            with patch.object(self.concatenator, "concatenate_files") as mock_concat:
                mock_concat.return_value = (176400, 2.0)
                
                data_size, duration = self.concatenator.concatenate_to_file(
                    [Path("test1.wav"), Path("test2.wav")],
                    output_path,
                    fade_duration_ms=100
                )
            
            assert data_size == 176400
            assert duration == 2.0
            mock_concat.assert_called_once()

    def test_concatenate_to_file_error_cleanup(self):
        """에러 시 파일 정리 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.wav"
            
            with patch.object(self.concatenator, "concatenate_files") as mock_concat:
                mock_concat.side_effect = ConcatenationError("Test error")
                
                # 일부 데이터를 쓰고 실패하는 상황 시뮬레이션
                output_path.touch()
                
                with pytest.raises(ConcatenationError):
                    self.concatenator.concatenate_to_file(
                        [Path("test.wav")], output_path
                    )
                
                # 실패한 파일이 정리되었는지 확인
                assert not output_path.exists() 