"""
FastAPI router for booking endpoints
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import asyncio
import random
from schemas import (
    BookingCreate, BookingResponse, BookingUpdate,
    MessageResponse, UserBookingsResponse
)
from services.booking_service import BookingService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def simulate_payment_processing(booking_id: int):
    """
    Simulate payment processing delay and auto-confirm booking.
    This is for demonstration purposes to support UI polling.
    """
    try:
        from models.payment import Payment
        from database import db
        import requests
        from config import Config
        from datetime import datetime
        
        delay = random.randint(3, 10)
        logger.info(f"Starting payment simulation for booking {booking_id} with {delay}s delay")
        await asyncio.sleep(delay)
        
        # 1. Get booking details to calculate amount
        booking = BookingService.get_booking(booking_id)
        if not booking:
            logger.error(f"Booking {booking_id} not found for payment simulation")
            return

        # 2. Get showtime price
        price_per_seat = 10.00 # fallback
        try:
            theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
            resp = requests.get(f"{theatre_url}/showtimes/{booking.showtime_id}", timeout=5)
            if resp.status_code == 200:
                showtime_data = resp.json()
                price_per_seat = showtime_data.get('price', 10.00)
        except Exception as e:
            logger.warning(f"Could not fetch showtime price: {e}. Using default.")

        # 3. Calculate total amount
        seat_count = booking.booked_seats.filter_by(is_deleted=False).count()
        total_amount = float(price_per_seat) * seat_count

        # Mock payment ID (e.g. 999 + booking_id)
        mock_payment_id = 999000 + booking_id
        
        # 4. Create dummy payment record
        # Check if it exists first to be safe (idempotency)
        existing_payment = db.session.query(Payment).filter_by(payment_id=mock_payment_id).first()
        if not existing_payment:
            payment = Payment(amount=total_amount, created_by=booking.user_id)
            payment.payment_id = mock_payment_id
            payment.status = 'completed'
            payment.updated_at = datetime.utcnow()
            db.session.add(payment)
            db.session.commit()
            logger.info(f"Created mock payment {mock_payment_id} for booking {booking_id}")
        
        success, result = BookingService.update_booking(
            booking_id,
            status='confirmed',
            payment_id=mock_payment_id
        )
        
        if success:
            logger.info(f"Payment simulation successful for booking {booking_id}")
            
            # --- Pub/Sub Integration ---
            try:
                import json
                from google.cloud import pubsub_v1
                
                # Fetch detailed info for the event
                movie_title = "Unknown Movie"
                start_time = "Unknown Time"
                user_email = "unknown@example.com"
                
                # 1. Fetch User Email
                try:
                    user_url = Config.USER_SERVICE_URL.rstrip("/")
                    u_resp = requests.get(f"{user_url}/users/{booking.user_id}", timeout=5)
                    if u_resp.status_code == 200:
                        user_data = u_resp.json()
                        user_email = user_data.get('email', user_email)
                    else:
                        logger.warning(f"Failed to fetch user {booking.user_id}: {u_resp.status_code}")
                except Exception as e:
                    logger.warning(f"Could not fetch user email: {e}")

                # We already have showtime_data from price fetch?
                # If not, fetch it again or move the fetch up scope
                if 'showtime_data' not in locals():
                    try:
                        theatre_url = Config.THEATRE_SERVICE_URL.rstrip("/")
                        resp = requests.get(f"{theatre_url}/showtimes/{booking.showtime_id}", timeout=5)
                        if resp.status_code == 200:
                            showtime_data = resp.json()
                    except:
                        showtime_data = {}

                if 'showtime_data' in locals():
                    start_time = showtime_data.get('start_time', start_time)
                    movie_id = showtime_data.get('movie_id')
                    
                    if movie_id:
                        try:
                            movie_url = Config.MOVIE_SERVICE_URL.rstrip("/")
                            m_resp = requests.get(f"{movie_url}/movies/{movie_id}", timeout=5)
                            if m_resp.status_code == 200:
                                movie_title = m_resp.json().get('title', movie_title)
                        except Exception as e:
                            logger.warning(f"Could not fetch movie title: {e}")

                # Prepare event data
                event_data = {
                    "booking_id": booking_id,
                    "email": user_email,
                    "movie": movie_title,
                    "showtime": start_time,
                    "amount": float(total_amount),
                    "status": "confirmed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Publish
                project_id = Config.GOOGLE_CLOUD_PROJECT
                topic_id = Config.PUBSUB_TOPIC_ID
                
                if project_id and topic_id and project_id != 'your-project-id':
                    publisher = pubsub_v1.PublisherClient()
                    topic_path = publisher.topic_path(project_id, topic_id)
                    message_bytes = json.dumps(event_data).encode("utf-8")
                    future = publisher.publish(topic_path, message_bytes)
                    logger.info(f"Event published to topic {topic_id}! Message ID: {future.result()}")
                else:
                    logger.warning("Pub/Sub project/topic not configured, skipping publish")
                    
            except Exception as e:
                logger.error(f"Failed to publish to Pub/Sub: {e}")
            # ---------------------------

        else:
            logger.error(f"Payment simulation failed for booking {booking_id}: {result}")
            
    except Exception as e:
        logger.error(f"Error in payment simulation for booking {booking_id}: {str(e)}")

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new booking",
    description="Create a new booking with seat reservations. Returns immediately with booking ID."
)
def create_booking(booking: BookingCreate, background_tasks: BackgroundTasks):
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
        
        # Schedule background payment simulation
        background_tasks.add_task(simulate_payment_processing, booking_obj.booking_id)

        return {
            "message": "Booking request accepted and is being processed",
            "booking_id": booking_obj.booking_id,
            "status": "processing",
            "poll_url": f"/api/bookings/{booking_obj.booking_id}",
            "estimated_completion": "3-10 seconds"
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