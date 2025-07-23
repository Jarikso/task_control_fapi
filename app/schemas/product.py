from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Базовая схема для продукции."""

    nomenclature: str = Field(..., description="Номенклатура изделия")
    ekn_code: str = Field(..., description="Уникальный код ЕКН")
    is_aggregated: bool = Field(
        default=False, description="Флаг, указывающий был ли продукт агрегирован"
    )


class ProductCreate(ProductBase):
    """Схема для создания продукции. Наследует все поля ProductBase."""

    pass


class Product(ProductBase):
    """Полная схема продукции, включая системные поля."""

    id: int = Field(..., description="Уникальный идентификатор продукции")
    aggregated_at: Optional[datetime] = Field(
        None, description="Дата и время агрегации продукции"
    )

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True
