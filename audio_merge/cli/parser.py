"""
명령행 인수 파싱 모듈

CLI 옵션과 인수들을 파싱하는 기능을 제공합니다.
"""

import argparse


def parse_arguments() -> argparse.Namespace:
    """CLI 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description="WAV 파일 병합 도구 - 여러 WAV 파일을 순서대로 병합합니다",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # Interactive 모드
  python main.py

  # Command-line 모드
  python main.py file1.wav file2.wav file3.wav
  python main.py --output merged.wav --auto-convert --verbose file1.wav file2.wav
  python main.py --fade 500 --buffer-size 32768 *.wav
        """,
    )

    # 입력 파일 (positional arguments)
    parser.add_argument(
        "files", nargs="*", help="병합할 WAV 파일들 (지정하지 않으면 interactive 모드)"
    )

    # 출력 파일
    parser.add_argument(
        "-o", "--output", default="merged.wav", help="출력 파일 경로 (기본: merged.wav)"
    )

    # 자동 변환
    parser.add_argument(
        "--auto-convert", action="store_true", help="포맷 불일치 시 자동 변환"
    )

    # Cross-fade
    parser.add_argument(
        "--fade",
        type=int,
        default=0,
        metavar="MS",
        help="파일 간 cross-fade 길이(ms) (기본: 0)",
    )

    # 상세 로그
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")

    # 버퍼 크기
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=65536,
        metavar="BYTES",
        help="스트리밍 버퍼 크기(바이트) (기본: 65536)",
    )

    # 로그 파일
    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="로그 파일 경로 (지정하지 않으면 파일 로깅 비활성화)",
    )

    return parser.parse_args()