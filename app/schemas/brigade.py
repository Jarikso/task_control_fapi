from pydantic import BaseModel


class BrigadeBase(BaseModel):
    """Базовая схема для бригады, содержащая общие поля."""

    name: str


class BrigadeCreate(BrigadeBase):
    """Схема для создания бригады. Наследует все поля BrigadeBase."""

    pass


class Brigade(BrigadeBase):
    """Схема для представления бригады, включая ID."""

    id: int

    class Config:
        """Конфигурация Pydantic для работы с ORM."""

        from_attributes = True
