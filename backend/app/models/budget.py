from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id       = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, nullable=False)
    amount   = Column(Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "amount": self.amount,
        }