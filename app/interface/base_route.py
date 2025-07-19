from abc import ABC, abstractmethod
from fastapi import APIRouter
from app.tools.sttng_log import setup_logger

logger = setup_logger()


class BaseRouter(ABC):
    """Абстрактный базовый класс для FastAPI роутеров.

    Attributes:
        router (APIRouter): Экземпляр FastAPI роутера.
    """

    def __init__(self) -> None:
        """Инициализация роутера с автоматической настройкой маршрутов."""
        self.router: APIRouter = APIRouter()
        self._setup_routes()
        self._log_init()

    def _log_init(self) -> None:
        """Логирование инициализации роутера."""
        logger.info("Настройка маршрутов завершена")
        logger.info(f"Работаем с роутами класса {self.__class__.__name__}")

    @abstractmethod
    def _setup_routes(self) -> None:
        """Абстрактный метод для настройки маршрутов API.

        Note:
            Должен быть реализован в дочерних классах.
        """
        logger.debug("Настройка маршрутов")
        raise NotImplementedError("Метод _setup_routes должен быть реализован")
