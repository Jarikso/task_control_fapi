from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, String

from ..database import Base

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    status: Mapped[bool] = mapped_column(default=False)
    task_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_center: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    work_center_id: Mapped[str] = mapped_column(ForeignKey("work_centers.id"))  # ИдентификаторРЦ
    work_center_ref: Mapped["WorkCenter"] = relationship(back_populates="shift_tasks")

    shift: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brigade: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nomenclature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ekn_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shift_start: Mapped[datetime]
    shift_end: Mapped[datetime]

class WorkCenter(Base):
    __tablename__ = "work_centers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))  # Название (Рабочий центр)