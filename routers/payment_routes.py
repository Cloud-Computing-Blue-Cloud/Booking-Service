"""
FastAPI router for payment endpoints
"""

from fastapi import APIRouter, HTTPException, status
from schemas import PaymentCreate, PaymentResponse, MessageResponse
from services.payment_service import PaymentService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payment",
    description="Create a new payment record"
)
async def create_payment(payment: PaymentCreate):
    """
    Create a new payment.

    - **amount**: Payment amount (must be positive)
    - **created_by**: User ID creating the payment (optional)
    """
    try:
        payment_obj, error = PaymentService.create_payment(
            amount=payment.amount,
            created_by=payment.created_by
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "message": "Payment created successfully",
            "payment": payment_obj.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{payment_id}",
    response_model=dict,
    summary="Get payment details",
    description="Retrieve payment information by ID"
)
async def get_payment(payment_id: int):
    """
    Get payment details.

    Returns payment information including amount, status, and timestamps.
    """
    try:
        payment = PaymentService.get_payment(payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        return {"payment": payment.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{payment_id}/process",
    response_model=MessageResponse,
    summary="Process payment",
    description="Process a pending payment (simulated gateway)"
)
async def process_payment(payment_id: int):
    """
    Process a payment.

    In production, this would integrate with a payment gateway
    like Stripe, PayPal, etc. Currently simulated.
    """
    try:
        success, message = PaymentService.process_payment(payment_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{payment_id}/fail",
    response_model=MessageResponse,
    summary="Mark payment as failed",
    description="Mark a payment as failed"
)
async def fail_payment(payment_id: int):
    """
    Mark payment as failed.

    Used when payment processing fails.
    """
    try:
        success, message = PaymentService.fail_payment(payment_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fail_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/{payment_id}/refund",
    response_model=MessageResponse,
    summary="Refund payment",
    description="Refund a completed payment"
)
async def refund_payment(payment_id: int):
    """
    Refund a payment.

    Only completed payments can be refunded.
    """
    try:
        success, message = PaymentService.refund_payment(payment_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refund_payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )