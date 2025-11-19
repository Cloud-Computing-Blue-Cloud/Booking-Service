from database import db
from models.booked_seat import BookedSeat
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

class SeatService:
    @staticmethod
    def check_seats_availability(showtime_id, seats):
        """
        Check if seats are available for booking

        Args:
            showtime_id: ID of the showtime
            seats: List of seat dictionaries with 'row' and 'col'

        Returns:
            tuple: (boolean indicating availability, message)
        """
        try:
            for seat in seats:
                # Check if seat is already booked or on hold (and not expired)
                existing_seat = BookedSeat.query.filter(
                    and_(
                        BookedSeat.showtime_id == showtime_id,
                        BookedSeat.seat_row == seat['row'],
                        BookedSeat.seat_col == seat['col'],
                        BookedSeat.is_deleted == False,
                        BookedSeat.status.in_(['on_hold', 'booked'])
                    )
                ).first()

                if existing_seat:
                    # Check if hold is expired
                    if existing_seat.is_hold_expired():
                        existing_seat.release()
                        db.session.commit()
                    else:
                        return False, f"Seat {seat['row']}{seat['col']} is already booked or on hold"

            return True, "All seats are available"

        except Exception as e:
            logger.error(f"Error checking seat availability: {str(e)}")
            return False, f"Error checking availability: {str(e)}"

    @staticmethod
    def get_booked_seats(showtime_id):
        """
        Get all booked seats for a showtime

        Args:
            showtime_id: ID of the showtime

        Returns:
            list: List of booked seats
        """
        try:
            booked_seats = BookedSeat.query.filter(
                and_(
                    BookedSeat.showtime_id == showtime_id,
                    BookedSeat.is_deleted == False,
                    BookedSeat.status.in_(['on_hold', 'booked'])
                )
            ).all()

            # Filter out expired holds
            active_seats = []
            for seat in booked_seats:
                if seat.is_hold_expired():
                    seat.release()
                    db.session.commit()
                else:
                    active_seats.append(seat)

            return active_seats

        except Exception as e:
            logger.error(f"Error getting booked seats: {str(e)}")
            return []

    @staticmethod
    def get_seat_map(showtime_id, screen_rows, screen_cols):
        """
        Generate a seat map showing availability

        Args:
            showtime_id: ID of the showtime
            screen_rows: List of row identifiers (e.g., ['A', 'B', 'C'])
            screen_cols: Number of columns

        Returns:
            dict: Seat map with availability status
        """
        try:
            booked_seats = SeatService.get_booked_seats(showtime_id)
            booked_set = {(seat.seat_row, seat.seat_col) for seat in booked_seats}

            seat_map = {}
            for row in screen_rows:
                seat_map[row] = []
                for col in range(1, screen_cols + 1):
                    seat_map[row].append({
                        'row': row,
                        'col': col,
                        'available': (row, col) not in booked_set
                    })

            return seat_map

        except Exception as e:
            logger.error(f"Error generating seat map: {str(e)}")
            return {}

    @staticmethod
    def extend_seat_hold(booking_id, additional_minutes=5):
        """
        Extend the hold time for seats in a booking

        Args:
            booking_id: ID of the booking
            additional_minutes: Additional minutes to extend

        Returns:
            tuple: (success boolean, message)
        """
        try:
            seats = BookedSeat.query.filter_by(
                booking_id=booking_id,
                status='on_hold',
                is_deleted=False
            ).all()

            if not seats:
                return False, "No seats on hold found for this booking"

            for seat in seats:
                seat.extend_hold(additional_minutes)

            db.session.commit()
            logger.info(f"Extended hold for booking {booking_id} by {additional_minutes} minutes")
            return True, f"Hold extended by {additional_minutes} minutes"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error extending seat hold: {str(e)}")
            return False, f"Failed to extend hold: {str(e)}"