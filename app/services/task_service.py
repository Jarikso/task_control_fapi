from datetime import datetime
from typing import List, Dict

from app.repository.task_repo import TaskRepository
from app.models.task import Task
from app.tools.sttng_log import setup_logger
from app.tools.exceptions import TaskNotFoundException, ValidationError
from app.schemas import task as schema

# Предполагаем, что BaseService находится в app.services.base_service
from app.interface.base_service import BaseService

logger = setup_logger()


class TaskService(BaseService[schema.Task, schema.TaskCreate]):
    """
    Сервис для работы с задачами (сменными заданиями).
    Наследует базовые CRUD операции от BaseService и добавляет специфичную логику.
    """

    def __init__(self, task_repo: TaskRepository):
        """Инициализирует сервис задач.

        Args:
            task_repo (TaskRepository): Репозиторий для работы с задачами.
        """
        super().__init__(task_repo)
        self.task_repo = task_repo

    async def create_batch(
        self, tasks_data: List[schema.TaskCreate]
    ) -> List[schema.Task]:
        """Массово создает задачи (сменные задания).

        Args:
            tasks_data (List[TaskCreate]): Список данных для создания задач.

        Returns:
            List[Task]: Список созданных задач.

        Raises:
            ValidationError: Если данные невалидны.
            Exception: При других ошибках.
        """
        try:
            if not tasks_data:
                raise ValidationError("Список задач не может быть пустым")

            self._log_operation(f"Создание {len(tasks_data)} задач")

            # Валидация данных
            for task in tasks_data:
                if not task.shift_start or not task.shift_end:
                    raise ValidationError("Даты начала и окончания смены обязательны")
                if task.shift_start >= task.shift_end:
                    raise ValidationError(
                        "Дата начала смены должна быть раньше даты окончания"
                    )

            return await self.task_repo.create_tasks(tasks_data)

        except Exception as e:
            self.logger.error(f"Ошибка создания задач: {str(e)}")
            raise

    async def create(self, task_data: schema.TaskCreate) -> schema.Task:
        """Создает новую задачу (сменное задание).

        Args:
            task_data (TaskCreate): Данные для создания задачи.

        Returns:
            Task: Созданная задача.

        Raises:
            ValidationError: Если данные невалидны.
        """
        try:
            task = await self.task_repo.create_task(task_data)
            self._log_operation("Создана задача", f"ID {task.id}")
            return task
        except Exception as e:
            self.logger.error(f"Ошибка создания задачи: {str(e)}")
            raise ValidationError(f"Ошибка создания задачи: {str(e)}")

    async def get(self, task_id: int) -> schema.Task:
        """Получает задачу по ID.

        Args:
            task_id (int): Идентификатор задачи.

        Returns:
            Task: Найденная задача.

        Raises:
            TaskNotFoundException: Если задача не найдена.
        """
        task = await self.task_repo.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundException(f"Задача с ID {task_id} не найдена")
        return task

    async def update(self, task_id: int, update_data: schema.TaskUpdate) -> Task:
        """Обновляет существующую задачу.

        Args:
            task_id (int): Идентификатор задачи.
            update_data (TaskUpdate): Данные для обновления.

        Returns:
            Task: Обновленная задача.

        Raises:
            TaskNotFoundException: Если задача не найдена.
            ValidationError: Если данные невалидны.
        """
        task = await self.task_repo.get_task_by_id(task_id)
        if not task:
            self.logger.error(f"Задача с ID {task_id} не найдена")
            raise TaskNotFoundException(f"Задача с ID {task_id} не найдена")

        update_dict = update_data.model_dump(exclude_unset=True)
        self._log_operation(f"Обновление задачи ID {task_id}", f"Данные: {update_dict}")

        # Бизнес-логика обновления closed_date
        if "status_close" in update_dict:
            update_dict["closed_date"] = (
                datetime.now() if update_dict["status_close"] else None
            )
            self.logger.info(f"Обновление closed_date для задачи ID {task_id}")

        # Валидация продуктов
        if "products" in update_dict:
            if not isinstance(update_dict["products"], list):
                raise ValidationError("Продукты должны быть списком")

            for product in update_dict["products"]:
                if not isinstance(product, dict):
                    raise ValidationError("Каждый продукт должен быть словарем")
                if "nomenclature" not in product:
                    raise ValidationError("В продукте отсутствует поле «номенклатура»")

        updated_task = await self.task_repo.update_task(task_id, update_dict)
        self.logger.info(f"Задача ID {task_id} успешно обновлена")
        return updated_task

    async def get_filtered(
        self, filters: Dict, offset: int = 0, limit: int = 100
    ) -> List[schema.Task]:
        """Получает список задач с применением фильтров.

        Args:
            filters (Dict): Словарь фильтров:
                - status_close: Статус завершения
                - batch_number: Номер партии
                - batch_date: Дата партии
                - work_center_id: ID рабочего центра
                - brigade_id: ID бригады
                - shift_start_from: Начало периода смены
                - shift_start_to: Конец периода смены
            offset (int): Смещение для пагинации.
            limit (int): Лимит для пагинации.

        Returns:
            List[Task]: Список задач, соответствующих фильтрам.
        """
        self._validate_pagination(offset, limit)  # Используем метод базового класса
        print(filters)
        return await self.task_repo.get_tasks_with_filters(
            status_close=filters.get("status_close"),
            batch_number=filters.get("batch_number"),
            batch_date=filters.get("batch_date"),
            work_center_id=filters.get("work_center_id"),
            brigade_id=filters.get("brigade_id"),
            offset=offset,
            limit=limit,
            shift_start_from=filters.get("shift_start_from"),
            shift_start_to=filters.get("shift_start_to"),
        )

    # Можно добавить специфичные для TaskService методы
    async def close_task(self, task_id: int) -> Task:
        """Закрывает задачу (устанавливает статус завершения).

        Args:
            task_id (int): Идентификатор задачи.

        Returns:
            Task: Обновленная задача.
        """
        return await self.update(task_id, schema.TaskUpdate(status_close=True))
