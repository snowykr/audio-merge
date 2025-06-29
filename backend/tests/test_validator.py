import pytest
import tempfile
import wave
from pathlib import Path

from audio_merge.core.validator import WaveValidator
from audio_merge.utils import WaveFormat, ValidationError


class TestWaveValidator:
    """WaveValidator 클래스 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.validator = WaveValidator()

    def create_test_wav(
        self, sample_rate=44100, channels=2, sample_width=2, duration=1.0
    ):
        """테스트용 WAV 파일 생성"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)

        # WAV 파일 생성
        with wave.open(str(temp_path), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)

            # 간단한 사인파 생성 (무음도 가능)
            frames = int(sample_rate * duration)
            audio_data = b"\x00" * (frames * channels * sample_width)
            wav_file.writeframes(audio_data)

        return temp_path

    def test_validate_file_access_valid(self):
        """유효한 파일 접근 테스트"""
        test_file = self.create_test_wav()
        try:
            result = self.validator.validate_file_access(test_file)
            assert result == test_file
        finally:
            test_file.unlink()

    def test_validate_file_access_not_found(self):
        """존재하지 않는 파일 테스트"""
        with pytest.raises(FileNotFoundError):
            self.validator.validate_file_access("nonexistent.wav")

    def test_validate_file_access_not_wav(self):
        """WAV가 아닌 파일 테스트"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)
            f.write(b"not a wav file")

        try:
            with pytest.raises(ValueError, match="WAV 파일이 아닙니다"):
                self.validator.validate_file_access(temp_path)
        finally:
            temp_path.unlink()

    def test_parse_wave_format_valid(self):
        """유효한 WAV 파일 파싱 테스트"""
        test_file = self.create_test_wav(
            sample_rate=48000, channels=1, sample_width=2, duration=2.0
        )
        try:
            format_info = self.validator.parse_wave_format(test_file)

            assert format_info.sample_rate == 48000
            assert format_info.channels == 1
            assert format_info.sample_width == 2
            assert format_info.duration == pytest.approx(2.0, rel=1e-3)
        finally:
            test_file.unlink()

    def test_parse_wave_format_invalid(self):
        """유효하지 않은 WAV 파일 파싱 테스트"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)
            f.write(b"fake wav data")

        try:
            with pytest.raises(ValidationError):
                self.validator.parse_wave_format(temp_path)
        finally:
            temp_path.unlink()

    def test_validate_format_consistency_same(self):
        """동일한 포맷 일치성 테스트"""
        format1 = WaveFormat(44100, 2, 2, 44100, 1.0)
        format2 = WaveFormat(44100, 2, 2, 44100, 1.0)

        stats = self.validator.validate_format_consistency(
            [format1, format2], ["file1.wav", "file2.wav"]
        )

        assert stats["is_consistent"] is True
        assert stats["reference_sample_rate"] == 44100
        assert stats["reference_channels"] == 2
        assert stats["reference_sample_width"] == 2

    def test_validate_format_consistency_different(self):
        """다른 포맷 불일치성 테스트"""
        format1 = WaveFormat(44100, 2, 2, 44100, 1.0)
        format2 = WaveFormat(48000, 1, 2, 48000, 1.0)  # 다른 샘플레이트, 채널

        stats = self.validator.validate_format_consistency(
            [format1, format2], ["file1.wav", "file2.wav"]
        )

        assert stats["is_consistent"] is False
        assert 44100 in stats["sample_rates"]
        assert 48000 in stats["sample_rates"]
        assert 1 in stats["channels"]
        assert 2 in stats["channels"]

    def test_validate_files_integration(self):
        """파일들 일괄 검증 통합 테스트"""
        # 같은 포맷의 테스트 파일 2개 생성
        test_file1 = self.create_test_wav(44100, 2, 2, 1.0)
        test_file2 = self.create_test_wav(44100, 2, 2, 2.0)

        try:
            formats, stats = self.validator.validate_files([test_file1, test_file2])

            assert len(formats) == 2
            assert stats["is_consistent"] is True
            assert stats["total_files"] == 2
            assert stats["total_duration"] == pytest.approx(3.0, rel=1e-3)
        finally:
            test_file1.unlink()
            test_file2.unlink()

    def test_validate_files_empty_list(self):
        """빈 파일 목록 테스트"""
        with pytest.raises(ValueError, match="검증할 파일이 없습니다"):
            self.validator.validate_files([])

    def test_wave_format_namedtuple(self):
        """WaveFormat NamedTuple 테스트"""
        format_info = WaveFormat(44100, 2, 2, 88200, 2.0)

        assert format_info.sample_rate == 44100
        assert format_info.channels == 2
        assert format_info.sample_width == 2
        assert format_info.frames == 88200
        assert format_info.duration == 2.0

        # NamedTuple의 불변성 테스트
        with pytest.raises(AttributeError):
            format_info.sample_rate = 48000
