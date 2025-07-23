import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import sessionmaker
from fastapi import HTTPException
from typing import Any

from app.tools.sttng_log import setup_logger

# Настройка логирования
logger = setup_logger()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:admin@localhost/task_control_fapi"
)

# Инициализация движка БД
engine: AsyncEngine
AsyncSessionLocal: sessionmaker[AsyncSession]


engine = create_async_engine(
    DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=3600
)
logger.info("database.py - База данных успешно создана")

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
logger.info("Асинхронный сеанс настроен")


Base: Any = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий БД.

    Yields:
        AsyncSession: Асинхронная сессия для работы с БД

    Raises:
        HTTPException: В случае ошибок работы с БД
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        logger.debug("Создание сессии базы данных")
        yield session
    except SQLAlchemyError as e:
        logger.exception("Ошибка работы с базой данных")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed") from e
    finally:
        await session.close()
        logger.debug("Сессия базы данных закрыта")
