from datetime import datetime

from typing import Optional, List, Dict
from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.sttng_log import setup_logger
from app.tools.exceptions import TaskNotFoundException

from app.interface.base_route import BaseRouter

from app.database import get_db

from app.repository.task_repo import TaskRepository
from app.repository.product_repo import ProductRepository
from app.repository.brigade_repo import BrigadeRepository
from app.repository.wc_repo import WorkCenterRepository

from app.services.task_service import TaskService
from app.services.product_service import ProductService

from app.schemas import task as schema

logger = setup_logger()


class TaskRouter(BaseRouter):
    """Роутер для обработки HTTP запросов, связанных с задачами (сменными заданиями).

    Предоставляет endpoints для:
    - Создания и массового создания задач
    - Получения задач по ID или с фильтрами
    - Обновления задач
    - Добавления продукции к задачам
    - Агрегации продукции

    Attributes:
        router (APIRouter): FastAPI роутер для регистрации endpoints.
    """

    def __init__(self) -> None:
        """Инициализирует роутер и настраивает маршруты."""
        super().__init__()
        logger.info(f"Инициализация роутера {self.__class__.__name__}")

    def _setup_routes(self) -> None:
        """Настраивает все маршруты API для работы с задачами."""
        self.router.add_api_route(
            "/tasks/",
            self.create_tasks,
            methods=["POST"],
            response_model=List[schema.TaskBase],
            status_code=201,
            summary="Массовое создание задач",
            description="Создает несколько задач в одной транзакции",
        )
        self.router.add_api_route(
            "/task/",
            self.create_task,
            methods=["POST"],
            response_model=schema.TaskBase,
            status_code=201,
            summary="Создание задачи",
            description="Создает новое сменное задание",
        )
        self.router.add_api_route(
            "/task/{task_id}",
            self.read_task,
            methods=["GET"],
            response_model=schema.Task,
            summary="Получение задачи",
            description="Возвращает задачу по ID со всей связанной информацией",
        )
        self.router.add_api_route(
            "/task/{task_id}",
            self.update_task,
            methods=["PUT"],
            response_model=schema.Task,
            summary="Обновление задачи",
            description="Обновляет данные сменного задания",
        )
        self.router.add_api_route(
            "/task/",
            self.read_filter_tasks,
            methods=["GET"],
            response_model=List[schema.Task],
            summary="Фильтрация задач",
            description="Возвращает список задач с возможностью фильтрации",
        )
        self.router.add_api_route(
            "/task/products",
            self.add_products_to_tasks,
            methods=["POST"],
            status_code=200,
            response_model=List[Dict[str, str]],
            summary="Добавление продукции",
            description="Добавляет продукцию к существующим партиям",
        )
        self.router.add_api_route(
            "/task/aggregate",
            self.aggregate_tasks,
            methods=["POST"],
            response_model=Dict[str, str],
            summary="Агрегация продукции",
            description="Отмечает продукцию как агрегированную",
        )

    def create_repository(self, db: AsyncSession) -> TaskRepository:
        """Создает и возвращает экземпляр TaskRepository.

        Args:
            db (AsyncSession): Сессия базы данных.

        Returns:
            TaskRepository: Экземпляр репозитория задач.
        """
        return TaskRepository(
            db=db,
            brigade_repo=BrigadeRepository(db),
            wc_repo=WorkCenterRepository(db),
            product_repo=ProductRepository(db),
        )

    def task_service(self, db: AsyncSession = Depends(get_db)):
        repo = self.create_repository(db)
        return TaskService(repo)

    def get_your_service(self, db: AsyncSession = Depends(get_db)):
        repo = self.create_repository(db)
        return TaskService(repo)

    def product_service(self, db: AsyncSession = Depends(get_db)):
        repo = self.create_repository(db)
        return ProductService(repo)

    async def create_tasks(
            self,
            tasks: List[schema.TaskCreate],
            db: AsyncSession = Depends(get_db)
    ) -> List[schema.TaskBase]:
        """Массово создает задачи (сменные задания).

        Args:
            tasks (List[TaskCreate]): Список данных для создания задач.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            List[TaskBase]: Список созданных задач.

        Raises:
            HTTPException: Если произошла ошибка при создании.
        """
        try:
            service = self.task_service(db)
            return await service.create_batch(tasks)
        except Exception as e:
            logger.error(f"Ошибка при массовом создании задач: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def create_task(
        self, task: schema.TaskCreate, db: AsyncSession = Depends(get_db)
    ) -> schema.TaskBase:
        """Создает новое сменное задание.

        Args:
            task (TaskCreate): Данные для создания задачи.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            TaskBase: Созданная задача.

        Raises:
            HTTPException: Если произошла ошибка при создании.
        """
        try:
            service = self.task_service(db)
            return await service.create(task)
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def read_task(
        self, task_id: int, db: AsyncSession = Depends(get_db)
    ) -> schema.Task:
        """Получает сменное задание по ID.

        Args:
            task_id (int): ID задачи.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            Task: Найденная задача со всей связанной информацией.

        Raises:
            HTTPException: 404 если задача не найдена.
            HTTPException: 400 при других ошибках.
        """
        try:
            service = self.task_service(db)
            return await service.get(task_id)
        except TaskNotFoundException as e:
            logger.error(f"Задача {task_id} не найдена: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Ошибка при получении задачи: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def update_task(
        self,
        task_id: int,
        task_update: schema.TaskUpdate,
        db: AsyncSession = Depends(get_db),
    ) -> schema.Task:
        """Обновляет сменное задание.

        Args:
            task_id (int): ID обновляемой задачи.
            task_update (TaskUpdate): Данные для обновления.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            Task: Обновленная задача.

        Raises:
            HTTPException: 404 если задача не найдена.
            HTTPException: 400 при других ошибках.
        """
        try:
            service = self.task_service(db)
            return await service.update(task_id, task_update)
        except TaskNotFoundException as e:
            logger.error(f"Задача {task_id} не найдена: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Ошибка при обновлении задачи: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def read_filter_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status_close: Optional[bool] = None,
        batch_number: Optional[int] = None,
        batch_date: Optional[datetime] = None,
        work_center_id: Optional[int] = None,
        brigade_id: Optional[int] = None,
        shift_start_from: Optional[datetime] = None,
        shift_start_to: Optional[datetime] = None,
        db: AsyncSession = Depends(get_db),
    ) -> List[schema.Task]:
        """Получает список сменных заданий с фильтрацией.

        Args:
            skip (int): Смещение для пагинации (по умолчанию 0).
            limit (int): Лимит для пагинации (по умолчанию 100).
            status_close (Optional[bool]): Фильтр по статусу завершения.
            batch_number (Optional[int]): Фильтр по номеру партии.
            batch_date (Optional[datetime]): Фильтр по дате партии.
            work_center_id (Optional[int]): Фильтр по ID рабочего центра.
            brigade_id (Optional[int]): Фильтр по ID бригады.
            shift_start_from (Optional[datetime]): Начало периода смены.
            shift_start_to (Optional[datetime]): Конец периода смены.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            List[Task]: Список задач, соответствующих фильтрам.

        Raises:
            HTTPException: Если произошла ошибка при получении данных.
        """
        try:
            service = self.task_service(db)
            filter_dict = {
                "status_close": status_close,
                "batch_number": batch_number,
                "batch_date": batch_date,
                "work_center_id": work_center_id,
                "brigade_id": brigade_id,
                "shift_start_from": shift_start_from,
                "shift_start_to": shift_start_to,
            }
            print(filter_dict)
            tasks = await service.get_filtered(
                filters=filter_dict, offset=skip, limit=limit
            )
            return tasks
        except Exception as e:
            logger.error(f"Ошибка при получении задач с фильтрами: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def add_products_to_tasks(
        self, products_data: List[dict], db: AsyncSession = Depends(get_db)
    ) -> List[dict]:
        """Добавляет продукцию к существующим партиям.

        Args:
            products_data (List[Dict]): Список данных о продукции.
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            List[Dict]: Список с результатами добавления.

        Raises:
            HTTPException: Если произошла ошибка при добавлении.
        """
        try:
            product_service = self.product_service(db)
            return await product_service.add_products_to_batches(products_data)
        except Exception as e:
            logger.error(f"Ошибка при добавлении продукции: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def aggregate_tasks(
        self, aggregate_data: dict, db: AsyncSession = Depends(get_db)
    ) -> dict:
        """Выполняет агрегацию продукции.

        Args:
            aggregate_data (Dict): Данные для агрегации (task_id, ekn_code).
            db (AsyncSession): Сессия базы данных (инъекция зависимости).

        Returns:
            Dict: Результат агрегации.

        Raises:
            HTTPException: 400 при ошибках валидации.
            HTTPException: 404 если данные не найдены.
            HTTPException: 500 при внутренних ошибках.
        """
        try:
            product_service = self.product_service(db)
            return await product_service.aggregate_product(
                task_id=aggregate_data["task_id"], ekn_code=aggregate_data["ekn_code"]
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Ошибка при агрегации: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")


task_router = TaskRouter()
