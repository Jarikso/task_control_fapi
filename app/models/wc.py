from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from typing import Optional
from pydantic import ConfigDict

from app.database import Base
# from app.models.task import Task


class WorkCenter(Base):
    """Модель рабочего центра.

    Attributes:
        id (int): Уникальный идентификатор рабочего центра.
        name (str): Название рабочего центра (макс. 100 символов).
        task_ref (Optional[Task]): Связанная задача.
    """

    __tablename__ = "work_centers"
    model_config = ConfigDict(from_attributes=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), doc="Название рабочего центра")

    task_ref: Mapped[Optional["Task"]] = relationship(
        "Task", back_populates="work_center"
    )
