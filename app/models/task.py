from datetime import datetime
from typing import Optional, List
from pydantic import ConfigDict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, DateTime, Boolean
from app.database import Base
from app.models.product import Product
from app.models.brigade import Brigade
from app.models.wc import WorkCenter


class Task(Base):
    """Модель сменного задания/партии.

    Attributes:
        id (int): Уникальный идентификатор задачи.
        status_close (bool): Статус выполнения задачи.
        closed_date (Optional[datetime]): Дата завершения задания.
        task_description (Optional[str]): Описание задачи.
        shift (Optional[str]): Смена.
        shift_start (datetime): Начало смены.
        shift_end (datetime): Окончание смены.
        batch_number (int): Номер партии.
        batch_date (datetime): Дата партии.
        brigade_id (int): Идентификатор бригады.
        work_center_id (int): Идентификатор рабочего центра.
        products (List[Product]): Список связанной продукции.
        brigade (Brigade): Связанная бригада.
        work_center (WorkCenter): Связанный рабочий центр.
    """

    __tablename__ = "tasks"
    model_config = ConfigDict(from_attributes=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status_close: Mapped[bool] = mapped_column(
        Boolean, default=False, doc="Статус выполнения"
    )
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Дата завершения задания"
    )
    task_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Описание задачи"
    )
    shift: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Смена")
    shift_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), doc="Начало смены"
    )
    shift_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), doc="Окончание смены"
    )
    batch_number: Mapped[int] = mapped_column(doc="Номер партии")
    batch_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), doc="Дата партии"
    )

    brigade_id: Mapped[int] = mapped_column(ForeignKey("brigade.id"), doc="Бригада")
    work_center_id: Mapped[int] = mapped_column(
        ForeignKey("work_centers.id"), doc="Идентификатор РЦ"
    )

    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="task_ref"
    )
    brigade: Mapped["Brigade"] = relationship("Brigade", back_populates="task_ref")
    work_center: Mapped["WorkCenter"] = relationship(
        "WorkCenter", back_populates="task_ref"
    )
