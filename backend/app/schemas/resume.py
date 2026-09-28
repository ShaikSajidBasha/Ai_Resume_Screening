from pydantic import BaseModel
from datetime import datetime


class ResumeOut(BaseModel):
    id: int
    file_name: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
