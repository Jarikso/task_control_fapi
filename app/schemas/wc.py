from pydantic import BaseModel, Field


class WorkCenterBase(BaseModel):
    """Базовая схема для рабочего центра."""

    name: str = Field(..., description="Название рабочего центра")


class WorkCenterCreate(WorkCenterBase):
    """Схема для создания рабочего центра. Наследует все поля WorkCenterBase."""

    pass


class WorkCenter(WorkCenterBase):
    """Полная схема рабочего центра, включая ID."""

    id: int = Field(..., description="Уникальный идентификатор рабочего центра")

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True
