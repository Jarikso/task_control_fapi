import pytest

from datetime import datetime
from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock

class TestTaskEndpoints:
    @pytest.mark.asyncio
    async def test_create_task_success(self, test_client, mocker):
        """Тест успешного создания задачи.

        Args:
            test_client (AsyncClient): Клиент для тестирования API
            mocker (MockerFixture): Фикстура для мокирования

        Проверяет:
            - Код ответа 201 (Created)
            - Корректность возвращаемых данных
            - Соответствие полей в ответе
        """
        task_data = {
            "status_close": False,
            "task_description": "Test task",
            "shift": "Day",
            "shift_start": "2023-01-01T08:00:00",
            "shift_end": "2023-01-01T20:00:00",
            "batch_number": 123,
            "batch_date": "2023-01-01",
            "brigade": {"name": "Brigade 1"},
            "work_center": {"name": "WC 1"},
            "product": [{"nomenclature": "Product 1", "ekn_code": "EKN123"}]
        }

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status_close = False
        mock_task.task_description = "Test task"
        mock_task.shift = "Day"
        mock_task.batch_number = 123

        mock_service = mocker.patch("app.routes.task.TaskService")
        mock_service_instance = mock_service.return_value

        async def mock_create(*args, **kwargs):
            return mock_task

        mock_service_instance.create = AsyncMock(side_effect=mock_create)

        mock_repo = mocker.patch("app.routes.task.TaskRepository")
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.create_task = AsyncMock(return_value=mock_task)

        response = test_client.post("/task/", json=task_data)

        print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data["task_description"] == "Test task"
        assert response_data["batch_number"] == 123

    def test_create_tasks_success(self, client, mocker, valid_tasks_data):
        """Тест успешного массового создания задач."""
        # Мокируем возвращаемые задачи
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.status_close = False
        mock_task1.task_description = "Test task 1"
        mock_task1.shift = "Day"
        mock_task1.batch_number = 123
        mock_task1.brigade = MagicMock(name="Brigade 1")
        mock_task1.work_center = MagicMock(name="WC 1")
        mock_task1.product = [MagicMock(nomenclature="Product 1", ekn_code="EKN123")]

        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_task2.status_close = True
        mock_task2.task_description = "Test task 2"
        mock_task2.shift = "Night"
        mock_task2.batch_number = 124
        mock_task2.brigade = MagicMock(name="Brigade 2")
        mock_task2.work_center = MagicMock(name="WC 2")
        mock_task2.product = [MagicMock(nomenclature="Product 2", ekn_code="EKN124")]

        # Мокируем сервис
        mock_service = mocker.patch("app.routes.task.TaskService")
        mock_service_instance = mock_service.return_value
        mock_service_instance.create_batch = AsyncMock(return_value=[mock_task1, mock_task2])

        # Отправляем запрос
        response = client.post("/tasks/", json=valid_tasks_data)

        # Проверяем результаты
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert len(response_data) == 2
        assert response_data[0]["task_description"] == "Test task 1"
        assert response_data[0]["batch_number"] == 123
        assert response_data[1]["task_description"] == "Test task 2"
        assert response_data[1]["batch_number"] == 124

    @pytest.mark.asyncio
    async def test_read_task_success(self, client, mock_task):
        """Тест успешного получения задачи по ID.

        Проверяет:
            - Код ответа 200 (OK)
            - Корректность возвращаемых данных
            - Соответствие полей в ответе
        """
        # Мокируем сервис
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service_instance = mock_service.return_value
            mock_service_instance.get = AsyncMock(return_value=mock_task)

            # Отправляем запрос
            task_id = 1
            response = client.get(f"/task/{task_id}")

            # Проверяем результаты
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()

            assert response_data["id"] == 1
            assert response_data["task_description"] == "Test task"
            assert response_data["batch_number"] == 123
            assert not response_data["status_close"]
            assert response_data["brigade"]["name"] == "Brigade 1"
            assert response_data["work_center"]["name"] == "WC 1"
            assert response_data["products"][0]["nomenclature"] == "Product 1"

    @pytest.mark.asyncio
    async def test_update_task_success(self, client, mocker):
        """Тест успешного обновления задачи.

        Проверяет:
            - Код ответа 200 (OK)
            - Корректность возвращаемых данных
            - Соответствие обновленных полей
        """
        # Данные для обновления
        update_data = {
            "task_description": "Updated task",
            "status_close": True,
            "batch_number": 456,
            "closed_date": "2023-01-02T00:00:00"
        }

        # Создаем мок обновленной задачи с правильной структурой
        updated_task = MagicMock()
        updated_task.id = 1
        updated_task.status_close = True
        updated_task.task_description = "Updated task"
        updated_task.shift = "Day"
        updated_task.batch_number = 456
        updated_task.closed_date = datetime(2023, 1, 2)

        # Создаем правильные моки для связанных объектов
        mock_brigade = MagicMock()
        mock_brigade.name = "Brigade 1"
        updated_task.brigade = mock_brigade

        mock_work_center = MagicMock()
        mock_work_center.name = "WC 1"
        updated_task.work_center = mock_work_center

        mock_product = MagicMock()
        mock_product.nomenclature = "Product 1"
        mock_product.ekn_code = "EKN123"
        updated_task.products = [mock_product]

        # Мокируем сервис
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service_instance = mock_service.return_value
            mock_service_instance.update = AsyncMock(return_value=updated_task)

            # Отправляем запрос на обновление
            task_id = 1
            response = client.put(f"/task/{task_id}", json=update_data)

            # Проверяем результаты
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()

            assert response_data["id"] == 1
            assert response_data["task_description"] == "Updated task"
            assert response_data["status_close"] is True
            assert response_data["batch_number"] == 456
            assert response_data["closed_date"] == "2023-01-02T00:00:00"
            assert response_data["brigade"]["name"] == "Brigade 1"
            assert response_data["work_center"]["name"] == "WC 1"
            assert response_data["products"][0]["nomenclature"] == "Product 1"

    @pytest.mark.asyncio
    async def test_filter_tasks_success(self, client, mocker, mock_tasks):
        """Тест успешного получения отфильтрованного списка задач."""
        # Мокируем сервис
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service_instance = mock_service.return_value
            mock_service_instance.get_filtered = AsyncMock(return_value=mock_tasks)

            # Параметры фильтрации
            params = {
                "status_close": "false",
                "batch_number": "123",
                "limit": "10",
                "skip": "0"
            }

            # Отправляем запрос
            response = client.get("/task/", params=params)

            # Проверяем результаты
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()

            assert len(response_data) == 2
            assert response_data[0]["id"] == 1
            assert response_data[0]["task_description"] == "Test task 1"
            assert response_data[0]["batch_number"] == 123
            assert response_data[0]["brigade"]["name"] == "Brigade 1"
            assert response_data[0]["work_center"]["name"] == "WC 1"
            assert response_data[0]["products"][0]["nomenclature"] == "Product 1"
