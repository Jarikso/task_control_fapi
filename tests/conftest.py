from datetime import datetime

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from fastapi import FastAPI



from app.models.task import Task
from app.models.product import Product
from app.models.brigade import Brigade
from app.models.wc import WorkCenter
from app.main import app as fastapi_app
from app.database import engine, AsyncSessionLocal, Base
from app.database import get_db as original_get_db


@pytest.fixture
def test_client():
    return TestClient(fastapi_app)


@pytest.fixture
def mock_engine():
    return AsyncMock(spec=AsyncEngine)


@pytest.fixture
def mock_app():
    """Фикстура для мокирования FastAPI приложения"""
    app = MagicMock(spec=FastAPI)
    return app


@pytest.fixture
async def async_engine():
    """Фикстура для асинхронного движка БД"""
    yield engine


@pytest.fixture
async def async_session_factory():
    """Фикстура для фабрики асинхронных сессий"""
    yield AsyncSessionLocal


@pytest.fixture
async def db_session(async_session_factory):
    """Фикстура для асинхронной сессии БД с автоматическим закрытием"""
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
async def test_db():
    """Фикстура для временной тестовой БД в памяти"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def async_test_session(test_db):
    """Фикстура для асинхронной сессии с тестовой БД"""
    async_session = async_sessionmaker(
        bind=test_db,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def mock_get_db(mocker, async_test_session):
    """Фикстура для мокирования get_db"""
    async def mock_session():
        async with async_test_session() as session:
            yield session

    mocker.patch("app.database.get_db", new=mock_session)
    return async_test_session


# Основные фикстуры приложения и клиента
@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


# Фикстуры тестовых данных
@pytest.fixture
def valid_task_data():
    return {
        "status_close": False,
        "task_description": "Test task",
        "shift": "Day",
        "shift_start": "2023-01-01T08:00:00",
        "shift_end": "2023-01-01T20:00:00",
        "batch_number": 123,
        "batch_date": "2025-07-19T18:05:23.538Z",
        "closed_date": "2025-07-19T18:05:23.538Z",
        "brigade": {"name": "Brigade 1"},
        "work_center": {"name": "WC 1"},
        "product": [{"nomenclature": "Product 1", "ekn_code": "EKN123"}]
    }


@pytest.fixture
def valid_tasks_data():
    return [
        {
            "status_close": False,
            "task_description": "Test task 1",
            "shift": "Day",
            "shift_start": "2023-01-01T08:00:00",
            "shift_end": "2023-01-01T20:00:00",
            "batch_number": 123,
            "batch_date": "2023-01-01",
            "brigade": {"name": "Brigade 1"},
            "work_center": {"name": "WC 1"},
            "product": [{"nomenclature": "Product 1", "ekn_code": "EKN123"}]
        },
        {
            "status_close": True,
            "task_description": "Test task 2",
            "shift": "Night",
            "shift_start": "2023-01-01T20:00:00",
            "shift_end": "2023-01-02T08:00:00",
            "batch_number": 124,
            "batch_date": "2023-01-01",
            "brigade": {"name": "Brigade 2"},
            "work_center": {"name": "WC 2"},
            "product": [{"nomenclature": "Product 2", "ekn_code": "EKN124"}]
        }
    ]


@pytest.fixture
def mock_task():
    task = MagicMock(spec=Task)
    task.id = 1
    task.status_close = False
    task.task_description = "Test task"
    task.shift = "Day"
    task.batch_number = 123
    task.shift_start = datetime(2023, 1, 1, 8, 0)
    task.shift_end = datetime(2023, 1, 1, 20, 0)
    task.batch_date = datetime(2023, 1, 1)
    task.closed_date = None

    brigade = MagicMock(spec=Brigade)
    brigade.name = "Brigade 1"
    task.brigade = brigade

    work_center = MagicMock(spec=WorkCenter)
    work_center.name = "WC 1"
    task.work_center = work_center

    product = MagicMock(spec=Product)
    product.nomenclature = "Product 1"
    product.ekn_code = "EKN123"
    task.products = [product]

    return task

@pytest.fixture
def mock_tasks():
    """Фикстура для мокирования списка задач с правильной структурой"""
    # Задача 1
    task1 = MagicMock(spec=Task)
    task1.id = 1
    task1.status_close = False
    task1.task_description = "Test task 1"
    task1.shift = "Day"
    task1.batch_number = 123
    task1.shift_start = datetime(2023, 1, 1, 8, 0)
    task1.shift_end = datetime(2023, 1, 1, 20, 0)
    task1.batch_date = datetime(2023, 1, 1)

    brigade1 = MagicMock(spec=Brigade)
    brigade1.name = "Brigade 1"
    task1.brigade = brigade1

    wc1 = MagicMock(spec=WorkCenter)
    wc1.name = "WC 1"
    task1.work_center = wc1

    product1 = MagicMock(spec=Product)
    product1.nomenclature = "Product 1"
    product1.ekn_code = "EKN123"
    task1.products = [product1]

    # Задача 2
    task2 = MagicMock(spec=Task)
    task2.id = 2
    task2.status_close = True
    task2.task_description = "Test task 2"
    task2.shift = "Night"
    task2.batch_number = 124
    task2.shift_start = datetime(2023, 1, 1, 20, 0)
    task2.shift_end = datetime(2023, 1, 2, 8, 0)
    task2.batch_date = datetime(2023, 1, 1)

    brigade2 = MagicMock(spec=Brigade)
    brigade2.name = "Brigade 2"
    task2.brigade = brigade2

    wc2 = MagicMock(spec=WorkCenter)
    wc2.name = "WC 2"
    task2.work_center = wc2

    product2 = MagicMock(spec=Product)
    product2.nomenclature = "Product 2"
    product2.ekn_code = "EKN124"
    task2.products = [product2]

    return [task1, task2]