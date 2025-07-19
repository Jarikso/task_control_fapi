from datetime import datetime
from typing import Optional


class TaskNotFoundException(Exception):
    """Исключение, возникающее при попытке доступа к несуществующей задаче.

    Attributes:
        message (str): Сообщение об ошибке с деталями.
    """

    def __init__(self, message: str = "Задача не найдена") -> None:
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Исключение для ошибок валидации входных данных.

    Attributes:
        message (str): Сообщение с описанием ошибки валидации.
        field (Optional[str]): Название поля с ошибкой (если применимо).
    """

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        self.message = message
        self.field = field
        super().__init__(self.message)


class ProductNotFoundException(Exception):
    """Исключение, возникающее при попытке доступа к несуществующему продукту.

    Attributes:
        ekn_code (str): Код ЕКН продукта, который не был найден.
    """

    def __init__(self, ekn_code: str) -> None:
        self.ekn_code = ekn_code
        super().__init__(f"Продукт с кодом ЕКН {ekn_code} не найден")


class ProductWrongBatchException(Exception):
    """Исключение при попытке работы с продуктом, привязанным к другой партии.

    Attributes:
        current_task_id (int): ID задачи, к которой привязан продукт.
        expected_task_id (int): ID задачи, к которой ожидалась привязка.
    """

    def __init__(self, current_task_id: int, expected_task_id: int) -> None:
        self.current_task_id = current_task_id
        self.expected_task_id = expected_task_id
        super().__init__(
            f"Продукт привязан к задаче {current_task_id}, ожидалась {expected_task_id}"
        )


class ProductAlreadyAggregatedException(Exception):
    """Исключение при попытке повторной агрегации уже агрегированного продукта.

    Attributes:
        ekn_code (str): Код ЕКН продукта.
        aggregated_at (datetime): Дата первоначальной агрегации.
    """

    def __init__(self, ekn_code: str, aggregated_at: datetime) -> None:
        self.ekn_code = ekn_code
        self.aggregated_at = aggregated_at
        super().__init__(f"Продукт {ekn_code} уже был агрегирован {aggregated_at}")


class NotFoundException(Exception):
    """Базовое исключение для случаев, когда сущность не найдена."""

    pass


class BusinessLogicException(Exception):
    """Исключение для нарушений бизнес-правил.

    Attributes:
        rule_name (str): Название нарушенного правила.
    """

    def __init__(self, message: str, rule_name: str) -> None:
        self.rule_name = rule_name
        super().__init__(f"{message} (нарушено правило: {rule_name})")


class RepositoryException(Exception):
    """Исключение для ошибок уровня репозитория при работе с БД.

    Attributes:
        operation (str): Название операции, вызвавшей ошибку.
    """

    def __init__(self, message: str, operation: str) -> None:
        self.operation = operation
        self.message = message
        super().__init__(f"Ошибка при {operation}: {message}")
