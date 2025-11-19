"""
Simple API test script for Booking Service
Run this after starting the service to test endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5003"

def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_booking():
    """Test creating a booking"""
    print("\n=== Testing Create Booking ===")
    data = {
        "user_id": 1,
        "showtime_id": 1,
        "seats": [
            {"row": "A", "col": 1},
            {"row": "A", "col": 2}
        ]
    }
    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        return response.json()['booking']['booking_id']
    return None

def test_get_booking(booking_id):
    """Test getting a booking"""
    print(f"\n=== Testing Get Booking {booking_id} ===")
    response = requests.get(f"{BASE_URL}/api/bookings/{booking_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_seat_map():
    """Test getting seat map"""
    print("\n=== Testing Get Seat Map ===")
    response = requests.get(
        f"{BASE_URL}/api/showtimes/1/seat-map?rows=A,B,C&cols=5"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_complete_booking(booking_id):
    """Test completing a booking"""
    print(f"\n=== Testing Complete Booking {booking_id} ===")
    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/complete")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_get_user_bookings():
    """Test getting user bookings"""
    print("\n=== Testing Get User Bookings ===")
    response = requests.get(f"{BASE_URL}/api/bookings/user/1")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Booking Service API Tests")
    print("=" * 60)

    # Test health check
    if not test_health():
        print("\nService is not running. Please start the service first.")
        return

    # Test creating a booking
    booking_id = test_create_booking()

    if booking_id:
        # Test getting the booking
        test_get_booking(booking_id)

        # Test completing the booking
        test_complete_booking(booking_id)

        # Test getting user bookings
        test_get_user_bookings()

    # Test seat map
    test_get_seat_map()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()