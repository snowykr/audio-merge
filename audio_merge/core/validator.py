from pathlib import Path
from typing import Dict, List, Union, Any
from ..utils import (
    ValidationError,
    WaveFormat,
    parse_wave_format,
    validate_file_path,
    get_logger,
)


class WaveValidator:
    """WAV 파일 검증 클래스"""

    def __init__(self):
        self.logger = get_logger()

    def validate_file_access(self, file_path: Union[str, Path]) -> Path:
        """
        파일 존재 여부와 읽기 권한을 검증합니다.

        Args:
            file_path: 검증할 파일 경로

        Returns:
            Path 객체

        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            PermissionError: 읽기 권한이 없음
        """
        return validate_file_path(file_path, check_wav=True)

    def _parse_and_log_format(self, file_path: Union[str, Path]) -> WaveFormat:
        """
        WAV 파일의 fmt chunk를 파싱하여 포맷 정보를 추출하고 로깅합니다.

        Args:
            file_path: WAV 파일 경로

        Returns:
            WaveFormat 객체

        Raises:
            ValidationError: 유효하지 않은 WAV 파일
        """
        path = self.validate_file_access(file_path)
        format_info = parse_wave_format(path)
        
        self.logger.debug(
            f"파일 포맷 파싱 완료 - {path.name}: "
            f"{format_info.sample_rate}Hz, {format_info.channels}ch, "
            f"{format_info.sample_width*8}bit, {format_info.duration:.2f}s"
        )
        
        return format_info

    def validate_format_consistency(
        self, formats: List[WaveFormat], file_paths: List[Union[str, Path]]
    ) -> Dict[str, Any]:
        """
        여러 WAV 파일들의 포맷 일치성을 검증합니다.

        Args:
            formats: 파일들의 포맷 정보 리스트
            file_paths: 파일 경로 리스트 (로깅용)

        Returns:
            포맷 통계 정보 딕셔너리

        Raises:
            ValueError: auto_convert가 False이고 포맷이 불일치할 때
        """
        if not formats:
            raise ValueError("검증할 포맷 정보가 없습니다")

        # 기준 포맷 (첫 번째 파일)
        reference = formats[0]

        # 포맷 일치성 검사
        sample_rates = set(f.sample_rate for f in formats)
        channels_set = set(f.channels for f in formats)
        sample_widths = set(f.sample_width for f in formats)

        is_consistent = (
            len(sample_rates) == 1
            and len(channels_set) == 1
            and len(sample_widths) == 1
        )

        # 통계 정보
        stats = {
            "is_consistent": is_consistent,
            "reference_sample_rate": reference.sample_rate,
            "reference_channels": reference.channels,
            "reference_sample_width": reference.sample_width,
            "total_files": len(formats),
            "total_duration": sum(f.duration for f in formats),
            "sample_rates": sorted(sample_rates),
            "channels": sorted(channels_set),
            "sample_widths": sorted(sample_widths),
        }

        if is_consistent:
            self.logger.info(
                f"모든 파일 포맷 일치: {reference.sample_rate}Hz, "
                f"{reference.channels}ch, {reference.sample_width*8}bit"
            )
        else:
            inconsistencies = []
            if len(sample_rates) > 1:
                inconsistencies.append(f"샘플레이트: {sorted(sample_rates)}")
            if len(channels_set) > 1:
                inconsistencies.append(f"채널: {sorted(channels_set)}")
            if len(sample_widths) > 1:
                bit_depths = [w * 8 for w in sorted(sample_widths)]
                inconsistencies.append(f"비트깊이: {bit_depths}")

            self.logger.warning(f"포맷 불일치 감지: {', '.join(inconsistencies)}")

            # 불일치 파일들 상세 로그
            for i, (fmt, path) in enumerate(zip(formats, file_paths)):
                self.logger.debug(
                    f"파일 {i+1}: {Path(path).name} - "
                    f"{fmt.sample_rate}Hz, {fmt.channels}ch, {fmt.sample_width*8}bit"
                )

        return stats

    def validate_files(
        self, file_paths: List[Union[str, Path]]
    ) -> tuple[List[WaveFormat], Dict[str, Any]]:
        """
        여러 WAV 파일들을 일괄 검증합니다.

        Args:
            file_paths: 검증할 파일 경로 리스트

        Returns:
            (포맷 정보 리스트, 포맷 통계 딕셔너리)
        """
        if not file_paths:
            raise ValueError("검증할 파일이 없습니다")

        self.logger.info(f"{len(file_paths)}개 파일 검증 시작")

        formats = []
        for i, file_path in enumerate(file_paths, 1):
            self.logger.debug(
                f"파일 {i}/{len(file_paths)} 검증 중: {Path(file_path).name}"
            )
            format_info = self._parse_and_log_format(file_path)
            formats.append(format_info)

        stats = self.validate_format_consistency(formats, file_paths)

        self.logger.info(
            f"검증 완료 - 총 {stats['total_files']}개 파일, "
            f"총 길이 {stats['total_duration']:.2f}초"
        )

        return formats, stats
