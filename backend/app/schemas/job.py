from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company: Optional[str] = None
    description: str = Field(..., min_length=20)


class JobDescriptionOut(BaseModel):
    id: int
    title: str
    company: Optional[str]
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
