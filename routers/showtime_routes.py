"""
FastAPI router for showtime/seat endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query
from schemas import (
    SeatAvailabilityCheck, SeatAvailabilityResponse,
    SeatMapResponse, ExtendHoldRequest, MessageResponse,
    ShowtimeSeatsResponse, BookedSeatUpdate
)
from services.seat_service import SeatService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/{showtime_id}/seats",
    response_model=ShowtimeSeatsResponse,
    summary="Get booked seats",
    description="Get all booked seats for a showtime"
)
async def get_booked_seats(showtime_id: int):
    """
    Get all booked seats for a showtime.

    Returns seats that are currently on hold or permanently booked.
    Automatically filters out expired holds.
    """
    try:
        seats = SeatService.get_booked_seats(showtime_id)

        return {
            "showtime_id": showtime_id,
            "booked_seats": [seat.to_dict() for seat in seats]
        }

    except Exception as e:
        logger.error(f"Error in get_booked_seats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{showtime_id}/seat-map",
    response_model=SeatMapResponse,
    summary="Get seat map",
    description="Get seat availability map for a showtime"
)
async def get_seat_map(
    showtime_id: int,
    rows: str = Query(default="A,B,C,D,E,F,G,H", description="Comma-separated row letters"),
    cols: int = Query(default=10, ge=1, le=50, description="Number of columns (1-50)")
):
    """
    Get seat map with availability status.

    - **showtime_id**: ID of the showtime
    - **rows**: Comma-separated row letters (e.g., "A,B,C,D")
    - **cols**: Number of columns per row

    Returns a map showing which seats are available and which are booked.
    """
    try:
        row_list = [row.strip().upper() for row in rows.split(",")]

        seat_map = SeatService.get_seat_map(showtime_id, row_list, cols)

        return {
            "showtime_id": showtime_id,
            "seat_map": seat_map
        }

    except Exception as e:
        logger.error(f"Error in get_seat_map: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{showtime_id}/check-availability",
    response_model=SeatAvailabilityResponse,
    summary="Check seat availability",
    description="Check if specific seats are available"
)
async def check_seat_availability(
    showtime_id: int,
    check: SeatAvailabilityCheck
):
    """
    Check if specific seats are available for booking.

    Returns whether all requested seats are available.
    """
    try:
        seats = [{"row": seat.row, "col": seat.col} for seat in check.seats]

        is_available, message = SeatService.check_seats_availability(
            showtime_id,
            seats
        )

        return {
            "available": is_available,
            "message": message
        }

    except Exception as e:
        logger.error(f"Error in check_seat_availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/booking/{booking_id}/extend-hold",
    response_model=MessageResponse,
    summary="Extend seat hold",
    description="Extend the hold time for seats in a booking"
)
async def extend_seat_hold(
    booking_id: int,
    extend: ExtendHoldRequest = ExtendHoldRequest()
):
    """
    Extend the hold time for seats.

    - **booking_id**: ID of the booking
    - **additional_minutes**: Additional minutes to extend (1-30, default: 5)

    Useful when customer needs more time during checkout.
    """
    try:
        success, message = SeatService.extend_seat_hold(
            booking_id,
            extend.additional_minutes
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
        logger.error(f"Error in extend_seat_hold: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put(
    "/seats/{booked_seat_id}",
    response_model=dict,
    summary="Update booked seat",
    description="Update a booked seat (status, extend hold)"
)
async def update_booked_seat(booked_seat_id: int, seat_update: BookedSeatUpdate):
    """
    Update a booked seat.

    - **booked_seat_id**: ID of the booked seat to update
    - **status**: New status (on_hold, booked, released) - optional
    - **additional_minutes**: Additional minutes to extend hold (1-30) - optional

    Only provided fields will be updated.
    """
    try:
        success, result = SeatService.update_booked_seat(
            booked_seat_id,
            status=seat_update.status,
            additional_minutes=seat_update.additional_minutes
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )

        return {
            "message": "Booked seat updated successfully",
            "seat": result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_booked_seat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/seats/{booked_seat_id}",
    response_model=MessageResponse,
    summary="Release booked seat",
    description="Release/delete a booked seat"
)
async def release_booked_seat(booked_seat_id: int):
    """
    Release a booked seat (soft delete).

    This will:
    - Release the seat (soft delete)
    - Update showtime seat counts if the seat was booked
    - Make the seat available for booking again
    """
    try:
        success, message = SeatService.delete_booked_seat(booked_seat_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in release_booked_seat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )