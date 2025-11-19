from database import Base, BaseModel, db_session
from sqlalchemy import Column, Integer, SmallInteger, DateTime
from datetime import datetime

class Showtime(Base, BaseModel):
    """
    Reference model for showtimes - actual data managed by Theatre Service
    This is a lightweight reference to avoid duplicating showtime data
    """
    __tablename__ = 'showtimes'

    showtime_id = Column(Integer, primary_key=True)
    screen_id = Column(Integer, nullable=False)
    movie_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    seats_booked = Column(SmallInteger, nullable=False, default=0)
    created_by = Column(Integer, nullable=True)

    def __init__(self, showtime_id, screen_id, movie_id, start_time, created_by=None):
        self.showtime_id = showtime_id
        self.screen_id = screen_id
        self.movie_id = movie_id
        self.start_time = start_time
        self.created_by = created_by
        self.seats_booked = 0

    def __repr__(self):
        return f'<Showtime {self.showtime_id}: Movie {self.movie_id}, Screen {self.screen_id}>'

    def increment_booked_seats(self, count=1):
        """Increment the number of booked seats"""
        self.seats_booked += count
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()

    def decrement_booked_seats(self, count=1):
        """Decrement the number of booked seats"""
        self.seats_booked = max(0, self.seats_booked - count)
        self.updated_at = datetime.utcnow()
        db_session.add(self)
        db_session.flush()