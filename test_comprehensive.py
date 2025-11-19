"""
Comprehensive test suite for Booking Service
Tests all endpoints with various scenarios
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5003"

class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# ============================================================================
# HEALTH & CONNECTIVITY TESTS
# ============================================================================

def test_health():
    """Test 1: Health Check"""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)

        if response.status_code == 200:
            print_success("Service is healthy")
            return True
        else:
            print_error("Health check failed")
            return False
    except Exception as e:
        print_error(f"Cannot connect to service: {e}")
        return False

# ============================================================================
# BOOKING TESTS
# ============================================================================

def test_create_booking_success():
    """Test 2: Create Booking - Success"""
    print_test("Create Booking - Happy Path")
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [
            {"row": "A", "col": 5},
            {"row": "A", "col": 6}
        ]
    }

    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response)

    if response.status_code == 201:
        booking_id = response.json()['booking']['booking_id']
        print_success(f"Booking created successfully (ID: {booking_id})")
        return booking_id
    else:
        print_error("Failed to create booking")
        return None

def test_create_booking_invalid_user():
    """Test 3: Create Booking - Missing user_id"""
    print_test("Create Booking - Missing User ID")
    data = {
        "showtime_id": 1,
        "seats": [{"row": "B", "col": 1}]
    }

    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response)

    if response.status_code == 400:
        print_success("Correctly rejected request with missing user_id")
    else:
        print_error("Should have rejected request")

def test_create_booking_invalid_seats():
    """Test 4: Create Booking - Invalid Seat Format"""
    print_test("Create Booking - Invalid Seat Format")
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [{"row": "AA", "col": 1}]  # Invalid: row should be single letter
    }

    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response)

    if response.status_code == 400:
        print_success("Correctly rejected invalid seat format")
    else:
        print_error("Should have rejected invalid seat format")

def test_create_booking_too_many_seats():
    """Test 5: Create Booking - Too Many Seats"""
    print_test("Create Booking - Exceeds Maximum Seats")
    seats = [{"row": "C", "col": i} for i in range(1, 12)]  # 11 seats (max is 10)
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": seats
    }

    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print_response(response)

    if response.status_code == 400:
        print_success("Correctly rejected booking with too many seats")
    else:
        print_error("Should have rejected booking with >10 seats")

def test_create_booking_duplicate_seat():
    """Test 6: Create Booking - Duplicate Seat"""
    print_test("Create Booking - Same Seat Twice")

    # First booking
    data1 = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [{"row": "D", "col": 1}]
    }
    response1 = requests.post(f"{BASE_URL}/api/bookings/", json=data1)
    print_info("First booking:")
    print_response(response1)

    # Try to book same seat
    data2 = {
        "user_id": 2,
        "showtime_id": 1,
        "seats": [{"row": "D", "col": 1}]
    }
    response2 = requests.post(f"{BASE_URL}/api/bookings/", json=data2)
    print_info("\nSecond booking (should fail):")
    print_response(response2)

    if response2.status_code == 400:
        print_success("Correctly prevented double booking")
    else:
        print_error("Should have prevented double booking")

def test_get_booking(booking_id):
    """Test 7: Get Booking Details"""
    print_test(f"Get Booking Details (ID: {booking_id})")

    response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
    print_response(response)

    if response.status_code == 200:
        print_success("Successfully retrieved booking")
        return True
    else:
        print_error("Failed to retrieve booking")
        return False

def test_get_booking_not_found():
    """Test 8: Get Non-existent Booking"""
    print_test("Get Non-existent Booking")

    response = requests.get(f"{BASE_URL}/api/bookings/99999")
    print_response(response)

    if response.status_code == 404:
        print_success("Correctly returned 404 for non-existent booking")
    else:
        print_error("Should have returned 404")

def test_get_user_bookings():
    """Test 9: Get User Bookings"""
    print_test("Get All Bookings for User")

    response = requests.get(f"{BASE_URL}/api/bookings/user/1")
    print_response(response)

    if response.status_code == 200:
        count = len(response.json().get('bookings', []))
        print_success(f"Retrieved {count} booking(s) for user")
    else:
        print_error("Failed to retrieve user bookings")

# ============================================================================
# SEAT & SHOWTIME TESTS
# ============================================================================

def test_check_seat_availability():
    """Test 10: Check Seat Availability"""
    print_test("Check Seat Availability")

    data = {
        "seats": [
            {"row": "E", "col": 1},
            {"row": "E", "col": 2}
        ]
    }

    response = requests.post(
        f"{BASE_URL}/api/showtimes/1/check-availability",
        json=data
    )
    print_response(response)

    if response.status_code == 200:
        available = response.json().get('available')
        if available:
            print_success("Seats are available")
        else:
            print_info("Seats are not available (may be booked)")
    else:
        print_error("Failed to check availability")

def test_get_seat_map():
    """Test 11: Get Seat Map"""
    print_test("Get Seat Map")

    response = requests.get(
        f"{BASE_URL}/api/showtimes/1/seat-map?rows=A,B,C,D,E&cols=10"
    )
    print_response(response)

    if response.status_code == 200:
        print_success("Successfully retrieved seat map")
    else:
        print_error("Failed to retrieve seat map")

def test_get_booked_seats():
    """Test 12: Get Booked Seats"""
    print_test("Get All Booked Seats for Showtime")

    response = requests.get(f"{BASE_URL}/api/showtimes/1/seats")
    print_response(response)

    if response.status_code == 200:
        count = len(response.json().get('booked_seats', []))
        print_success(f"Retrieved {count} booked seat(s)")
    else:
        print_error("Failed to retrieve booked seats")

# ============================================================================
# PAYMENT TESTS
# ============================================================================

def test_create_payment():
    """Test 13: Create Payment"""
    print_test("Create Payment")

    data = {
        "amount": 25.50,
        "created_by": 1
    }

    response = requests.post(
        f"{BASE_URL}/api/payments/",
        json=data
    )
    print_response(response)

    if response.status_code == 201:
        payment_id = response.json()['payment']['payment_id']
        print_success(f"Payment created successfully (ID: {payment_id})")
        return payment_id
    else:
        print_error("Failed to create payment")
        return None

def test_process_payment(payment_id):
    """Test 14: Process Payment"""
    print_test(f"Process Payment (ID: {payment_id})")

    response = requests.post(f"{BASE_URL}/api/payments/{payment_id}/process")
    print_response(response)

    if response.status_code == 200:
        print_success("Payment processed successfully")
        return True
    else:
        print_error("Failed to process payment")
        return False

def test_complete_booking(booking_id):
    """Test 15: Complete Booking (Payment + Confirmation)"""
    print_test(f"Complete Booking (ID: {booking_id})")

    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/complete")
    print_response(response)

    if response.status_code == 200:
        print_success("Booking completed successfully")
        return True
    else:
        print_error("Failed to complete booking")
        return False

def test_cancel_booking():
    """Test 16: Cancel Booking"""
    print_test("Cancel Booking")

    # Create a booking first
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [{"row": "F", "col": 1}]
    }
    response = requests.post(f"{BASE_URL}/api/bookings/", json=data)

    if response.status_code == 201:
        booking_id = response.json()['booking']['booking_id']
        print_info(f"Created booking {booking_id}")

        # Now cancel it
        cancel_response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/cancel")
        print_response(cancel_response)

        if cancel_response.status_code == 200:
            print_success("Booking cancelled successfully")

            # Verify seat is available again
            check_data = {"seats": [{"row": "F", "col": 1}]}
            check_response = requests.post(
                f"{BASE_URL}/api/showtimes/1/check-availability",
                json=check_data
            )

            if check_response.json().get('available'):
                print_success("Seat is available again after cancellation")
            else:
                print_error("Seat should be available after cancellation")
        else:
            print_error("Failed to cancel booking")
    else:
        print_error("Failed to create test booking")

def test_extend_hold():
    """Test 17: Extend Seat Hold"""
    print_test("Extend Seat Hold Time")

    # Create a booking
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [{"row": "G", "col": 1}]
    }
    response = requests.post(f"{BASE_URL}/api/bookings/", json=data)

    if response.status_code == 201:
        booking_id = response.json()['booking']['booking_id']
        print_info(f"Created booking {booking_id}")

        # Extend hold
        extend_data = {"additional_minutes": 5}
        extend_response = requests.post(
            f"{BASE_URL}/api/showtimes/booking/{booking_id}/extend-hold",
            json=extend_data
        )
        print_response(extend_response)

        if extend_response.status_code == 200:
            print_success("Hold time extended successfully")
        else:
            print_error("Failed to extend hold time")
    else:
        print_error("Failed to create test booking")

# ============================================================================
# FULL FLOW TEST
# ============================================================================

def test_complete_flow():
    """Test 18: Complete Booking Flow"""
    print_test("Complete Booking Flow (End-to-End)")

    print_info("Step 1: Check seat availability")
    check_data = {"seats": [{"row": "H", "col": 1}, {"row": "H", "col": 2}]}
    check_response = requests.post(
        f"{BASE_URL}/api/showtimes/1/check-availability",
        json=check_data
    )

    if not check_response.json().get('available'):
        print_error("Seats not available, skipping flow test")
        return

    print_success("Seats available")

    print_info("\nStep 2: Create booking")
    booking_data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [{"row": "H", "col": 1}, {"row": "H", "col": 2}]
    }
    booking_response = requests.post(f"{BASE_URL}/api/bookings/", json=booking_data)

    if booking_response.status_code != 201:
        print_error("Failed to create booking")
        return

    booking_id = booking_response.json()['booking']['booking_id']
    print_success(f"Booking created (ID: {booking_id})")

    print_info("\nStep 3: Get booking details")
    get_response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
    print_success("Retrieved booking details")

    print_info("\nStep 4: Complete booking (payment + confirmation)")
    complete_response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/complete")

    if complete_response.status_code == 200:
        print_success("Booking completed successfully")
        payment_id = complete_response.json()['payment']['payment_id']
        print_info(f"Payment ID: {payment_id}")
        print_info(f"Total Amount: ${complete_response.json()['payment']['amount']}")

        print_info("\nStep 5: Verify seat is no longer available")
        verify_response = requests.post(
            f"{BASE_URL}/api/showtimes/1/check-availability",
            json=check_data
        )

        if not verify_response.json().get('available'):
            print_success("✓ Seats correctly marked as unavailable")
        else:
            print_error("Seats should not be available")

        print_success("\n🎉 COMPLETE FLOW TEST PASSED!")
    else:
        print_error("Failed to complete booking")

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    start_time = time.time()

    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}BOOKING SERVICE - COMPREHENSIVE TEST SUITE{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")

    # Test 1: Health check
    if not test_health():
        print_error("\n❌ Service is not running. Aborting tests.")
        print_info("Start the service with: python app.py")
        return

    # Test 2-9: Booking tests
    test_create_booking_invalid_user()
    test_create_booking_invalid_seats()
    test_create_booking_too_many_seats()
    test_create_booking_duplicate_seat()

    booking_id = test_create_booking_success()
    if booking_id:
        test_get_booking(booking_id)

    test_get_booking_not_found()
    test_get_user_bookings()

    # Test 10-12: Seat/Showtime tests
    test_check_seat_availability()
    test_get_seat_map()
    test_get_booked_seats()

    # Test 13-14: Payment tests
    payment_id = test_create_payment()
    if payment_id:
        test_process_payment(payment_id)

    # Test 15-17: Advanced booking operations
    if booking_id:
        test_complete_booking(booking_id)

    test_cancel_booking()
    test_extend_hold()

    # Test 18: Complete flow
    test_complete_flow()

    # Summary
    elapsed_time = time.time() - start_time
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS COMPLETED{Colors.END}")
    print(f"{Colors.BOLD}Time elapsed: {elapsed_time:.2f} seconds{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

if __name__ == "__main__":
    run_all_tests()
