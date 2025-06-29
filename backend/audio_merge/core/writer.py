import struct
from pathlib import Path
from typing import Union, List, Dict, Any, cast
from ..utils import (
    WriteError,
    find_chunk_position,
    get_logger,
)


class WaveWriter:
    """WAV 파일 헤더 재계산 및 완성 클래스"""

    def __init__(self):
        self.logger = get_logger()

    def update_wave_header(self, file_path: Union[str, Path], data_size: int) -> None:
        """
        WAV 파일의 RIFF 헤더와 data chunk 크기를 업데이트합니다.

        Args:
            file_path: 업데이트할 WAV 파일 경로
            data_size: 실제 오디오 데이터 크기 (바이트)

        Raises:
            WriteError: 헤더 업데이트 실패
            PermissionError: 파일 쓰기 권한 없음
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise WriteError(f"파일이 존재하지 않습니다: {file_path}")

        try:
            # 파일 크기 및 헤더 정보 읽기
            file_size = file_path.stat().st_size

            with open(file_path, "r+b") as f:
                # RIFF 헤더 확인
                f.seek(0)
                riff_header = f.read(12)

                if len(riff_header) != 12:
                    raise WriteError("유효하지 않은 RIFF 헤더")

                if riff_header[:4] != b"RIFF":
                    raise WriteError("유효하지 않은 RIFF 헤더입니다")

                if riff_header[8:12] != b"WAVE":
                    raise WriteError("유효하지 않은 WAVE 헤더입니다")

                # RIFF chunk 크기 계산 및 업데이트
                # RIFF chunk 크기 = 전체 파일 크기 - 8바이트 (RIFF 헤더 제외)
                riff_chunk_size = file_size - 8

                # RIFF chunk 크기 업데이트 (4바이트, 리틀 엔디안)
                f.seek(4)
                f.write(struct.pack("<I", riff_chunk_size))

                # data chunk 위치 찾기
                data_chunk_pos = find_chunk_position(f, b"data")

                if data_chunk_pos is None:
                    raise WriteError("data chunk를 찾을 수 없습니다")

                # data chunk 크기 업데이트
                f.seek(data_chunk_pos + 4)  # 'data' 문자열 다음 4바이트가 크기
                f.write(struct.pack("<I", data_size))

                # 파일 동기화
                f.flush()

                self.logger.debug(
                    f"헤더 업데이트 완료: RIFF 크기={riff_chunk_size}, "
                    f"data 크기={data_size}"
                )

        except PermissionError:
            raise PermissionError(f"파일 쓰기 권한이 없습니다: {file_path}")
        except Exception as e:
            raise WriteError(f"헤더 업데이트 실패 ({file_path}): {e}")


    def validate_wav_structure(self, file_path: Union[str, Path]) -> dict:
        """
        WAV 파일의 구조를 검증하고 정보를 반환합니다.

        Args:
            file_path: 검증할 WAV 파일 경로

        Returns:
            파일 구조 정보 딕셔너리

        Raises:
            WriteError: 파일 구조 오류
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise WriteError(f"파일이 존재하지 않습니다: {file_path}")

        try:
            file_size = file_path.stat().st_size
            structure_info: Dict[str, Any] = {
                "file_size": file_size,
                "riff_chunk_size": 0,
                "data_chunk_size": 0,
                "has_riff_header": False,
                "has_fmt_chunk": False,
                "has_data_chunk": False,
                "chunks": [],
            }

            with open(file_path, "rb") as f:
                # RIFF 헤더 확인
                riff_header = f.read(12)
                if (
                    len(riff_header) == 12
                    and riff_header[:4] == b"RIFF"
                    and riff_header[8:12] == b"WAVE"
                ):
                    structure_info["has_riff_header"] = True
                    structure_info["riff_chunk_size"] = struct.unpack(
                        "<I", riff_header[4:8]
                    )[0]
                else:
                    raise WriteError("유효하지 않은 RIFF/WAVE 헤더")

                # chunk 정보 수집
                while True:
                    chunk_start = f.tell()
                    chunk_header = f.read(8)

                    if len(chunk_header) < 8:
                        break

                    chunk_id = chunk_header[:4]
                    chunk_size = struct.unpack("<I", chunk_header[4:8])[0]

                    chunk_info = {
                        "id": chunk_id.decode("ascii", errors="ignore"),
                        "size": chunk_size,
                        "position": chunk_start,
                    }
                    structure_info["chunks"].append(chunk_info)

                    if chunk_id == b"fmt ":
                        structure_info["has_fmt_chunk"] = True
                    elif chunk_id == b"data":
                        structure_info["has_data_chunk"] = True
                        structure_info["data_chunk_size"] = chunk_size

                    # 다음 chunk로 이동 (패딩 고려)
                    skip_size = chunk_size + (chunk_size % 2)
                    f.seek(skip_size, 1)

                # 구조 유효성 검사
                if not structure_info["has_fmt_chunk"]:
                    raise WriteError("fmt chunk가 없습니다")

                if not structure_info["has_data_chunk"]:
                    raise WriteError("data chunk가 없습니다")

                # 크기 일치성 검사
                expected_riff_size = file_size - 8
                if abs(structure_info["riff_chunk_size"] - expected_riff_size) > 1:
                    self.logger.warning(
                        f"RIFF 크기 불일치: 헤더={structure_info['riff_chunk_size']}, "
                        f"실제={expected_riff_size}"
                    )

                self.logger.debug(
                    f"파일 구조 검증 완료: {len(structure_info['chunks'])}개 chunk"
                )
                return structure_info

        except Exception as e:
            raise WriteError(f"파일 구조 검증 실패 ({file_path}): {e}")

    def finalize_wav_file(
        self, file_path: Union[str, Path], data_size: int, validate: bool = True
    ) -> dict:
        """
        WAV 파일을 완성합니다 (헤더 업데이트 + 검증).

        Args:
            file_path: 완성할 WAV 파일 경로
            data_size: 실제 오디오 데이터 크기
            validate: 완성 후 구조 검증 여부

        Returns:
            파일 정보 딕셔너리

        Raises:
            WriteError: 파일 완성 실패
        """
        file_path = Path(file_path)

        self.logger.info(f"WAV 파일 완성 시작: {file_path.name}")

        # 헤더 업데이트
        self.update_wave_header(file_path, data_size)

        # 검증 (옵션)
        if validate:
            structure_info = self.validate_wav_structure(file_path)
        else:
            file_size = file_path.stat().st_size
            structure_info = {"file_size": file_size, "data_chunk_size": data_size}

        # 파일 정보 요약
        file_info = {
            "path": str(file_path),
            "size_bytes": structure_info["file_size"],
            "size_mb": structure_info["file_size"] / (1024 * 1024),
            "data_size_bytes": data_size,
            "data_size_mb": data_size / (1024 * 1024),
            "validated": validate,
        }

        self.logger.info(
            f"WAV 파일 완성: {file_path.name} "
            f"({file_info['size_mb']:.2f} MB, 데이터 {file_info['data_size_mb']:.2f} MB)"
        )

        return file_info
