from datetime import datetime

from sqlalchemy import select, delete
from typing import List, Dict

from app.tools.sttng_log import setup_logger
from app.tools.exceptions import (
    RepositoryException,
    ProductAlreadyAggregatedException,
    ProductNotFoundException,
    ProductWrongBatchException,
)


from app.interface.base_repository import BaseRepository

from app.models.task import Task
from app.models.product import Product

logger = setup_logger()


class ProductRepository(BaseRepository):
    """Репозиторий для работы с продукцией в базе данных.

    Предоставляет методы для создания, обновления и агрегации продукции.
    """

    async def create_product_data(self, product: Product, task: int) -> Product:
        """Создает новую запись о продукции.

        Args:
            product (Product): Объект продукции для создания.
            task_id (int): ID связанной задачи.

        Returns:
            Product: Созданный объект продукции.

        Raises:
            RepositoryException: Если произошла ошибка при создании.
        """
        async with self._transaction():
            try:
                product = Product(
                    nomenclature=product.nomenclature,
                    ekn_code=product.ekn_code,
                    is_aggregated=product.is_aggregated,
                    task_id=task,
                )
                self.db.add(product)
                await self.db.flush()
                await self.db.refresh(product)
                return product
            except Exception as e:
                logger.error(f"Ошибка при создании данных о продукции: {str(e)}")
                raise RepositoryException(f"Не удалось создать продукт: {str(e)}")

    async def update_task_products(
        self, task_id: int, products_data: List[dict]
    ) -> List[Product]:
        """Обновляет список продуктов для задачи.

        Args:
            task_id (int): ID задачи.
            products_data (List[Dict]): Список данных о продуктах.

        Returns:
            List[Product]: Список обновленных продуктов.

        Raises:
            RepositoryException: Если произошла ошибка при обновлении.
        """
        async with self._transaction():
            try:
                # Удаляем старые продукты
                await self.db.execute(delete(Product).where(Product.task_id == task_id))

                # Создаем новые продукты
                new_products = []
                for product_data in products_data:
                    if isinstance(product_data, dict):
                        product = Product(
                            nomenclature=product_data.get("nomenclature"),
                            ekn_code=product_data.get("ekn_code"),
                            task_id=task_id,
                        )
                        self.db.add(product)
                        new_products.append(product)

                await self.db.flush()
                return new_products
            except Exception as e:
                logger.error(f"Ошибка при обновлении продуктов задачи: {str(e)}")
                raise RepositoryException(
                    f"Не удалось обновить продукты задачи: {str(e)}"
                )

    async def add_products_to_batches(self, products_data: List[dict]) -> List[Product]:
        """Добавляет продукцию к партиям.

        Args:
            products_data (List[Dict]): Список данных о продукции.

        Returns:
            List[Product]: Список добавленных продуктов.

        Raises:
            RepositoryException: Если произошла ошибка при добавлении.
        """
        async with self._transaction():
            try:
                added_products = []
                for product_data in products_data:
                    ekn_code = product_data["ekn_code"]
                    batch_number = product_data["batch_number"]
                    batch_date_str = product_data["batch_date"]
                    try:
                        batch_date = datetime.fromisoformat(batch_date_str)
                    except (ValueError, TypeError):
                        logger.error(f"Неверный формат даты: {batch_date_str}")
                        continue
                    existing_task = await self.db.execute(
                        select(Task).where(
                            Task.batch_number == batch_number,
                            Task.batch_date == batch_date,
                        )
                    )
                    task = existing_task.scalars().first()
                    if not task:
                        logger.info("Партии нет - сброс!")
                        continue

                    existing_product = await self.db.execute(
                        select(Product).where(Product.ekn_code == ekn_code)
                    )
                    product = existing_product.scalars().first()
                    if not product:
                        product = Product(
                            ekn_code=ekn_code, is_aggregated=False, task_id=task.id
                        )
                        self.db.add(product)
                        await self.db.flush()
                        continue
                    product.task_id = task.id

                await self.db.flush()
                return added_products
            except Exception as e:
                logger.error(f"Ошибка при добавлении продукции к партиям: {str(e)}")
                raise RepositoryException(
                    f"Не удалось добавить продукты в партии.: {str(e)}"
                )

    async def aggregate_product(self, task_id: int, ekn_code: str) -> Dict[str, str]:
        """Выполняет агрегацию продукции.

        Args:
            task_id (int): ID задачи.
            ekn_code (str): Код ЕКН продукции.

        Returns:
            Dict: Словарь с кодом агрегированной продукции.

        Raises:
            ProductNotFoundException: Если продукт не найден.
            ProductWrongBatchException: Если продукт привязан к другой партии.
            ProductAlreadyAggregatedException: Если продукт уже агрегирован.
            RepositoryException: При других ошибках.
        """

        try:
            # Находим продукт по коду
            query = select(Product).where(Product.ekn_code == ekn_code)
            result = await self.db.execute(query)
            product = result.scalars().first()

            if not product:
                raise ProductNotFoundException(f"Продукт с кодом {ekn_code} не найден")

            # Проверяем, что продукт привязан к нужной партии
            if product.task_id != task_id:
                raise ProductWrongBatchException(
                    f"Продукт привязан к другой партии (ID: {product.task_id})"
                )

            # Проверяем, не был ли уже агрегирован
            if product.is_aggregated:
                raise ProductAlreadyAggregatedException(
                    f"Продукт уже был агрегирован в {product.aggregated_at}"
                )

            # Обновляем статус агрегации
            product.is_aggregated = True
            product.aggregated_at = datetime.now()

            await self.db.commit()
            await self.db.refresh(product)
            return {"ekn_code": product.ekn_code}

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка при агрегации продукции: {str(e)}")
            raise RepositoryException(f"Не удалось агрегировать продукт: {str(e)}")
