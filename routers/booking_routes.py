"""
FastAPI router for booking endpoints
"""

from fastapi import APIRouter, HTTPException, status
from schemas import (
    BookingCreate, BookingResponse, BookingUpdate,
    MessageResponse, UserBookingsResponse
)
from services.booking_service import BookingService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new booking",
    description="Create a new booking with seat reservations. Returns immediately with booking ID."
)
def create_booking(booking: BookingCreate):
    """
    Create a new booking (HTTP 202 Accepted).

    This endpoint returns immediately with a booking ID while the seat reservation
    is processed. Use GET /api/bookings/{id} to check the booking status.

    - **user_id**: ID of the user making the booking
    - **showtime_id**: ID of the showtime
    - **seats**: List of seats to book (maximum 10 seats)

    Returns HTTP 202 with booking reference. Poll GET /api/bookings/{id} to check status.
    Seats will be held for 10 minutes.
    """
    try:
        # Convert Pydantic models to dicts
        seats = [{"row": seat.row, "col": seat.col} for seat in booking.seats]

        # TODO: Get created_by from authenticated user context
        created_by = 1  # Hardcoded for now, should be from auth

        # Create booking
        booking_obj, error = BookingService.create_booking(
            user_id=booking.user_id,
            showtime_id=booking.showtime_id,
            seats=seats,
            created_by=created_by
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Return 202 Accepted with booking reference
        return {
            "message": "Booking request accepted and is being processed",
            "booking_id": booking_obj.booking_id,
            "status": "processing",
            "poll_url": f"/api/bookings/{booking_obj.booking_id}",
            "estimated_completion": "10 seconds"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{booking_id}",
    response_model=dict,
    summary="Get booking details",
    description="Retrieve details of a specific booking by ID"
)
def get_booking(booking_id: int):
    """
    Get booking details including:
    - Booking information
    - Seat details
    - Payment information (if exists)
    """
    try:
        booking = BookingService.get_booking(booking_id)

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        return {"booking": booking.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_booking: {str(e)}")

@router.get(
    "/showtime/{showtime_id}/seats",
    response_model=dict,
    summary="Get booked seats for showtime",
    description="Retrieve all booked and held seats for a specific showtime"
)
def get_showtime_seats(showtime_id: int):
    """
    Get list of booked seats for a showtime.
    Used by the UI to render the seat grid.
    """
    try:
        seats = BookingService.get_showtime_seats(showtime_id)
        return {"seats": seats}
    except Exception as e:
        logger.error(f"Error in get_showtime_seats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/user/{user_id}",
    response_model=UserBookingsResponse,
    summary="Get user's bookings",
    description="Retrieve all bookings for a specific user"
)
def get_user_bookings(
    user_id: int,
    include_cancelled: bool = False
):
    """
    Get all bookings for a user.

    - **user_id**: ID of the user
    - **include_cancelled**: Include cancelled bookings (default: false)
    """
    try:
        bookings = BookingService.get_user_bookings(user_id, include_cancelled)

        return {
            "bookings": [booking.to_dict() for booking in bookings]
        }

    except Exception as e:
        logger.error(f"Error in get_user_bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put(
    "/{booking_id}",
    response_model=dict,
    summary="Update booking",
    description="Update booking details (status, payment_id)"
)
def update_booking(booking_id: int, booking_update: BookingUpdate):
    """
    Update a booking.
    
    This is the primary endpoint for state transitions:
    - Confirming a booking (status='confirmed', payment_id=...)
    - Failing a booking (status='failed')
    - Cancelling a booking (status='cancelled')

    - **booking_id**: ID of the booking to update
    - **status**: New status (pending, confirmed, cancelled, failed) - optional
    - **payment_id**: Payment ID to associate with booking - optional

    Only provided fields will be updated.
    """
    try:
        success, result = BookingService.update_booking(
            booking_id,
            status=booking_update.status,
            payment_id=booking_update.payment_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )

        # Result is either a message (if failed) or booking object (if success)
        # Wait, update_booking returns (success, booking/message)
        # If success, result is booking object.
        
        return {
            "message": "Booking updated successfully",
            "booking": result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/{booking_id}",
    response_model=MessageResponse,
    summary="Delete booking",
    description="Soft delete a booking and release seats"
)
def delete_booking_endpoint(booking_id: int):
    """
    Delete a booking (soft delete).

    This will:
    - Soft delete the booking record
    - Release all held/booked seats
    - Update showtime seat counts
    - Refund payment if exists

    The booking will be marked as deleted but not removed from the database.
    """
    try:
        success, message = BookingService.delete_booking(booking_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_booking_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )