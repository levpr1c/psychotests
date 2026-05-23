from datetime import date, datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int | None = None
    name: str = Field(min_length=1, max_length=100)
    birth_date: date | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    birth_date: date | None = None
