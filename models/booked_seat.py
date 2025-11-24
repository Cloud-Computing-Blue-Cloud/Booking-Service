from database import Base, BaseModel, db_session
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, ForeignKey, Index, UniqueConstraint
from datetime import datetime, timedelta

class BookedSeat(Base, BaseModel):
    __tablename__ = 'booked_seats'

    booked_seat_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey('bookings.booking_id'), nullable=False, index=True)
    showtime_id = Column(Integer, nullable=False, index=True)
    seat_row = Column(SmallInteger, nullable=False)
    seat_col = Column(SmallInteger, nullable=False)
    status = Column(String(50), nullable=False, default='on_hold')  # on_hold, booked, released
    hold_expiry_time = Column(DateTime, nullable=True)

    # Composite index for seat uniqueness per showtime
    __table_args__ = (
        Index('idx_showtime_seat', 'showtime_id', 'seat_row', 'seat_col'),
        UniqueConstraint('showtime_id', 'seat_row', 'seat_col', 'booking_id',
                        name='uq_showtime_seat_booking'),
    )

    def __init__(self, booking_id, showtime_id, seat_row, seat_col, created_by=None, hold_duration_minutes=10):
        self.booking_id = booking_id
        self.showtime_id = showtime_id
        self.seat_row = seat_row
        self.seat_col = seat_col
        self.status = 'on_hold'
        self.hold_expiry_time = datetime.utcnow() + timedelta(minutes=hold_duration_minutes)
        self.created_by = created_by

    def __repr__(self):
        return f'<BookedSeat {self.booked_seat_id}: {self.seat_row}{self.seat_col}, Status: {self.status}>'

    def is_hold_expired(self):
        """Check if the seat hold has expired"""
        if self.status == 'on_hold' and self.hold_expiry_time:
            return datetime.utcnow() > self.hold_expiry_time
        return False

    def confirm(self):
        """Confirm the seat booking"""
        self.status = 'booked'
        self.hold_expiry_time = datetime.utcnow()  # Set to current time when confirmed
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def release(self):
        """Release the seat"""
        self.status = 'released'
        self.soft_delete()
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def extend_hold(self, additional_minutes=5):
        """Extend the hold time"""
        if self.status == 'on_hold':
            self.hold_expiry_time = datetime.utcnow() + timedelta(minutes=additional_minutes)
            self.updated_at = datetime.utcnow()
            db_session.add(self)
            db_session.flush()