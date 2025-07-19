from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import ConfigDict
from fastapi import Depends
from sqlalchemy import select, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, get_db

# from app.models.task import Task


class Product(Base):
    """Модель продукции.

    Attributes:
        id (int): Уникальный идентификатор продукции.
        nomenclature (Optional[str]): Номенклатура изделия.
        ekn_code (Optional[str]): Код ЕКН (уникальный).
        is_aggregated (bool): Флаг агрегации продукции.
        aggregated_at (Optional[datetime]): Дата агрегации.
        task_id (Optional[int]): Идентификатор связанной задачи.
        task_ref (Optional[Task]): Связанная задача (партия).
    """

    __tablename__ = "product"
    model_config = ConfigDict(from_attributes=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nomenclature: Mapped[Optional[str]] = mapped_column(
        Text, default="Изделие", doc="Номенклатура"
    )
    ekn_code: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Код ЕКН", unique=True
    )
    is_aggregated: Mapped[bool] = mapped_column(
        default=False, doc="Был ли код агрегирован"
    )
    aggregated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, doc="Дата агрегации"
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id"), nullable=True
    )
    task_ref: Mapped[Optional["Task"]] = relationship("Task", back_populates="products")

    @classmethod
    async def get_batch_numbers_by_ekn(
        cls, db: AsyncSession = Depends(get_db), ekn_code: Optional[str] = None
    ) -> List[int]:
        """Возвращает номера партий для продукции с указанным кодом ЕКН.

        Args:
            db (AsyncSession): Асинхронная сессия SQLAlchemy.
            ekn_code (Optional[str]): Код ЕКН для поиска.

        Returns:
            List[int]: Список номеров партий. Пустой список, если продукция не найдена.
        """
        product = await db.scalar(select(cls).where(cls.ekn_code == ekn_code))
        return [product.task_ref.batch_number] if product and product.task_ref else []

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект продукции в словарь.

        Returns:
            Dict[str, Any]: Словарь с основными атрибутами продукции.
        """
        return {
            "id": self.id,
            "nomenclature": self.nomenclature,
            "ekn_code": self.ekn_code,
            "task_id": self.task_id,
        }
