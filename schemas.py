"""
Pydantic schemas for request/response validation
FastAPI uses these for automatic validation and documentation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# ============================================================================
# SEAT SCHEMAS
# ============================================================================

class SeatBase(BaseModel):
    """Base seat schema"""
    row: str = Field(..., description="Seat row (A-Z)")
    col: int = Field(..., gt=0, description="Seat column number (positive integer)")

    @validator('row')
    def validate_row(cls, v):
        if not v or len(v) != 1 or not v.isalpha():
            raise ValueError('Row must be a single letter (A-Z)')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "row": "A",
                "col": 1
            }
        }

class SeatResponse(SeatBase):
    """Seat response with booking details"""
    booked_seat_id: int
    booking_id: int
    showtime_id: int
    status: str
    hold_expiry_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# BOOKING SCHEMAS
# ============================================================================

class BookingCreate(BaseModel):
    """Schema for creating a new booking"""
    user_id: int = Field(..., gt=0, description="User ID")
    showtime_id: int = Field(..., gt=0, description="Showtime ID")
    seats: List[SeatBase] = Field(..., min_length=1, max_length=10, description="List of seats to book (max 10)")

    @validator('seats')
    def validate_seats_unique(cls, v):
        # Check for duplicate seats
        seat_set = set((seat.row, seat.col) for seat in v)
        if len(seat_set) != len(v):
            raise ValueError('Duplicate seats are not allowed')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "showtime_id": 1,
                "seats": [
                    {"row": "A", "col": 1},
                    {"row": "A", "col": 2}
                ]
            }
        }

class BookingResponse(BaseModel):
    """Schema for booking response"""
    booking_id: int
    user_id: int
    showtime_id: int
    payment_id: Optional[int] = None
    booking_time: datetime
    status: str
    seats: List[SeatResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingConfirm(BaseModel):
    """Schema for confirming a booking"""
    payment_id: int = Field(..., gt=0, description="Payment ID")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": 1
            }
        }

# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentCreate(BaseModel):
    """Schema for creating a payment"""
    amount: float = Field(..., gt=0, le=100000, description="Payment amount")
    created_by: Optional[int] = Field(None, gt=0, description="User creating the payment")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 20.00,
                "created_by": 1
            }
        }

class PaymentResponse(BaseModel):
    """Schema for payment response"""
    payment_id: int
    amount: float
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SHOWTIME/SEAT AVAILABILITY SCHEMAS
# ============================================================================

class SeatAvailabilityCheck(BaseModel):
    """Schema for checking seat availability"""
    seats: List[SeatBase] = Field(..., min_length=1, description="Seats to check")

    class Config:
        json_schema_extra = {
            "example": {
                "seats": [
                    {"row": "A", "col": 1},
                    {"row": "A", "col": 2}
                ]
            }
        }

class SeatAvailabilityResponse(BaseModel):
    """Schema for seat availability response"""
    available: bool
    message: str

class SeatMapItem(BaseModel):
    """Individual seat in seat map"""
    row: str
    col: int
    available: bool

class SeatMapResponse(BaseModel):
    """Schema for seat map response"""
    showtime_id: int
    seat_map: dict[str, List[SeatMapItem]]

class ExtendHoldRequest(BaseModel):
    """Schema for extending seat hold"""
    additional_minutes: int = Field(default=5, ge=1, le=30, description="Additional minutes to extend (1-30)")

    class Config:
        json_schema_extra = {
            "example": {
                "additional_minutes": 5
            }
        }

# ============================================================================
# GENERIC RESPONSE SCHEMAS
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str

class BookingCompleteResponse(BaseModel):
    """Response for complete booking operation"""
    message: str
    booking: BookingResponse
    payment: PaymentResponse

class UserBookingsResponse(BaseModel):
    """Response for user bookings"""
    bookings: List[BookingResponse]

class ShowtimeSeatsResponse(BaseModel):
    """Response for showtime seats"""
    showtime_id: int
    booked_seats: List[SeatResponse]