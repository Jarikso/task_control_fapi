from sqlalchemy import select

from app.tools.sttng_log import setup_logger
from app.tools.exceptions import RepositoryException

from app.interface.base_repository import BaseRepository

from app.models.wc import WorkCenter

logger = setup_logger()


class WorkCenterRepository(BaseRepository):
    """Репозиторий для работы с рабочими центрами в базе данных.

    Предоставляет методы для создания и получения записей о рабочих центрах.
    """

    async def get_or_create_work_center(self, name: str) -> WorkCenter:
        """
        Получает или создает рабочий центр по названию.

        Args:
            name (str): Название рабочего центра.

        Returns:
            WorkCenter: Найденный или созданный объект рабочего центра.

        Raises:
            RepositoryException: Если произошла ошибка при работе с базой данных.
        """
        async with self._transaction():
            try:
                query = select(WorkCenter).where(WorkCenter.name == name)
                result = await self.db.execute(query)
                work_center = result.scalars().first()

                if not work_center:
                    work_center = WorkCenter(name=name)
                    self.db.add(work_center)
                    await self.db.flush()
                    await self.db.refresh(work_center)

                return work_center
            except Exception as e:
                logger.error(f"Ошибка при получении/создании рабочего центра: {str(e)}")
                raise RepositoryException(
                    f"Не удалось получить или создать рабочий центр: {str(e)}"
                )
