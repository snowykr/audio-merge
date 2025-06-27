import tempfile
from pathlib import Path
from typing import List, Union, Dict, Any, cast
from pydub import AudioSegment
from ..utils import (
    ConversionError,
    WaveFormat,
    get_logger,
    cleanup_temp_files,
)


class WaveConverter:
    """WAV 파일 포맷 변환 클래스"""
    
    # 비트 깊이별 FFmpeg 코덱 매핑
    BIT_DEPTH_CODECS = {
        8: "pcm_u8",
        16: "pcm_s16le",
        24: "pcm_s24le",
        32: "pcm_s32le",
    }

    def __init__(self, temp_dir: Union[str, Path, None] = None):
        """
        Args:
            temp_dir: 임시 파일 저장 디렉토리 (None이면 시스템 기본값 사용)
        """
        self.logger = get_logger()
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self.temp_files: List[Path] = []  # 정리용 임시 파일 목록

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """생성된 임시 파일들을 정리합니다."""
        cleanup_temp_files(self.temp_files, self.logger)

    def determine_target_format(
        self, formats: List[WaveFormat], stats: Dict[str, Any]
    ) -> WaveFormat:
        """
        변환 대상 포맷을 결정합니다.
        기본적으로 가장 높은 품질의 포맷을 선택합니다.

        Args:
            formats: 파일들의 포맷 정보
            stats: 포맷 통계 정보

        Returns:
            대상 포맷 정보
        """
        if stats["is_consistent"]:
            # 이미 일치하는 경우 기준 포맷 사용
            return WaveFormat(
                sample_rate=stats["reference_sample_rate"],
                channels=stats["reference_channels"],
                sample_width=stats["reference_sample_width"],
                frames=0,  # 변환 후 계산됨
                duration=0.0,  # 변환 후 계산됨
            )

        # 최고 품질 선택 전략
        max_sample_rate = max(stats["sample_rates"])
        max_channels = max(stats["channels"])
        max_sample_width = max(stats["sample_widths"])

        target_format = WaveFormat(
            sample_rate=max_sample_rate,
            channels=max_channels,
            sample_width=max_sample_width,
            frames=0,
            duration=0.0,
        )

        self.logger.info(
            f"변환 대상 포맷 결정: {max_sample_rate}Hz, {max_channels}ch, "
            f"{max_sample_width*8}bit"
        )

        return target_format

    def convert_file(
        self, input_path: Union[str, Path], target_format: WaveFormat
    ) -> Path:
        """
        단일 파일을 지정된 포맷으로 변환합니다.

        Args:
            input_path: 입력 파일 경로
            target_format: 변환할 대상 포맷

        Returns:
            변환된 파일의 경로

        Raises:
            ConversionError: 변환 실패
        """
        input_path = Path(input_path)

        try:
            # pydub로 오디오 로드
            audio = AudioSegment.from_wav(str(input_path))

            # 포맷 변환이 필요한지 확인
            needs_conversion = (
                audio.frame_rate != target_format.sample_rate
                or audio.channels != target_format.channels
                or audio.sample_width != target_format.sample_width
            )

            if not needs_conversion:
                self.logger.debug(f"변환 불필요: {input_path.name}")
                return input_path

            self.logger.info(
                f"파일 변환 시작: {input_path.name} "
                f"({audio.frame_rate}Hz, {audio.channels}ch, "
                f"{audio.sample_width*8}bit) → "
                f"({target_format.sample_rate}Hz, {target_format.channels}ch, "
                f"{target_format.sample_width*8}bit)"
            )

            # 포맷 변환
            converted_audio = audio

            # 샘플레이트 변환
            if audio.frame_rate != target_format.sample_rate:
                converted_audio = converted_audio.set_frame_rate(
                    target_format.sample_rate
                )

            # 채널 수 변환
            if audio.channels != target_format.channels:
                if target_format.channels == 1 and audio.channels > 1:
                    # 스테레오 → 모노: 다운믹스
                    converted_audio = converted_audio.set_channels(1)
                elif target_format.channels == 2 and audio.channels == 1:
                    # 모노 → 스테레오: 복제
                    converted_audio = converted_audio.set_channels(2)
                else:
                    # 기타 경우 (예: 5.1 → 스테레오)
                    converted_audio = converted_audio.set_channels(
                        target_format.channels
                    )

            # 비트 깊이 변환 체크
            if converted_audio.sample_width != target_format.sample_width:
                bit_depth = target_format.sample_width * 8
                if bit_depth not in self.BIT_DEPTH_CODECS:
                    raise ConversionError(f"지원하지 않는 비트 깊이: {bit_depth}bit")

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(
                suffix=f"_converted_{input_path.stem}.wav",
                dir=self.temp_dir,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                # WAV 내보내기 파라미터 설정
                export_params: Dict[str, Any] = {"format": "wav", "parameters": []}

                # 비트 깊이 설정
                bit_depth = target_format.sample_width * 8
                if bit_depth in self.BIT_DEPTH_CODECS:
                    codec = self.BIT_DEPTH_CODECS[bit_depth]
                    cast(list, export_params["parameters"]).extend(["-acodec", codec])

                # 파일 내보내기
                converted_audio.export(str(temp_path), **export_params)

                # 임시 파일 목록에 추가
                self.temp_files.append(temp_path)

                self.logger.debug(f"변환 완료: {temp_path}")
                return temp_path

        except Exception as e:
            error_msg = f"파일 변환 실패 ({input_path}): {e}"
            self.logger.error(error_msg)
            raise ConversionError(error_msg)

    def convert_files(
        self,
        file_paths: List[Union[str, Path]],
        formats: List[WaveFormat],
        stats: Dict[str, Any],
    ) -> List[Path]:
        """
        여러 파일을 일괄 변환합니다.

        Args:
            file_paths: 변환할 파일 경로 리스트
            formats: 각 파일의 포맷 정보
            stats: 포맷 통계 정보

        Returns:
            변환된 파일 경로 리스트 (변환이 필요없는 파일은 원본 경로)
        """
        if len(file_paths) != len(formats):
            raise ValueError("파일 경로와 포맷 정보의 개수가 일치하지 않습니다")

        if stats["is_consistent"]:
            self.logger.info("모든 파일 포맷이 일치하므로 변환을 건너뜁니다")
            return [Path(p) for p in file_paths]

        target_format = self.determine_target_format(formats, stats)
        converted_paths = []

        self.logger.info(f"{len(file_paths)}개 파일 변환 시작")

        for i, (file_path, format_info) in enumerate(zip(file_paths, formats), 1):
            self.logger.debug(
                f"파일 {i}/{len(file_paths)} 처리 중: "
                f"{Path(file_path).name}"
            )

            try:
                converted_path = self.convert_file(file_path, target_format)
                converted_paths.append(converted_path)
            except ConversionError:
                # 변환 실패 시 전체 작업 중단
                self.cleanup_temp_files()
                raise

        self.logger.info(f"변환 완료: {len(converted_paths)}개 파일")
        return converted_paths
