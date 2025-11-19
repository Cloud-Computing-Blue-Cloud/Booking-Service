from database import Base, BaseModel, db_session
from sqlalchemy import Column, Integer, String, Numeric
from datetime import datetime
from decimal import Decimal

class Payment(Base, BaseModel):
    __tablename__ = 'payments'

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # pending, completed, failed, refunded
    created_by = Column(Integer, nullable=True)

    def __init__(self, amount, created_by=None):
        self.amount = Decimal(str(amount))
        self.created_by = created_by
        self.status = 'pending'

    def __repr__(self):
        return f'<Payment {self.payment_id}: Amount {self.amount}, Status: {self.status}>'

    def complete(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def fail(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def refund(self):
        """Mark payment as refunded"""
        self.status = 'refunded'
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def to_dict(self):
        """Convert payment to dictionary"""
        data = super().to_dict()
        data['amount'] = float(self.amount)
        return data