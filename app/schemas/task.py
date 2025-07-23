from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from .product import Product, ProductCreate
from .brigade import Brigade, BrigadeCreate
from .wc import WorkCenter, WorkCenterCreate


class TaskBase(BaseModel):
    """Базовая схема для сменного задания/партии."""

    status_close: bool = Field(default=False, description="Статус завершения задания")
    task_description: Optional[str] = Field(None, description="Описание задачи")
    shift: Optional[str] = Field(None, description="Номер или название смены")
    shift_start: datetime = Field(..., description="Дата и время начала смены")
    shift_end: datetime = Field(..., description="Дата и время окончания смены")
    batch_number: int = Field(..., description="Номер производственной партии")
    batch_date: datetime = Field(..., description="Дата создания партии")


class TaskCreate(TaskBase):
    """Схема для создания сменного задания."""

    product: Optional[List[ProductCreate]] = Field(
        None, description="Список продукции в задании"
    )
    brigade: Optional[BrigadeCreate] = Field(None, description="Данные бригады")
    work_center: Optional[WorkCenterCreate] = Field(
        None, description="Данные рабочего центра"
    )


class Task(TaskBase):
    """Полная схема сменного задания, включая системные поля и связи."""

    id: int = Field(..., description="Уникальный идентификатор задания")
    closed_date: Optional[datetime] = Field(None, description="Дата завершения задания")
    products: Optional[List[Product]] = Field(
        None, description="Список продукции в задании"
    )
    brigade: Optional[Brigade] = Field(None, description="Информация о бригаде")
    work_center: Optional[WorkCenter] = Field(
        None, description="Информация о рабочем центре"
    )

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True


class TaskUpdate(BaseModel):
    """Схема для обновления сменного задания."""

    status_close: Optional[bool] = Field(None, description="Новый статус завершения")
    task_description: Optional[str] = Field(None, description="Новое описание задачи")
    shift: Optional[str] = Field(None, description="Новая смена")
    shift_start: Optional[datetime] = Field(
        None, description="Новое время начала смены"
    )
    shift_end: Optional[datetime] = Field(
        None, description="Новое время окончания смены"
    )
    closed_status: Optional[bool] = Field(
        None, description="Альтернативное поле для статуса завершения"
    )
    products: Optional[List[ProductCreate]] = Field(
        None, description="Обновленный список продукции"
    )
    brigade: Optional[Union[BrigadeCreate, dict]] = Field(
        None, description="Обновленные данные бригады"
    )
    work_center: Optional[Union[WorkCenterCreate, dict]] = Field(
        None, description="Обновленные данные рабочего центра"
    )
