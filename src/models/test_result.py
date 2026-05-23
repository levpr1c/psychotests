from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class TestResult(BaseModel):
    id: int | None = None
    user_id: int
    test_name: str
    raw_data: str = ""
    scores: dict[str, Any] = {}
    interpretation: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class TestResultCreate(BaseModel):
    user_id: int
    test_name: str
    raw_data: str = ""
    scores: dict[str, Any] = {}
    interpretation: str = ""
