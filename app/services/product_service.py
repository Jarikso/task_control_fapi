from typing import List, Dict
from fastapi import HTTPException

from app.repository.task_repo import TaskRepository
from app.tools.sttng_log import setup_logger
from app.tools.exceptions import (
    ValidationError,
    ProductNotFoundException,
    ProductWrongBatchException,
    ProductAlreadyAggregatedException,
)

logger = setup_logger()


class ProductService:
    """Сервис для работы с продуктами (бизнес-логика)"""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo
        logger.info(f"Инициализирован сервис {self.__class__.__name__}")

    async def add_products_to_batches(
        self, products_data: List[Dict]
    ) -> List[Dict[str, int]]:
        """Добавляет продукцию к существующим партиям.

        Args:
            products_data (List[Dict]): Список данных о продукции. Каждый элемент должен содержать:
                - ekn_code: Код ЕКН продукции
                - batch_number: Номер партии
                - batch_date: Дата партии

        Returns:
            List[Dict]: Список словарей с информацией о добавленной продукции:
                - ekn_code: Код ЕКН
                - task_id: ID связанной задачи

        Raises:
            ValidationError: Если список продукции пуст или данные невалидны.
            HTTPException: При других ошибках (500 статус).
        """
        try:
            if not products_data:
                raise ValidationError("Список продукции не может быть пустым")

            # Валидация входных данных
            validated_data = []
            for item in products_data:
                if not all(
                    key in item for key in ["ekn_code", "batch_number", "batch_date"]
                ):
                    continue
                validated_data.append(item)

            added_products = await self.task_repo.product_repo.add_products_to_batches(
                validated_data
            )
            return [
                {"ekn_code": p.ekn_code, "task_id": p.task_id} for p in added_products
            ]
        except Exception as e:
            logger.error(f"Ошибка при добавлении продукции: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def aggregate_product(self, task_id: int, ekn_code: str) -> Dict[str, str]:
        """Выполняет агрегацию продукции с проверками.

        Args:
            task_id (int): ID задачи, к которой привязана продукция.
            ekn_code (str): Код ЕКН продукции.

        Returns:
            Dict: Словарь с результатом агрегации (содержит ekn_code).

        Raises:
            HTTPException:
                - 404 если продукт не найден.
                - 400 если продукт привязан к другой партии или уже агрегирован.
                - 500 при внутренних ошибках.
        """
        try:
            product = await self.task_repo.product_repo.aggregate_product(
                task_id, ekn_code
            )
            return product
        except ProductNotFoundException as e:
            logger.error(f"Продукт не найден: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except (ProductWrongBatchException, ProductAlreadyAggregatedException) as e:
            logger.error(f"Ошибка агрегации: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Неизвестная ошибка при агрегации: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
