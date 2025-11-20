"""
FastAPI router for booking endpoints
"""

from fastapi import APIRouter, HTTPException, status
from schemas import (
    BookingCreate, BookingResponse, BookingConfirm, BookingUpdate,
    MessageResponse, BookingCompleteResponse, UserBookingsResponse
)
from services.booking_service import BookingService
from services.payment_service import PaymentService
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
async def create_booking(booking: BookingCreate):
    """
    Create a new booking asynchronously (HTTP 202 Accepted).

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

        # Create booking (in real async implementation, this would be queued)
        booking_obj, error = BookingService.create_booking(
            user_id=booking.user_id,
            showtime_id=booking.showtime_id,
            seats=seats,
            created_by=booking.user_id
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
async def get_booking(booking_id: int):
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
async def get_user_bookings(
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

@router.post(
    "/{booking_id}/confirm",
    response_model=MessageResponse,
    summary="Confirm booking",
    description="Confirm a booking after successful payment"
)
async def confirm_booking(booking_id: int, confirm: BookingConfirm):
    """
    Confirm a booking with a payment.

    - **booking_id**: ID of the booking to confirm
    - **payment_id**: ID of the completed payment
    """
    try:
        success, message = BookingService.confirm_booking(
            booking_id,
            confirm.payment_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in confirm_booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{booking_id}/cancel",
    response_model=MessageResponse,
    summary="Cancel booking",
    description="Cancel a booking and release seats"
)
async def cancel_booking(booking_id: int):
    """
    Cancel a booking.

    This will:
    - Update booking status to 'cancelled'
    - Release all held/booked seats
    - Refund payment if exists
    """
    try:
        success, message = BookingService.cancel_booking(booking_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cancel_booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{booking_id}/complete",
    response_model=BookingCompleteResponse,
    summary="Complete booking",
    description="One-step: Create payment, process it, and confirm booking"
)
async def complete_booking(booking_id: int):
    """
    Complete booking in one step:

    1. Calculate booking amount
    2. Create payment
    3. Process payment
    4. Confirm booking

    Returns the completed booking and payment details.
    """
    try:
        # Get booking
        booking = BookingService.get_booking(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Calculate amount
        num_seats = booking.booked_seats.filter_by(is_deleted=False).count()
        amount = PaymentService.calculate_booking_amount(num_seats)

        # Create payment
        payment, error = PaymentService.create_payment(amount, booking.user_id)
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Process payment
        success, message = PaymentService.process_payment(payment.payment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # Confirm booking
        success, message = BookingService.confirm_booking(
            booking_id,
            payment.payment_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {
            "message": "Booking completed successfully",
            "booking": booking.to_dict(),
            "payment": payment.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_booking: {str(e)}")
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
async def update_booking(booking_id: int, booking_update: BookingUpdate):
    """
    Update a booking.

    - **booking_id**: ID of the booking to update
    - **status**: New status (pending, confirmed, cancelled) - optional
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
async def delete_booking_endpoint(booking_id: int):
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