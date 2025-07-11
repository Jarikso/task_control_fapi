from loguru import logger
import sys
import os


def setup_logger():
    """Настройка и возврат логгера loguru."""
    logger.remove()  # Удаляем стандартный обработчик

    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Логи в консоль
    logger.add(
        sys.stdout,
        level="INFO",
        format=log_format,
        colorize=True,
    )

    # Логи в файл (с ротацией)
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    logger.add(
        os.path.join(logs_dir, "app_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format=log_format,
        rotation="00:00",
        retention="30 days",
        compression="zip",
    )

    return logger