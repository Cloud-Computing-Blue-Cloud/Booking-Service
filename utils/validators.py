import re

def validate_booking_request(data):
    """
    Validate booking request data

    Args:
        data: Request data dictionary

    Returns:
        tuple: (is_valid boolean, error message or None)
    """
    if not data:
        return False, "Request body is required"

    required_fields = ['user_id', 'showtime_id', 'seats']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate user_id
    if not isinstance(data['user_id'], int) or data['user_id'] <= 0:
        return False, "Invalid user_id"

    # Validate showtime_id
    if not isinstance(data['showtime_id'], int) or data['showtime_id'] <= 0:
        return False, "Invalid showtime_id"

    # Validate seats
    if not isinstance(data['seats'], list) or len(data['seats']) == 0:
        return False, "Seats must be a non-empty list"

    if len(data['seats']) > 10:
        return False, "Cannot book more than 10 seats at once"

    return True, None

def validate_seat_format(seat):
    """
    Validate seat format

    Args:
        seat: Seat dictionary with 'row' and 'col'

    Returns:
        boolean: True if valid, False otherwise
    """
    if not isinstance(seat, dict):
        return False

    if 'row' not in seat or 'col' not in seat:
        return False

    # Validate row (should be a letter A-Z)
    if not isinstance(seat['row'], str) or not re.match(r'^[A-Z]$', seat['row']):
        return False

    # Validate col (should be a positive integer)
    if not isinstance(seat['col'], int) or seat['col'] <= 0:
        return False

    return True

def validate_payment_amount(amount):
    """
    Validate payment amount

    Args:
        amount: Payment amount

    Returns:
        tuple: (is_valid boolean, error message or None)
    """
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return False, "Amount must be greater than 0"
        if amount_float > 100000:
            return False, "Amount exceeds maximum limit"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid amount format"

def validate_showtime_id(showtime_id):
    """
    Validate showtime ID

    Args:
        showtime_id: Showtime ID to validate

    Returns:
        tuple: (is_valid boolean, error message or None)
    """
    if not isinstance(showtime_id, int) or showtime_id <= 0:
        return False, "Invalid showtime ID"
    return True, None