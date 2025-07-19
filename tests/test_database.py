import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_engine_initialization(async_engine):
    """
    Тест инициализации движка базы данных.

    Проверяет:
    1. Что движок БД успешно создается
    2. Что движок является асинхронным
    3. Что URL подключения корректный
    """
    engine = async_engine
    assert engine is not None, "Движок БД не был инициализирован"
    assert "asyncpg" in str(engine.url), "Движок должен быть асинхронным"
    assert "postgresql" in str(engine.url), "Должен использоваться PostgreSQL"
    assert engine.pool is not None, "Пул соединений не был создан"


@pytest.mark.asyncio
async def test_async_session_creation(async_session_factory):
    """
    Тест создания асинхронной сессии.

    Проверяет:
    1. Что фабрика сессий AsyncSessionLocal создана
    2. Что созданная сессия является асинхронной
    3. Что сессия корректно привязана к движку
    """
    session = async_session_factory()
    try:
        assert session is not None, "Сессия не была создана"
        assert isinstance(session, AsyncSession), "Сессия должна быть асинхронной"
        assert session.bind is not None, "Сессия должна быть привязана к движку"
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_database_connection(db_session):
    """
    Тест подключения к базе данных.

    Проверяет:
    1. Что можно установить соединение с БД
    2. Что можно выполнить простой SQL-запрос
    3. Что БД отвечает (проверка версии PostgreSQL)
    """
    try:
        # Выполняем простой запрос для проверки версии PostgreSQL
        result = await db_session.execute(text("SELECT version()"))
        version = result.scalar()

        assert version is not None, "Не удалось получить версию PostgreSQL"
        assert "PostgreSQL" in version, "Ответ должен содержать информацию о PostgreSQL"
    except Exception as e:
        pytest.fail(f"Ошибка при подключении к БД: {str(e)}")