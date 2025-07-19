from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.database import Base
from typing import List
from pydantic import ConfigDict
# from app.models.task import Task


class Brigade(Base):
    """Модель рабочей бригады/команды.

    Attributes:
        id (int): Уникальный идентификатор бригады.
        name (str): Название бригады/команды (макс. 100 символов).
        task_ref (List[Task]): Список задач, связанных с этой бригадой.
    """

    __tablename__ = "brigade"
    model_config = ConfigDict(from_attributes=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), doc="Название бригады/команды")

    task_ref: Mapped[List["Task"]] = relationship("Task", back_populates="brigade")
