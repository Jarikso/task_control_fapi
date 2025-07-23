from abc import ABC
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager


class BaseRepository(ABC):
    """Абстрактный базовый класс для репозиториев с поддержкой транзакций.

    Attributes:
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Инициализация репозитория.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
        """
        self.db = db

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[None]:
        """Контекстный менеджер для управления транзакциями.

        Yields:
            None: Вход в контекст транзакции.

        Note:
            Если уже находимся в транзакции, просто продолжает работу без создания новой.
        """
        if not self.db.in_transaction():
            async with self.db.begin():
                yield
        else:
            yield
