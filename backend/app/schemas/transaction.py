from pydantic import BaseModel, field_validator  # type: ignore[import]
from datetime import datetime
from typing import Optional


class TransactionCreate(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    category: str
    confidence: float
    date: datetime
    is_anomaly: bool
    anomaly_score: float
    source: str

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources_used: int


class UploadResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]