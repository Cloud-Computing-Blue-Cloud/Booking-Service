"""
FastAPI utility decorators and dependencies
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status

# Note: FastAPI handles request validation automatically via Pydantic
# These decorators are kept for reference but are largely unnecessary

def deprecated(reason: str = "This endpoint is deprecated"):
    """
    Decorator to mark endpoints as deprecated

    Usage:
        @app.get("/old-endpoint")
        @deprecated("Use /new-endpoint instead")
        async def old_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Could log deprecation warning here
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# FastAPI doesn't need these decorators as validation is automatic:
# - @require_json -> automatic with Pydantic models
# - @validate_params -> automatic with type hints
#
# Example:
# Instead of:
#   @validate_params('user_id', 'showtime_id')
#   def create_booking():
#       ...
#
# FastAPI does:
#   async def create_booking(booking: BookingCreate):
#       # booking.user_id and booking.showtime_id are automatically validated!
