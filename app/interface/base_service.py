from abc import ABC, abstractmethod
from typing import List, Dict, TypeVar, Generic, Any

import logging

from app.tools.sttng_log import setup_logger
from app.tools.exceptions import ValidationError

T = TypeVar("T")
K = TypeVar("K")

logger = setup_logger()


class BaseService(ABC, Generic[T, K]):
    """Абстрактный базовый класс сервиса с общими CRUD операциями.

    Type Variables:
        T: Тип возвращаемой DTO/модели.
        K: Тип входной DTO для создания/обновления.

    Attributes:
        repository: Репозиторий для работы с данными.
        logger (logging.Logger): Логгер сервиса.
    """

    def __init__(self, repository: Any) -> None:
        """Инициализация сервиса.

        Args:
            repository: Репозиторий для работы с данными.
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        logger.info(f"Инициализирован сервис {self.__class__.__name__}")

    @abstractmethod
    async def create(self, data: K) -> T:
        """Создание новой сущности.

        Args:
            data (K): Данные для создания сущности.

        Returns:
            T: Созданная сущность.

        Raises:
            ValidationError: При ошибках валидации данных.
        """
        raise NotImplementedError

    @abstractmethod
    async def create_batch(self, items_data: List[K]) -> List[T]:
        """Массовое создание сущностей.

        Args:
            items_data (List[K]): Список данных для создания.

        Returns:
            List[T]: Список созданных сущностей.

        Raises:
            ValidationError: При ошибках валидации данных.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, entity_id: int) -> T:
        """Получение сущности по идентификатору.

        Args:
            entity_id (int): Идентификатор сущности.

        Returns:
            T: Найденная сущность.

        Raises:
            NotFoundException: Если сущность не найдена.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity_id: int, update_data: K) -> T:
        """Обновление сущности.

        Args:
            entity_id (int): Идентификатор сущности.
            update_data (K): Данные для обновления.

        Returns:
            T: Обновленная сущность.

        Raises:
            NotFoundException: Если сущность не найдена.
            ValidationError: При ошибках валидации данных.
            BusinessLogicException: При нарушении бизнес-правил.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_filtered(
        self, filters: Dict[str, Any], offset: int = 0, limit: int = 100
    ) -> List[T]:
        """Получение списка сущностей с фильтрацией и пагинацией.

        Args:
            filters (Dict[str, Any]): Словарь фильтров.
            offset (int): Смещение (по умолчанию 0).
            limit (int): Лимит (по умолчанию 100).

        Returns:
            List[T]: Список сущностей.

        Raises:
            ValidationError: При невалидных параметрах пагинации.
        """
        raise NotImplementedError

    def _validate_pagination(self, offset: int, limit: int) -> None:
        """Валидация параметров пагинации.

        Args:
            offset (int): Смещение.
            limit (int): Лимит.

        Raises:
            ValidationError: Если параметры пагинации невалидны.
        """
        if limit > 1000:
            raise ValidationError("Максимальный лимит - 1000")
        if offset < 0:
            raise ValidationError("Смещение не может быть отрицательным")

    def _log_operation(self, operation: str, details: str = "") -> None:
        """Логирование операций сервиса.

        Args:
            operation (str): Название операции.
            details (str): Дополнительные детали (по умолчанию "").
        """
        self.logger.info(f"{operation} {details}".strip())
