from database import Base, BaseModel, db_session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Booking(Base, BaseModel):
    __tablename__ = 'bookings'

    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    showtime_id = Column(Integer, nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey('payments.payment_id'), nullable=True)
    booking_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='pending')  # pending, confirmed, cancelled, failed
    created_by = Column(Integer, nullable=True)

    # Relationships
    booked_seats = relationship('BookedSeat', backref='booking', lazy='dynamic',
                               foreign_keys='BookedSeat.booking_id')
    payment = relationship('Payment', backref='booking', uselist=False,
                          foreign_keys=[payment_id])

    def __init__(self, user_id, showtime_id, created_by=None):
        self.user_id = user_id
        self.showtime_id = showtime_id
        self.created_by = created_by
        self.booking_time = datetime.utcnow()
        self.status = 'pending'

    def __repr__(self):
        return f'<Booking {self.booking_id}: User {self.user_id}, Showtime {self.showtime_id}, Status: {self.status}>'

    def to_dict(self):
        """Convert booking to dictionary with related data"""
        data = super().to_dict()
        data['seats'] = [seat.to_dict() for seat in self.booked_seats.filter_by(is_deleted=False).all()]
        if self.payment:
            data['payment'] = self.payment.to_dict()
        return data

    def confirm(self):
        """Confirm the booking"""
        self.status = 'confirmed'
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def cancel(self):
        """Cancel the booking"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
        # Also release the seats
        for seat in self.booked_seats.filter_by(is_deleted=False).all():
            seat.release()
        db_session.add(self)
        db_session.flush()