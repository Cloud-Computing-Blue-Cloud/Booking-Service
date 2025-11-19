from database import db
from models.booking import Booking
from models.booked_seat import BookedSeat
from models.showtime import Showtime
from services.seat_service import SeatService
from services.payment_service import PaymentService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BookingService:
    @staticmethod
    def create_booking(user_id, showtime_id, seats, created_by=None):
        """
        Create a new booking with seats on hold

        Args:
            user_id: ID of the user making the booking
            showtime_id: ID of the showtime
            seats: List of seat dictionaries with 'row' and 'col'
            created_by: ID of the user creating this record

        Returns:
            tuple: (booking object, error message or None)
        """
        try:
            # Validate seats availability
            is_available, message = SeatService.check_seats_availability(showtime_id, seats)
            if not is_available:
                return None, message

            # Create booking
            booking = Booking(user_id=user_id, showtime_id=showtime_id, created_by=created_by)
            db.session.add(booking)
            db.session.flush()  # Get booking_id

            # Add seats
            for seat in seats:
                booked_seat = BookedSeat(
                    booking_id=booking.booking_id,
                    showtime_id=showtime_id,
                    seat_row=seat['row'],
                    seat_col=seat['col']
                )
                db.session.add(booked_seat)

            # Update showtime seats count
            showtime = Showtime.query.get(showtime_id)
            if showtime:
                showtime.increment_booked_seats(len(seats))

            db.session.commit()
            logger.info(f"Booking created: {booking.booking_id} for user {user_id}")
            return booking, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating booking: {str(e)}")
            return None, f"Failed to create booking: {str(e)}"

    @staticmethod
    def get_booking(booking_id, include_deleted=False):
        """Get booking by ID"""
        query = Booking.query.filter_by(booking_id=booking_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.first()

    @staticmethod
    def get_user_bookings(user_id, include_cancelled=False):
        """Get all bookings for a user"""
        query = Booking.query.filter_by(user_id=user_id, is_deleted=False)
        if not include_cancelled:
            query = query.filter(Booking.status != 'cancelled')
        return query.order_by(Booking.booking_time.desc()).all()

    @staticmethod
    def confirm_booking(booking_id, payment_id):
        """
        Confirm a booking after successful payment

        Args:
            booking_id: ID of the booking
            payment_id: ID of the completed payment

        Returns:
            tuple: (success boolean, message)
        """
        try:
            booking = BookingService.get_booking(booking_id)
            if not booking:
                return False, "Booking not found"

            if booking.status != 'pending':
                return False, f"Booking is already {booking.status}"

            # Verify payment
            payment = PaymentService.get_payment(payment_id)
            if not payment or payment.status != 'completed':
                return False, "Invalid or incomplete payment"

            # Update booking
            booking.payment_id = payment_id
            booking.confirm()

            # Confirm all seats
            for seat in booking.booked_seats.filter_by(is_deleted=False).all():
                seat.confirm()

            db.session.commit()
            logger.info(f"Booking confirmed: {booking_id}")
            return True, "Booking confirmed successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error confirming booking: {str(e)}")
            return False, f"Failed to confirm booking: {str(e)}"

    @staticmethod
    def cancel_booking(booking_id):
        """
        Cancel a booking and release seats

        Args:
            booking_id: ID of the booking to cancel

        Returns:
            tuple: (success boolean, message)
        """
        try:
            booking = BookingService.get_booking(booking_id)
            if not booking:
                return False, "Booking not found"

            if booking.status == 'cancelled':
                return False, "Booking is already cancelled"

            # Cancel booking and release seats
            seats_count = booking.booked_seats.filter_by(is_deleted=False).count()
            booking.cancel()

            # Update showtime seats count
            showtime = Showtime.query.get(booking.showtime_id)
            if showtime:
                showtime.decrement_booked_seats(seats_count)

            # Refund payment if exists
            if booking.payment_id:
                PaymentService.refund_payment(booking.payment_id)

            db.session.commit()
            logger.info(f"Booking cancelled: {booking_id}")
            return True, "Booking cancelled successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling booking: {str(e)}")
            return False, f"Failed to cancel booking: {str(e)}"

    @staticmethod
    def release_expired_holds():
        """Release seats with expired hold times"""
        try:
            expired_seats = BookedSeat.query.filter(
                BookedSeat.status == 'on_hold',
                BookedSeat.hold_expiry_time < datetime.utcnow(),
                BookedSeat.is_deleted == False
            ).all()

            booking_ids = set()
            for seat in expired_seats:
                booking_ids.add(seat.booking_id)
                seat.release()

            # Cancel associated bookings
            for booking_id in booking_ids:
                booking = Booking.query.get(booking_id)
                if booking and booking.status == 'pending':
                    booking.cancel()

            db.session.commit()
            logger.info(f"Released {len(expired_seats)} expired seat holds")
            return len(expired_seats)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error releasing expired holds: {str(e)}")
            return 0