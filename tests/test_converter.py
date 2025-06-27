"""
WAV 파일 변환기 테스트
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from audio_merge.core import WaveConverter
from audio_merge.utils import WaveFormat, ConversionError


class TestWaveConverter:
    """WaveConverter 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.converter = WaveConverter(temp_dir=self.temp_dir)

    def teardown_method(self):
        """각 테스트 후 정리"""
        self.converter.cleanup_temp_files()

    def test_init(self):
        """초기화 테스트"""
        # 기본 초기화
        converter = WaveConverter()
        assert converter.temp_dir is None
        assert converter.temp_files == []

        # 임시 디렉토리 지정
        converter = WaveConverter(temp_dir="/tmp/test")
        assert converter.temp_dir == Path("/tmp/test")

    def test_bit_depth_codecs(self):
        """비트 깊이 코덱 매핑 테스트"""
        assert WaveConverter.BIT_DEPTH_CODECS[8] == "pcm_u8"
        assert WaveConverter.BIT_DEPTH_CODECS[16] == "pcm_s16le"
        assert WaveConverter.BIT_DEPTH_CODECS[24] == "pcm_s24le"
        assert WaveConverter.BIT_DEPTH_CODECS[32] == "pcm_s32le"

    def test_context_manager(self):
        """컨텍스트 매니저 테스트"""
        with WaveConverter() as converter:
            assert isinstance(converter, WaveConverter)
        # __exit__ 후 temp_files가 정리되어야 함

    def test_determine_target_format_consistent(self):
        """일관된 포맷일 때 타겟 포맷 결정"""
        formats = [
            WaveFormat(44100, 2, 2, 1000, 0.02),
            WaveFormat(44100, 2, 2, 2000, 0.04),
        ]
        stats = {
            "is_consistent": True,
            "reference_sample_rate": 44100,
            "reference_channels": 2,
            "reference_sample_width": 2,
            "sample_rates": [44100],
            "channels": [2],
            "sample_widths": [2],
        }

        target = self.converter.determine_target_format(formats, stats)
        assert target.sample_rate == 44100
        assert target.channels == 2
        assert target.sample_width == 2

    def test_determine_target_format_inconsistent(self):
        """불일치 포맷일 때 최고 품질 선택"""
        formats = [
            WaveFormat(44100, 2, 2, 1000, 0.02),
            WaveFormat(48000, 1, 3, 2000, 0.04),
            WaveFormat(44100, 2, 4, 1500, 0.03),
        ]
        stats = {
            "is_consistent": False,
            "sample_rates": [44100, 48000],
            "channels": [1, 2],
            "sample_widths": [2, 3, 4],
        }

        target = self.converter.determine_target_format(formats, stats)
        assert target.sample_rate == 48000  # 최고 샘플레이트
        assert target.channels == 2  # 최대 채널
        assert target.sample_width == 4  # 최대 비트 깊이

    @patch("audio_merge.core.converter.AudioSegment")
    def test_convert_file_no_conversion_needed(self, mock_audio_segment):
        """변환이 필요 없는 경우"""
        # Mock 설정
        mock_audio = Mock()
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio.sample_width = 2
        mock_audio_segment.from_wav.return_value = mock_audio

        target_format = WaveFormat(44100, 2, 2, 0, 0.0)
        input_path = Path("test.wav")

        result = self.converter.convert_file(input_path, target_format)
        assert result == input_path

    @patch("audio_merge.core.converter.AudioSegment")
    @patch("tempfile.NamedTemporaryFile")
    def test_convert_file_sample_rate(self, mock_temp_file, mock_audio_segment):
        """샘플레이트 변환 테스트"""
        # Mock 설정
        mock_audio = Mock()
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio.sample_width = 2
        mock_audio.set_frame_rate = Mock(return_value=mock_audio)
        mock_audio.export = Mock()
        mock_audio_segment.from_wav.return_value = mock_audio

        # 임시 파일 Mock
        temp_file = MagicMock()
        temp_file.name = "/tmp/test_converted.wav"
        mock_temp_file.return_value.__enter__.return_value = temp_file

        target_format = WaveFormat(48000, 2, 2, 0, 0.0)
        input_path = Path("test.wav")

        result = self.converter.convert_file(input_path, target_format)
        
        # 검증
        mock_audio.set_frame_rate.assert_called_once_with(48000)
        assert result == Path("/tmp/test_converted.wav")
        assert Path("/tmp/test_converted.wav") in self.converter.temp_files

    def test_convert_file_unsupported_bit_depth(self):
        """지원하지 않는 비트 깊이 테스트"""
        with patch("audio_merge.core.converter.AudioSegment") as mock_audio_segment:
            mock_audio = Mock()
            mock_audio.frame_rate = 44100
            mock_audio.channels = 2
            mock_audio.sample_width = 2
            mock_audio_segment.from_wav.return_value = mock_audio

            # 지원하지 않는 비트 깊이 (5 * 8 = 40bit)
            target_format = WaveFormat(44100, 2, 5, 0, 0.0)
            input_path = Path("test.wav")

            with pytest.raises(ConversionError) as exc_info:
                self.converter.convert_file(input_path, target_format)
            assert "지원하지 않는 비트 깊이: 40bit" in str(exc_info.value)

    def test_convert_files(self):
        """여러 파일 일괄 변환 테스트"""
        file_paths = [Path("file1.wav"), Path("file2.wav")]
        formats = [
            WaveFormat(44100, 2, 2, 1000, 0.02),
            WaveFormat(48000, 2, 2, 2000, 0.04),
        ]
        stats = {
            "is_consistent": False,
            "sample_rates": [44100, 48000],
            "channels": [2],
            "sample_widths": [2],
        }

        with patch.object(self.converter, "convert_file") as mock_convert:
            mock_convert.side_effect = [Path("/tmp/file1_converted.wav"), Path("/tmp/file2_converted.wav")]
            
            results = self.converter.convert_files(file_paths, formats, stats)
            
            assert len(results) == 2
            assert mock_convert.call_count == 2

    def test_convert_files_consistent_formats(self):
        """포맷이 일치하는 경우 변환 건너뛰기"""
        file_paths = [Path("file1.wav"), Path("file2.wav")]
        formats = [
            WaveFormat(44100, 2, 2, 1000, 0.02),
            WaveFormat(44100, 2, 2, 2000, 0.04),
        ]
        stats = {"is_consistent": True}

        results = self.converter.convert_files(file_paths, formats, stats)
        assert results == file_paths  # 원본 경로 그대로 반환

    def test_cleanup_temp_files(self):
        """임시 파일 정리 테스트"""
        # 임시 파일 생성
        temp_file = Path(self.temp_dir) / "test_temp.wav"
        temp_file.touch()
        self.converter.temp_files.append(temp_file)

        # 정리
        self.converter.cleanup_temp_files()

        assert not temp_file.exists()
        assert len(self.converter.temp_files) == 0 