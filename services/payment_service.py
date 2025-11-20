from database import db
from models.payment import Payment
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    def create_payment(amount, created_by=None):
        """
        Create a new payment record

        Args:
            amount: Payment amount
            created_by: ID of the user creating this record

        Returns:
            tuple: (payment object, error message or None)
        """
        try:
            if amount <= 0:
                return None, "Invalid payment amount"

            payment = Payment(amount=amount, created_by=created_by)
            db.session.add(payment)
            db.session.commit()

            logger.info(f"Payment created: {payment.payment_id}")
            return payment, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating payment: {str(e)}")
            return None, f"Failed to create payment: {str(e)}"

    @staticmethod
    def get_payment(payment_id):
        """Get payment by ID"""
        return Payment.query.filter_by(payment_id=payment_id, is_deleted=False).first()

    @staticmethod
    def process_payment(payment_id):
        """
        Process a payment (simulate payment gateway)

        Args:
            payment_id: ID of the payment to process

        Returns:
            tuple: (success boolean, message)
        """
        try:
            payment = PaymentService.get_payment(payment_id)
            if not payment:
                return False, "Payment not found"

            if payment.status != 'pending':
                return False, f"Payment is already {payment.status}"

            # Simulate payment processing
            # In real implementation, this would integrate with payment gateway
            payment.complete()
            db.session.commit()

            logger.info(f"Payment processed: {payment_id}")
            return True, "Payment completed successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing payment: {str(e)}")
            return False, f"Failed to process payment: {str(e)}"

    @staticmethod
    def fail_payment(payment_id):
        """
        Mark payment as failed

        Args:
            payment_id: ID of the payment

        Returns:
            tuple: (success boolean, message)
        """
        try:
            payment = PaymentService.get_payment(payment_id)
            if not payment:
                return False, "Payment not found"

            payment.fail()
            db.session.commit()

            logger.info(f"Payment failed: {payment_id}")
            return True, "Payment marked as failed"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error failing payment: {str(e)}")
            return False, f"Failed to update payment: {str(e)}"

    @staticmethod
    def refund_payment(payment_id):
        """
        Refund a payment

        Args:
            payment_id: ID of the payment to refund

        Returns:
            tuple: (success boolean, message)
        """
        try:
            payment = PaymentService.get_payment(payment_id)
            if not payment:
                return False, "Payment not found"

            if payment.status != 'completed':
                return False, "Only completed payments can be refunded"

            # Simulate refund processing
            payment.refund()
            db.session.commit()

            logger.info(f"Payment refunded: {payment_id}")
            return True, "Payment refunded successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error refunding payment: {str(e)}")
            return False, f"Failed to refund payment: {str(e)}"

    @staticmethod
    def calculate_booking_amount(num_seats, price_per_seat=10.00):
        """
        Calculate total booking amount

        Args:
            num_seats: Number of seats
            price_per_seat: Price per seat (default: 10.00)

        Returns:
            float: Total amount
        """
        return num_seats * price_per_seat

    @staticmethod
    def update_payment(payment_id, amount=None, status=None):
        """
        Update a payment

        Args:
            payment_id: ID of the payment to update
            amount: New amount (optional)
            status: New status (optional)

        Returns:
            tuple: (success boolean, message or payment object)
        """
        from decimal import Decimal
        from datetime import datetime

        try:
            payment = PaymentService.get_payment(payment_id)
            if not payment:
                return False, "Payment not found"

            if amount is not None:
                if amount <= 0:
                    return False, "Invalid payment amount"
                payment.amount = Decimal(str(amount))
                payment.updated_at = datetime.utcnow()

            if status:
                valid_statuses = ['pending', 'completed', 'failed', 'refunded']
                if status not in valid_statuses:
                    return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                payment.status = status
                payment.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Payment updated: {payment_id}")
            return True, payment

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating payment: {str(e)}")
            return False, f"Failed to update payment: {str(e)}"

    @staticmethod
    def delete_payment(payment_id):
        """
        Soft delete a payment

        Args:
            payment_id: ID of the payment to delete

        Returns:
            tuple: (success boolean, message)
        """
        from datetime import datetime

        try:
            payment = Payment.query.filter_by(payment_id=payment_id).first()
            if not payment:
                return False, "Payment not found"

            if payment.is_deleted:
                return False, "Payment is already deleted"

            # Soft delete the payment
            payment.soft_delete()
            payment.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Payment deleted: {payment_id}")
            return True, "Payment deleted successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting payment: {str(e)}")
            return False, f"Failed to delete payment: {str(e)}"