from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base


class Income(Base):
    __tablename__ = "incomes"

    id          = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount      = Column(Float, nullable=False)
    category    = Column(String, default="salary")
    date        = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat() if self.date else None,
        }