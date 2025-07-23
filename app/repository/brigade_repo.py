from sqlalchemy import select
from app.tools.sttng_log import setup_logger
from app.interface.base_repository import BaseRepository
from app.models.brigade import Brigade
from app.tools.exceptions import RepositoryException

logger = setup_logger()


class BrigadeRepository(BaseRepository):
    """Репозиторий для работы с бригадами в базе данных.

    Предоставляет методы для создания и получения записей о бригадах.
    """

    async def get_or_create_brigade(self, name: str) -> Brigade:
        """Получает или создает бригаду по названию.

        Args:
            name (str): Название бригады.

        Returns:
            Brigade: Найденный или созданный объект бригады.

        Raises:
            RepositoryException: Если произошла ошибка при работе с базой данных.
        """
        async with self._transaction():
            try:
                query = select(Brigade).where(Brigade.name == name)
                result = await self.db.execute(query)
                brigade = result.scalars().first()

                if not brigade:
                    brigade = Brigade(name=name)
                    self.db.add(brigade)
                    await self.db.flush()
                    await self.db.refresh(brigade)

                return brigade
            except Exception as e:
                logger.error(f"Ошибка при получении/создании бригады: {str(e)}")
                raise RepositoryException(
                    f"Не удалось получить или создать бригаду: {str(e)}"
                )
