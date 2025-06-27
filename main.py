#!/usr/bin/env python3
"""
WAV 파일 병합 CLI 프로그램

여러 개의 .wav 파일을 지정한 순서대로 이어 붙여 하나의 .wav 파일로 합치는 프로그램입니다.
무손실(PCM) 병합과 포맷 불일치 시 자동 변환 기능을 제공합니다.
"""

import sys
import time
from pathlib import Path

from logger_conf import setup_logger
from audio_merge.core import WaveValidator, WaveConverter, WaveConcatenator, WaveWriter
from audio_merge.cli import parse_arguments, get_files_interactive
from audio_merge.utils import (
    ValidationError,
    ConversionError,
    ConcatenationError,
    ChunkOverflowError,
    WriteError,
)




def main():
    """메인 함수"""
    start_time = time.time()

    try:
        # 인수 파싱
        args = parse_arguments()

        # 로거 설정
        logger = setup_logger(verbose=args.verbose, log_file=args.log_file)

        logger.info("WAV 파일 병합 프로그램 시작")

        # 파일 목록 결정
        if args.files:
            # Command-line 모드
            input_files = args.files
            logger.info(f"Command-line 모드: {len(input_files)}개 파일")
        else:
            # Interactive 모드
            logger.info("Interactive 모드 시작")
            input_files = get_files_interactive()

        if not input_files:
            logger.error("병합할 파일이 없습니다")
            sys.exit(1)

        logger.info(f"입력 파일: {[Path(f).name for f in input_files]}")
        logger.info(f"출력 파일: {args.output}")
        logger.info(f"자동 변환: {'활성화' if args.auto_convert else '비활성화'}")
        if args.fade > 0:
            logger.info(f"Cross-fade: {args.fade}ms")

        # Step 1: 파일 검증
        logger.info("=== Step 1: 파일 검증 ===")
        validator = WaveValidator()

        try:
            formats, stats = validator.validate_files(input_files)
        except (FileNotFoundError, PermissionError, ValidationError) as e:
            logger.error(f"파일 검증 실패: {e}")
            sys.exit(1)

        # Step 2: 포맷 변환 (필요한 경우)
        logger.info("=== Step 2: 포맷 변환 ===")
        converted_files = input_files

        if not stats["is_consistent"]:
            if not args.auto_convert:
                logger.error(
                    "파일 포맷이 일치하지 않습니다. --auto-convert 옵션을 사용하세요."
                )
                sys.exit(1)

            try:
                with WaveConverter() as converter:
                    converted_files = converter.convert_files(
                        input_files, formats, stats
                    )
                    logger.info(f"{len(converted_files)}개 파일 변환 완료")
            except ConversionError as e:
                logger.error(f"파일 변환 실패: {e}")
                sys.exit(1)

        # Step 3: 파일 병합
        logger.info("=== Step 3: 파일 병합 ===")
        concatenator = WaveConcatenator(buffer_size=args.buffer_size)

        try:
            data_size, duration = concatenator.concatenate_to_file(
                converted_files, args.output, fade_duration_ms=args.fade
            )
        except (ConcatenationError, ChunkOverflowError) as e:
            logger.error(f"파일 병합 실패: {e}")
            sys.exit(1)

        # Step 4: 헤더 완성
        logger.info("=== Step 4: 헤더 완성 ===")
        writer = WaveWriter()

        try:
            file_info = writer.finalize_wav_file(args.output, data_size)
        except (WriteError, PermissionError) as e:
            logger.error(f"헤더 완성 실패: {e}")
            sys.exit(1)

        # Step 5: 완료
        elapsed_time = time.time() - start_time

        logger.info("=== 병합 완료 ===")
        logger.info(f"출력 파일: {file_info['path']}")
        logger.info(f"파일 크기: {file_info['size_mb']:.2f} MB")
        logger.info(f"재생 시간: {duration:.2f}초")
        logger.info(f"처리 시간: {elapsed_time:.2f}초")

        print("\n✅ 병합이 완료되었습니다!")
        print(f"📁 출력 파일: {file_info['path']}")
        print(f"📊 크기: {file_info['size_mb']:.2f} MB")
        print(f"⏱️  길이: {duration:.2f}초")

        # 임시 파일 정리 안내
        if converted_files != input_files:
            logger.info("변환에 사용된 임시 파일들은 자동으로 정리됩니다")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        if "logger" in locals():
            logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        else:
            print(f"오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
