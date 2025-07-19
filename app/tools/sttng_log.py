import sys

from typing import NoReturn
from loguru import logger
from pathlib import Path


def setup_logger() -> logger:
    """Настраивает и возвращает конфигурированный логгер loguru.

    Конфигурация включает:
    - Вывод в консоль (уровень INFO)
    - Запись в файлы с ротацией (уровень DEBUG)
    - Стандартизированный формат логов

    Returns:
        logger: Сконфигурированный экземпляр логгера.

    Example:
        >>> log = setup_logger()
        >>> log.info("Тестовое сообщение")
    """
    logger.remove()

    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    _setup_console_logging(log_format)

    _setup_file_logging(log_format)

    return logger


def _setup_console_logging(format: str) -> NoReturn:
    """Настраивает вывод логов в консоль.

    Args:
        format (str): Формат строки лога.
    """
    logger.add(
        sys.stdout,
        level="INFO",
        format=format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


def _setup_file_logging(format: str) -> NoReturn:
    """Настраивает запись логов в файлы с ротацией.

    Args:
        format (str): Формат строки лога.
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format=format,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
