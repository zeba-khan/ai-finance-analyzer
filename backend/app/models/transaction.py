from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean  # type: ignore[import]
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, default="uncategorized")
    confidence = Column(Float, default=0.0)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[import]
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    source = Column(String, default="manual")

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "confidence": round(self.confidence, 2),
            "date": self.date.isoformat() if self.date else None,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "source": self.source,
        }