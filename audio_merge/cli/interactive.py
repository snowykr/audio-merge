"""
대화형 모드 처리 모듈

사용자와의 상호작용을 통해 파일 목록을 입력받는 기능을 제공합니다.
"""

import sys
from typing import List


def get_files_interactive() -> List[str]:
    """Interactive 모드에서 파일 목록을 입력받습니다."""
    print("=== WAV 파일 병합 도구 ===")
    print()

    # 파일 개수 입력
    file_count: int = 0
    while True:
        try:
            file_count_str = input("병합할 파일의 개수를 입력하세요: ").strip()
            file_count = int(file_count_str)
            if file_count <= 0:
                print("1 이상의 숫자를 입력해주세요.")
                continue
            break
        except ValueError:
            print("올바른 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            sys.exit(0)

    # 파일 경로 입력
    files = []
    for i in range(file_count):
        while True:
            try:
                file_path = input(f"파일 {i+1}/{file_count} 경로: ").strip()
                if not file_path:
                    print("파일 경로를 입력해주세요.")
                    continue
                files.append(file_path)
                break
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                sys.exit(0)

    print()
    return files