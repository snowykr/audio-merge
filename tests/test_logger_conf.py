import logging
import tempfile
from pathlib import Path

from logger_conf import setup_logger, get_logger


class TestLoggerConf:
    """logger_conf 모듈 테스트"""

    def test_setup_logger_basic(self):
        """기본 로거 설정 테스트"""
        logger = setup_logger(name="test_logger")

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logger_verbose(self):
        """상세 모드 로거 설정 테스트"""
        logger = setup_logger(name="test_verbose", verbose=True)

        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self):
        """파일 로깅을 포함한 로거 설정 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            logger = setup_logger(name="test_file_logger", log_file=str(log_file))

            # 테스트 로그 메시지
            logger.info("Test message")

            # 파일이 생성되었는지 확인
            assert log_file.exists()

            # 파일 내용 확인
            content = log_file.read_text(encoding="utf-8")
            assert "Test message" in content

    def test_get_logger(self):
        """기존 로거 가져오기 테스트"""
        # 먼저 로거 설정
        original_logger = setup_logger(name="test_get_logger")

        # 같은 이름으로 로거 가져오기
        retrieved_logger = get_logger(name="test_get_logger")

        assert original_logger is retrieved_logger
        assert retrieved_logger.name == "test_get_logger"

    def test_logger_message_levels(self):
        """로그 레벨별 메시지 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "levels.log"

            # INFO 레벨 로거
            info_logger = setup_logger(
                name="info_test", verbose=False, log_file=str(log_file)
            )

            info_logger.debug("Debug message")  # 표시되지 않음
            info_logger.info("Info message")  # 표시됨
            info_logger.warning("Warning message")  # 표시됨
            info_logger.error("Error message")  # 표시됨

            content = log_file.read_text(encoding="utf-8")
            assert "Debug message" not in content  # DEBUG는 INFO 레벨에서 기록되지 않음
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content

    def test_logger_duplicate_setup(self):
        """로거 중복 설정 테스트 (핸들러 중복 방지)"""
        logger_name = "duplicate_test"

        # 첫 번째 설정
        logger1 = setup_logger(name=logger_name)
        handler_count_1 = len(logger1.handlers)

        # 두 번째 설정 (같은 이름)
        logger2 = setup_logger(name=logger_name)
        handler_count_2 = len(logger2.handlers)

        # 같은 로거 객체이고, 핸들러가 중복되지 않았는지 확인
        assert logger1 is logger2
        assert handler_count_1 == handler_count_2
