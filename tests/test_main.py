import pytest
from fastapi import HTTPException, Request

from unittest.mock import AsyncMock, patch

from app.database import Base
from app.main import app, create_tables, lifespan, http_exception_handler
from app.tools.sttng_log import setup_logger

logger = setup_logger()



@pytest.mark.asyncio
async def test_create_tables_success(mock_engine):
    """
    Тест успешного создания таблиц в базе данных.
    """
    with patch("app.main.engine", mock_engine):
        await create_tables()

    # Проверяем, что был вызван create_all
    mock_engine.begin.return_value.__aenter__.return_value.run_sync.assert_called_once_with(
        Base.metadata.create_all
    )


@pytest.mark.asyncio
async def test_create_tables_failure(mock_engine):
    """
    Тест обработки ошибки при создании таблиц.
    """
    mock_engine.begin.return_value.__aenter__.return_value.run_sync.side_effect = Exception("DB error")

    with patch("app.main.engine", mock_engine):
        with pytest.raises(HTTPException) as exc_info:
            await create_tables()

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Неудалось инициализировать таблицы базы данных"

@pytest.mark.asyncio
async def test_lifespan_success(mock_app):
    with patch("app.main.create_tables", AsyncMock()) as mock_create:
        async with lifespan(mock_app) as _:
            pass
        mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_failure(mock_app):
    with patch("app.main.create_tables", AsyncMock(side_effect=Exception("Startup error"))):
        with pytest.raises(Exception):
            async with lifespan(mock_app) as _:
                pass

@pytest.mark.asyncio
async def test_http_exception_handler():
    """
    Тест обработчика HTTP исключений.
    """
    # Создаем тестовые данные
    request = Request(scope={"type": "http"})
    exc = HTTPException(status_code=404, detail="Not Found")

    # Вызываем обработчик как асинхронную функцию
    response = await http_exception_handler(request, exc)

    # Проверяем результат
    assert response.status_code == 404
    assert response.body == b'{"message":"Not Found"}'
    assert response.headers["content-type"] == "application/json"
