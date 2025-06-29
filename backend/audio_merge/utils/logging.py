import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "audio_merge", verbose: bool = False, log_file: Optional[str] = None
) -> logging.Logger:
    """
    로깅 시스템을 설정합니다.

    Args:
        name: 로거 이름
        verbose: 상세 로그 출력 여부 (DEBUG 레벨)
        log_file: 로그 파일 경로 (None이면 파일 로깅 비활성화)

    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)

    # 기존 핸들러 제거 (중복 로그 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 로그 레벨 설정
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # 로그 포맷 설정
    verbose_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    simple_format = "%(levelname)s: %(message)s"

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if verbose:
        console_formatter = logging.Formatter(verbose_format)
    else:
        console_formatter = logging.Formatter(simple_format)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 설정 (옵션)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 파일에는 항상 DEBUG 레벨 저장

        file_formatter = logging.Formatter(verbose_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "audio_merge") -> logging.Logger:
    """
    기존에 설정된 로거를 가져옵니다.

    Args:
        name: 로거 이름

    Returns:
        로거 객체
    """
    return logging.getLogger(name)
