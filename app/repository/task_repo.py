from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional

from app.tools.sttng_log import setup_logger
from app.tools.exceptions import RepositoryException, TaskNotFoundException

from app.interface.base_repository import BaseRepository

from app.models.task import Task

from app.repository.product_repo import ProductRepository
from app.repository.brigade_repo import BrigadeRepository
from app.repository.wc_repo import WorkCenterRepository

from app.schemas import task as schema

logger = setup_logger()


class TaskRepository(BaseRepository):
    """
    Репозиторий для работы с задачами в базе данных.
    Предоставляет методы для CRUD операций с задачами и связанными сущностями.
    """

    def __init__(
        self,
        db: AsyncSession,
        brigade_repo: BrigadeRepository,
        wc_repo: WorkCenterRepository,
        product_repo: ProductRepository,
    ):
        """Инициализирует репозиторий задач.

        Args:
            db (AsyncSession): Сессия базы данных.
            brigade_repo (BrigadeRepository): Репозиторий бригад.
            wc_repo (WorkCenterRepository): Репозиторий рабочих центров.
            product_repo (ProductRepository): Репозиторий продукции.
        """
        super().__init__(db)
        self.brigade_repo = brigade_repo
        self.wc_repo = wc_repo
        self.product_repo = product_repo

    async def create_task(self, task_data: schema.TaskCreate) -> schema.TaskBase:
        """Создает новую задачу с продукцией.

        Args:
            task_data (TaskCreate): Данные для создания задачи.

        Returns:
            Task: Созданная задача.

        Raises:
            RepositoryException: Если произошла ошибка при создании.
        """
        async with self._transaction():
            try:
                brigade = await self.brigade_repo.get_or_create_brigade(
                    name=task_data.brigade.name
                )
                work_center = await self.wc_repo.get_or_create_work_center(
                    name=task_data.work_center.name
                )
                add_task = await self._add_task(task_data, brigade.id, work_center.id)

                for product_data in task_data.product:
                    await self.product_repo.create_product_data(
                        product=product_data, task=add_task.id
                    )

                return add_task
            except Exception as e:
                logger.error(f"Ошибка созданиязадачи: {str(e)}")
                raise

    async def create_tasks(
        self, tasks_data: List[schema.TaskCreate]
    ) -> List[schema.TaskBase]:
        """Создает несколько задач в одной транзакции.

        Args:
            tasks_data (List[TaskCreate]): Список данных для создания задач.

        Returns:
            List[Task]: Список созданных задач.

        Raises:
            RepositoryException: Если произошла ошибка при создании.
        """
        async with self._transaction():
            try:
                created_tasks = []
                brigade_cache = {}
                work_center_cache = {}

                # Сначала создаем все бригады и рабочие центры
                for task_data in tasks_data:
                    if task_data.brigade.name not in brigade_cache:
                        brigade = await self.brigade_repo.get_or_create_brigade(
                            name=task_data.brigade.name
                        )
                        brigade_cache[task_data.brigade.name] = brigade

                    if task_data.work_center.name not in work_center_cache:
                        work_center = await self.wc_repo.get_or_create_work_center(
                            name=task_data.work_center.name
                        )
                        work_center_cache[task_data.work_center.name] = work_center

                # Затем создаем задачи
                for task_data in tasks_data:
                    db_task = await self._add_task(
                        task_data,
                        brigade_cache[task_data.brigade.name].id,
                        work_center_cache[task_data.work_center.name].id,
                    )
                    self.db.add(db_task)
                    created_tasks.append(db_task)

                await self.db.flush()

                # Затем добавляем продукты
                for task_data, db_task in zip(tasks_data, created_tasks):
                    if task_data.product:
                        products = (
                            task_data.product
                            if isinstance(task_data.product, list)
                            else [task_data.product]
                        )
                        for product in products:
                            await self.product_repo.create_product_data(
                                product, db_task.id
                            )

                return created_tasks

            except Exception as e:
                logger.error(f"Ошибка при создании задач: {str(e)}")
                raise

    async def get_task_by_id(self, task_id: int) -> Task:
        """Получает задачу по ID со связанными сущностями.

        Args:
            task_id (int): ID задачи.

        Returns:
            Optional[Task]: Найденная задача или None.

        Raises:
            RepositoryException: Если произошла ошибка при получении.
        """
        try:
            query = (
                select(Task)
                .options(
                    joinedload(Task.products),
                    joinedload(Task.brigade),
                    joinedload(Task.work_center),
                )
                .where(Task.id == task_id)
            )
            result = await self.db.execute(query)
            task = result.scalars().first()
            return task
        except Exception as e:
            logger.error(f"Ошибка при получении задачи: {str(e)}")
            raise

    async def update_task(self, task_id: int, update_data: dict) -> Task:
        """Обновляет задачу и связанные сущности.

        Args:
            task_id (int): ID задачи.
            update_data (Dict): Данные для обновления.

        Returns:
            Task: Обновленная задача.

        Raises:
            TaskNotFoundException: Если задача не найдена.
            RepositoryException: При других ошибках.
        """
        async with self._transaction():
            try:
                # Получаем задачу со всеми связями
                task = await self.get_task_by_id(task_id)
                if not task:
                    raise TaskNotFoundException(
                        f"Задача с идентификатором {task_id} не найдена"
                    )

                # Основные поля
                for field, value in update_data.items():
                    if hasattr(task, field) and field not in [
                        "products",
                        "brigade",
                        "work_center",
                    ]:
                        setattr(task, field, value)

                # Обновляем продукты (если есть в запросе)
                if "products" in update_data:
                    await self.product_repo.update_task_products(
                        task_id, update_data["products"]
                    )

                # Обновляем связи многие-к-одному
                brigade_name = (
                    update_data.get("brigade", {}).get("name")
                    if isinstance(update_data.get("brigade"), dict)
                    else None
                )
                work_center_name = (
                    update_data.get("work_center", {}).get("name")
                    if isinstance(update_data.get("work_center"), dict)
                    else None
                )

                if brigade_name or work_center_name:
                    await self.update_task_relations(
                        task, brigade_name, work_center_name
                    )

                await self.db.commit()
                await self.db.refresh(task)
                return task
            except Exception as e:
                logger.error(f"Ошибка при обновлении задачи: {str(e)}")
                self.db.rollback()
                raise

    async def _update_task_relations(
        self,
        task: Task,
        brigade_name: Optional[str] = None,
        work_center_name: Optional[str] = None,
    ) -> None:
        """Обновляет связи задачи с бригадой и рабочим центром.

        Args:
            task (Task): Объект задачи.
            brigade_name (Optional[str]): Название бригады.
            work_center_name (Optional[str]): Название рабочего центра.

        Raises:
            RepositoryException: Если произошла ошибка при обновлении.
        """
        async with self._transaction():
            try:
                if brigade_name:
                    brigade = await self.brigade_repo.get_or_create_brigade(
                        brigade_name
                    )
                    task.brigade_id = brigade.id

                if work_center_name:
                    work_center = await self.wc_repo.get_or_create_work_center(
                        work_center_name
                    )
                    task.work_center_id = work_center.id

                await self.db.commit()
                return task
            except Exception as e:
                logger.error(f"Ошибка при обновлении связей задачи: {str(e)}")
                raise RepositoryException(f"Не удалось обновить связи задач: {str(e)}")

    async def get_tasks_with_filters(
        self,
        status_close: Optional[bool] = None,
        batch_number: Optional[int] = None,
        batch_date: Optional[str] = None,
        work_center_id: Optional[int] = None,
        brigade_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
        shift_start_from: Optional[datetime] = None,
        shift_start_to: Optional[datetime] = None,
    ) -> List[Task]:
        """Получает задачи с применением фильтров.

        Args:
            status_close (Optional[bool]): Статус завершения.
            batch_number (Optional[int]): Номер партии.
            batch_date (Optional[datetime]): Дата партии.
            work_center_id (Optional[int]): ID рабочего центра.
            brigade_id (Optional[int]): ID бригады.
            offset (int): Смещение (по умолчанию 0).
            limit (int): Лимит (по умолчанию 100).
            shift_start_from (Optional[datetime]): Начало периода смены.
            shift_start_to (Optional[datetime]): Конец периода смены.

        Returns:
            List[Task]: Список найденных задач.

        Raises:
            RepositoryException: Если произошла ошибка при получении.
        """
        try:
            query = select(Task).options(
                joinedload(Task.products),
                joinedload(Task.brigade),
                joinedload(Task.work_center),
            )

            if status_close is not None:
                query = query.where(Task.status_close == status_close)
            if batch_number is not None:
                query = query.where(Task.batch_number == batch_number)
            if batch_date is not None:
                query = query.where(Task.batch_date == batch_date)
            if work_center_id is not None:
                query = query.where(Task.work_center_id == work_center_id)
            if brigade_id is not None:
                query = query.where(Task.brigade_id == brigade_id)
            if shift_start_from is not None:
                query = query.where(Task.shift_start >= shift_start_from)
            if shift_start_to is not None:
                query = query.where(Task.shift_start <= shift_start_to)

            query = query.offset(offset).limit(limit)
            result = await self.db.execute(query)
            tasks = result.unique().scalars().all()
            return tasks
        except Exception as e:
            logger.error(f"Ошибка при получении задач с фильтрами: {str(e)}")
            raise

    async def find_task_by_batch(
        self, batch_number: int, batch_date: str
    ) -> Optional[Task]:
        """Находит задачу по номеру и дате партии.

        Args:
            batch_number (int): Номер партии.
            batch_date (datetime): Дата партии.

        Returns:
            Optional[Task]: Найденная задача или None.

        Raises:
            RepositoryException: Если произошла ошибка при поиске.
        """
        try:
            query = select(Task).where(
                and_(Task.batch_number == batch_number, Task.batch_date == batch_date)
            )
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Ошибка при поиске задачи по партии: {str(e)}")
            raise RepositoryException(
                f"Не удалось получить отфильтрованные задачи: {str(e)}"
            )

    async def _add_task(
        self, task: schema.TaskCreate, brigade: int, work_center: int
    ) -> None:
        """Добавляет новую задачу в базу данных.

        Args:
            task_data (TaskCreate): Данные задачи.
            brigade_id (int): ID бригады.
            work_center_id (int): ID рабочего центра.

        Returns:
            Task: Созданная задача.

        Raises:
            RepositoryException: Если произошла ошибка при добавлении.
        """
        async with self._transaction():
            try:
                db_task = Task(
                    status_close=task.status_close,
                    task_description=task.task_description,
                    shift=task.shift,
                    shift_start=task.shift_start,
                    shift_end=task.shift_end,
                    batch_number=task.batch_number,
                    batch_date=task.batch_date,
                    brigade_id=brigade,
                    work_center_id=work_center,
                )

                self.db.add(db_task)
                await self.db.flush()
                await self.db.refresh(db_task)
                return db_task
            except Exception as e:
                logger.error(f"Ошибка при добавлении задачи: {str(e)}")
                raise RepositoryException(f"Не удалось добавить задачу: {str(e)}")
