from database import db
from models.booking import Booking
from models.booked_seat import BookedSeat

from services.seat_service import SeatService
from services.payment_service import PaymentService
from datetime import datetime
import logging
import requests
from config import Config

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
            # Validate showtime exists in TheatreService
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            try:
                resp = requests.get(f"{theatre_url}/showtimes/{showtime_id}", timeout=5)
            except requests.RequestException as exc:
                return None, f"Theatre service unavailable: {exc}"

            if resp.status_code == 404:
                return None, f"Showtime {showtime_id} not found"
            if resp.status_code >= 400:
                return None, f"Theatre service error: {resp.status_code}"

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
                    seat_col=seat['col'],
                    created_by=created_by
                )
                db.session.add(booked_seat)

            # Commit booking and seat holds (do NOT increment theatre's booked count yet)
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
    def get_showtime_seats(showtime_id):
        """
        Get all booked/held seats for a showtime
        
        Args:
            showtime_id: ID of the showtime
            
        Returns:
            list: List of dicts with seat info
        """
        seats = BookedSeat.query.filter_by(
            showtime_id=showtime_id, 
            is_deleted=False
        ).all()
        
        return [
            {
                "row": seat.seat_row,
                "col": seat.seat_col,
                "status": seat.status,
                "booking_id": seat.booking_id
            }
            for seat in seats
        ]

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

            # Calculate number of seats to confirm
            seats = booking.booked_seats.filter_by(is_deleted=False).all()
            num_seats = len(seats)

            # Attempt to increment booked seats in TheatreService first
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            try:
                resp = requests.post(
                    f"{theatre_url}/showtimes/{booking.showtime_id}/seats",
                    json={"count": num_seats},
                    timeout=5
                )
            except requests.RequestException as exc:
                db.session.rollback()
                return False, f"Theatre service unavailable: {exc}"

            if resp.status_code >= 400:
                db.session.rollback()
                return False, f"Failed to update theatre showtime seats: {resp.status_code}"

            # Update booking locally and confirm seats
            booking.payment_id = payment_id
            booking.confirm()
            for seat in seats:
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

            # Attempt to decrement booked seats in TheatreService if seats were previously confirmed
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            try:
                # send negative count to release
                resp = requests.post(
                    f"{theatre_url}/showtimes/{booking.showtime_id}/seats",
                    json={"count": -seats_count},
                    timeout=5
                )
                if resp.status_code >= 400:
                    logger.warning(f"Failed to update theatre seats on cancel: {resp.status_code}")
            except requests.RequestException:
                logger.warning("Could not reach theatre service to update seats on cancel")

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
    def fail_booking(booking_id):
        """
        Mark a booking as failed and release seats (used for payment failure)

        Args:
            booking_id: ID of the booking to fail

        Returns:
            tuple: (success boolean, message)
        """
        try:
            booking = BookingService.get_booking(booking_id)
            if not booking:
                return False, "Booking not found"

            if booking.status == 'failed':
                return False, "Booking is already failed"

            # Fail booking and release seats
            seats_count = booking.booked_seats.filter_by(is_deleted=False).count()
            
            booking.status = 'failed'
            booking.updated_at = datetime.utcnow()
            
            # Release seats
            for seat in booking.booked_seats.filter_by(is_deleted=False).all():
                seat.release()

            # Attempt to decrement booked seats in TheatreService
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            try:
                # send negative count to release
                resp = requests.post(
                    f"{theatre_url}/showtimes/{booking.showtime_id}/seats",
                    json={"count": -seats_count},
                    timeout=5
                )
                if resp.status_code >= 400:
                    logger.warning(f"Failed to update theatre seats on failure: {resp.status_code}")
            except requests.RequestException:
                logger.warning("Could not reach theatre service to update seats on failure")

            db.session.commit()
            logger.info(f"Booking failed: {booking_id}")
            return True, "Booking marked as failed successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error failing booking: {str(e)}")
            return False, f"Failed to fail booking: {str(e)}"

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

    @staticmethod
    def update_booking(booking_id, status=None, payment_id=None):
        """
        Update a booking

        Args:
            booking_id: ID of the booking to update
            status: New status (optional)
            payment_id: Payment ID to associate (optional)

        Returns:
            tuple: (success boolean, message or booking object)
        """
        try:
            booking = BookingService.get_booking(booking_id)
            if not booking:
                return False, "Booking not found"



            if payment_id:
                booking.payment_id = payment_id
                booking.updated_at = datetime.utcnow()
                db.session.flush()

            if status:
                valid_statuses = ['pending', 'confirmed', 'cancelled', 'failed']
                if status not in valid_statuses:
                    return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                
                # Handle status transitions with side effects
                if status == 'confirmed' and booking.status != 'confirmed':
                    # Use internal confirm logic
                    # We need to pass payment_id if it was just updated
                    current_payment_id = payment_id or booking.payment_id
                    if not current_payment_id:
                        return False, "Cannot confirm booking without payment ID"
                    return BookingService.confirm_booking(booking_id, current_payment_id)
                
                elif status == 'failed' and booking.status != 'failed':
                    return BookingService.fail_booking(booking_id)
                
                elif status == 'cancelled' and booking.status != 'cancelled':
                    return BookingService.cancel_booking(booking_id)
                
                else:
                    # Just update status if no specific transition logic needed (e.g. back to pending?)
                    booking.status = status
                    booking.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Booking updated: {booking_id}")
            return True, booking

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating booking: {str(e)}")
            return False, f"Failed to update booking: {str(e)}"

    @staticmethod
    def delete_booking(booking_id):
        """
        Soft delete a booking

        Args:
            booking_id: ID of the booking to delete

        Returns:
            tuple: (success boolean, message)
        """
        try:
            booking = BookingService.get_booking(booking_id, include_deleted=True)
            if not booking:
                return False, "Booking not found"

            if booking.is_deleted:
                return False, "Booking is already deleted"

            # Soft delete the booking
            booking.soft_delete()
            booking.updated_at = datetime.utcnow()

            # Release all seats
            seats_count = booking.booked_seats.filter_by(is_deleted=False).count()
            for seat in booking.booked_seats.filter_by(is_deleted=False).all():
                seat.release()

            # Attempt to decrement booked seats in TheatreService (best-effort)
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            try:
                resp = requests.post(
                    f"{theatre_url}/showtimes/{booking.showtime_id}/seats",
                    json={"count": -seats_count},
                    timeout=5
                )
                if resp.status_code >= 400:
                    logger.warning(f"Failed to update theatre seats on delete: {resp.status_code}")
            except requests.RequestException:
                logger.warning("Could not reach theatre service to update seats on delete")

            db.session.commit()
            logger.info(f"Booking deleted: {booking_id}")
            return True, "Booking deleted successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting booking: {str(e)}")
            return False, f"Failed to delete booking: {str(e)}"