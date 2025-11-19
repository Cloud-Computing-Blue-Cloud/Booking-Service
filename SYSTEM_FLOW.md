# Booking Service - End-to-End System Flow

## Overview

The Booking Service is a microservice that manages movie ticket bookings, seat reservations, and payments. It integrates with Movie Service, Theatre Service, and User Service to provide a complete ticket booking experience.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User/UI   │────▶│   Booking    │────▶│  Cloud SQL  │
│  (Theatre   │     │   Service    │     │  Database   │
│    UI)      │◀────│  (Port 5003) │◀────│             │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ├──────────────┐
                           │              │
                           ▼              ▼
                    ┌─────────────┐  ┌──────────────┐
                    │   Movie     │  │   Theatre    │
                    │   Service   │  │   Service    │
                    │  (Port 5001)│  │  (Port 5002) │
                    └─────────────┘  └──────────────┘
```

---

## Complete Booking Flow (End-to-End)

### Phase 1: User Browses Movies and Showtimes

```
┌─────────┐
│  USER   │
└────┬────┘
     │
     │ 1. Browse movies
     ▼
┌─────────────────┐
│ Movie Service   │──▶ Returns: List of movies with details
│ GET /movies     │    (name, rating, language, runtime, etc.)
└─────────────────┘
     │
     │ 2. Select movie, view showtimes
     ▼
┌─────────────────┐
│Theatre Service  │──▶ Returns: Available showtimes for selected movie
│GET /showtimes   │    (showtime_id, screen_id, start_time, etc.)
│  ?movie_id=X    │
└─────────────────┘
```

**Data Flow:**
- User sees movies from Movie Service
- Selects a movie
- Theatre Service shows available showtimes in different theaters/screens

---

### Phase 2: Seat Selection and Availability Check

```
┌─────────┐
│  USER   │ Selects showtime & wants to see seat map
└────┬────┘
     │
     │ 3. Request seat map for showtime
     ▼
┌──────────────────────────────────┐
│ Booking Service                  │
│ GET /api/showtimes/{id}/seat-map │
│   ?rows=A,B,C&cols=10            │
└──────────┬───────────────────────┘
           │
           │ Queries booked_seats table
           ▼
┌─────────────────────────────────┐
│ Cloud SQL Database              │
│ SELECT * FROM booked_seats      │
│ WHERE showtime_id = X           │
│   AND status IN ('on_hold',     │
│                   'booked')     │
│   AND is_deleted = FALSE        │
└──────────┬──────────────────────┘
           │
           │ Returns seat availability
           ▼
┌─────────┐
│  USER   │ Sees seat map:
└─────────┘ [A1][A2][A3][A4][A5]
            [B1][B2][X ][B4][B5]  (X = occupied)
            [C1][C2][C3][C4][C5]
```

**Optional: Check Specific Seats**
```
POST /api/showtimes/{showtime_id}/check-availability
{
  "seats": [
    {"row": "A", "col": 1},
    {"row": "A", "col": 2}
  ]
}

Response:
{
  "available": true,
  "message": "All seats are available"
}
```

---

### Phase 3: Create Booking (Reserve Seats)

```
┌─────────┐
│  USER   │ Selects seats: A1, A2 and clicks "Book"
└────┬────┘
     │
     │ 4. Create booking request
     ▼
┌──────────────────────────────┐
│ Booking Service              │
│ POST /api/bookings/          │
│ {                            │
│   "user_id": 1,              │
│   "showtime_id": 123,        │
│   "seats": [                 │
│     {"row": "A", "col": 1},  │
│     {"row": "A", "col": 2}   │
│   ]                          │
│ }                            │
└──────────┬───────────────────┘
           │
           │ ① Validate request
           │ ② Check seat availability
           ▼
┌─────────────────────────────────┐
│ SeatService                     │
│ check_seats_availability()      │
│ - Query existing bookings       │
│ - Check for expired holds       │
│ - Validate seats are free       │
└──────────┬──────────────────────┘
           │
           │ ③ Create booking record
           ▼
┌─────────────────────────────────┐
│ Cloud SQL - bookings table      │
│ INSERT INTO bookings            │
│ (user_id, showtime_id,          │
│  booking_time, status)          │
│ VALUES (1, 123, NOW(),          │
│         'pending')              │
│                                 │
│ Returns: booking_id = 501       │
└──────────┬──────────────────────┘
           │
           │ ④ Reserve seats (put on hold)
           ▼
┌─────────────────────────────────┐
│ Cloud SQL - booked_seats table  │
│ INSERT INTO booked_seats        │
│ (booking_id, showtime_id,       │
│  seat_row, seat_col, status,    │
│  hold_expiry_time)              │
│ VALUES                          │
│ (501, 123, 'A', 1, 'on_hold',   │
│  NOW() + INTERVAL '10 min'),    │
│ (501, 123, 'A', 2, 'on_hold',   │
│  NOW() + INTERVAL '10 min')     │
└──────────┬──────────────────────┘
           │
           │ ⑤ Update showtime seat count
           ▼
┌─────────────────────────────────┐
│ Cloud SQL - showtimes table     │
│ UPDATE showtimes                │
│ SET seats_booked =              │
│     seats_booked + 2            │
│ WHERE showtime_id = 123         │
└──────────┬──────────────────────┘
           │
           │ Response
           ▼
┌─────────┐
│  USER   │ Receives booking confirmation
└─────────┘ {
              "message": "Booking created",
              "booking": {
                "booking_id": 501,
                "status": "pending",
                "seats": [
                  {"row": "A", "col": 1,
                   "status": "on_hold",
                   "hold_expiry_time": "2025-11-19T10:40:00"},
                  {"row": "A", "col": 2,
                   "status": "on_hold",
                   "hold_expiry_time": "2025-11-19T10:40:00"}
                ]
              }
            }
```

**At this point:**
- Seats are **held for 10 minutes** (configurable)
- Booking status is **"pending"**
- Other users **cannot book these seats**
- User has 10 minutes to complete payment

---

### Phase 4: Payment Processing

```
┌─────────┐
│  USER   │ Proceeds to payment
└────┬────┘
     │
     │ 5. Complete booking (creates payment & confirms)
     ▼
┌──────────────────────────────────┐
│ Booking Service                  │
│ POST /api/bookings/501/complete  │
└──────────┬───────────────────────┘
           │
           │ ① Get booking details
           ▼
┌─────────────────────────────────┐
│ BookingService.get_booking(501) │
│ - Fetch booking                 │
│ - Count seats (2 seats)         │
└──────────┬──────────────────────┘
           │
           │ ② Calculate amount
           ▼
┌─────────────────────────────────┐
│ PaymentService                  │
│ calculate_booking_amount(2)     │
│ = 2 seats × $10 = $20.00        │
└──────────┬──────────────────────┘
           │
           │ ③ Create payment record
           ▼
┌─────────────────────────────────┐
│ Cloud SQL - payments table      │
│ INSERT INTO payments            │
│ (amount, status, created_by)    │
│ VALUES (20.00, 'pending', 1)    │
│                                 │
│ Returns: payment_id = 301       │
└──────────┬──────────────────────┘
           │
           │ ④ Process payment (simulate gateway)
           ▼
┌─────────────────────────────────┐
│ PaymentService.process_payment()│
│ - In production: Call Stripe,   │
│   PayPal, or other gateway      │
│ - Currently: Simulated success  │
│                                 │
│ UPDATE payments                 │
│ SET status = 'completed'        │
│ WHERE payment_id = 301          │
└──────────┬──────────────────────┘
           │
           │ ⑤ Confirm booking
           ▼
┌─────────────────────────────────┐
│ BookingService.confirm_booking()│
│                                 │
│ UPDATE bookings                 │
│ SET status = 'confirmed',       │
│     payment_id = 301            │
│ WHERE booking_id = 501          │
└──────────┬──────────────────────┘
           │
           │ ⑥ Confirm seats (permanent)
           ▼
┌─────────────────────────────────┐
│ Cloud SQL - booked_seats        │
│ UPDATE booked_seats             │
│ SET status = 'booked',          │
│     hold_expiry_time = NULL     │
│ WHERE booking_id = 501          │
└──────────┬──────────────────────┘
           │
           │ Success Response
           ▼
┌─────────┐
│  USER   │ Booking Confirmed! 🎉
└─────────┘ {
              "message": "Booking completed",
              "booking": {
                "booking_id": 501,
                "status": "confirmed",
                "payment_id": 301
              },
              "payment": {
                "payment_id": 301,
                "amount": 20.00,
                "status": "completed"
              }
            }
```

**At this point:**
- Payment is **completed**
- Booking status is **"confirmed"**
- Seats are **permanently booked**
- User receives confirmation

---

### Phase 5: Alternative Flows

#### 5A: User Cancels Booking

```
┌─────────┐
│  USER   │ Decides to cancel
└────┬────┘
     │
     │ POST /api/bookings/501/cancel
     ▼
┌──────────────────────────────────┐
│ BookingService.cancel_booking()  │
│                                  │
│ ① UPDATE bookings                │
│   SET status = 'cancelled'       │
│                                  │
│ ② UPDATE booked_seats            │
│   SET status = 'released',       │
│       is_deleted = TRUE          │
│                                  │
│ ③ UPDATE showtimes               │
│   SET seats_booked =             │
│       seats_booked - 2           │
│                                  │
│ ④ If payment exists:             │
│   UPDATE payments                │
│   SET status = 'refunded'        │
└──────────────────────────────────┘

Result: Seats released, available for others
```

#### 5B: Hold Timer Expires (Auto-Release)

```
┌───────────────┐
│ Background    │ Runs periodically (cron/scheduler)
│ Task/Scheduler│
└───────┬───────┘
        │
        │ BookingService.release_expired_holds()
        ▼
┌─────────────────────────────────┐
│ Find expired seat holds         │
│ SELECT * FROM booked_seats      │
│ WHERE status = 'on_hold'        │
│   AND hold_expiry_time < NOW()  │
│   AND is_deleted = FALSE        │
└──────────┬──────────────────────┘
           │
           │ Release seats
           ▼
┌─────────────────────────────────┐
│ UPDATE booked_seats             │
│ SET status = 'released',        │
│     is_deleted = TRUE           │
│                                 │
│ UPDATE bookings                 │
│ SET status = 'cancelled'        │
│                                 │
│ UPDATE showtimes                │
│ SET seats_booked =              │
│     seats_booked - 2            │
└─────────────────────────────────┘

Result: Seats automatically released after 10 minutes
        if payment not completed
```

#### 5C: Extend Hold Time

```
┌─────────┐
│  USER   │ Needs more time during checkout
└────┬────┘
     │
     │ POST /api/showtimes/booking/501/extend-hold
     │ { "additional_minutes": 5 }
     ▼
┌─────────────────────────────────┐
│ SeatService.extend_seat_hold()  │
│                                 │
│ UPDATE booked_seats             │
│ SET hold_expiry_time =          │
│     NOW() + INTERVAL '5 min'    │
│ WHERE booking_id = 501          │
│   AND status = 'on_hold'        │
└─────────────────────────────────┘

Result: Hold extended by 5 more minutes
```

---

## Database State Transitions

### Booking States

```
pending ────────▶ confirmed
   │
   │
   ▼
cancelled
```

- **pending**: Booking created, payment not completed
- **confirmed**: Payment successful, seats permanently booked
- **cancelled**: User cancelled or hold expired

### Seat States

```
on_hold ────────▶ booked
   │
   │
   ▼
released
```

- **on_hold**: Temporarily reserved (10 min timer)
- **booked**: Permanently reserved after payment
- **released**: Freed up (cancelled or expired)

### Payment States

```
pending ────────▶ completed
   │                  │
   │                  ▼
   │              refunded
   ▼
failed
```

- **pending**: Payment initiated
- **completed**: Payment successful
- **failed**: Payment processing failed
- **refunded**: Payment returned after cancellation

---

## Data Models & Relationships

### Entity Relationship

```
┌─────────────┐         ┌──────────────┐
│  bookings   │◀───────▶│ booked_seats │
│             │         │              │
│ booking_id  │──┐      │ booking_id   │
│ user_id     │  │      │ showtime_id  │
│ showtime_id │  │      │ seat_row     │
│ payment_id  │  │      │ seat_col     │
│ status      │  │      │ status       │
└──────┬──────┘  │      └──────────────┘
       │         │
       │         │      ┌──────────────┐
       │         └─────▶│  payments    │
       │                │              │
       │                │ payment_id   │
       │                │ amount       │
       │                │ status       │
       │                └──────────────┘
       │
       │                ┌──────────────┐
       └───────────────▶│  showtimes   │
                        │              │
                        │ showtime_id  │
                        │ screen_id    │
                        │ movie_id     │
                        │ seats_booked │
                        └──────────────┘
```

### Key Database Queries

**Check Seat Availability:**
```sql
SELECT * FROM booked_seats
WHERE showtime_id = 123
  AND seat_row = 'A'
  AND seat_col = 1
  AND status IN ('on_hold', 'booked')
  AND is_deleted = FALSE;
```

**Get User Bookings:**
```sql
SELECT b.*, bs.*, p.*
FROM bookings b
LEFT JOIN booked_seats bs ON b.booking_id = bs.booking_id
LEFT JOIN payments p ON b.payment_id = p.payment_id
WHERE b.user_id = 1
  AND b.is_deleted = FALSE
ORDER BY b.booking_time DESC;
```

**Find Expired Holds:**
```sql
SELECT * FROM booked_seats
WHERE status = 'on_hold'
  AND hold_expiry_time < NOW()
  AND is_deleted = FALSE;
```

---

## Service Integration Points

### With Theatre Service

```
┌──────────────────┐
│ Theatre Service  │
└────────┬─────────┘
         │
         │ Provides:
         ├─▶ Showtime information
         ├─▶ Screen details (rows, columns)
         ├─▶ Cinema/theatre information
         │
         │ Booking Service uses this to:
         └─▶ Validate showtime_id exists
             Generate seat maps
             Display screening details
```

### With Movie Service

```
┌──────────────────┐
│  Movie Service   │
└────────┬─────────┘
         │
         │ Provides:
         ├─▶ Movie details
         ├─▶ Movie metadata
         │
         │ Booking Service uses this to:
         └─▶ Display movie info in bookings
             Show movie details on tickets
```

### With User Service

```
┌──────────────────┐
│  User Service    │
└────────┬─────────┘
         │
         │ Provides:
         ├─▶ User authentication
         ├─▶ User profile information
         │
         │ Booking Service uses this to:
         └─▶ Validate user_id
             Associate bookings with users
             Send notifications
```

---

## API Endpoint Summary

### Bookings
- **POST** `/api/bookings/` - Create booking
- **GET** `/api/bookings/{id}` - Get booking details
- **GET** `/api/bookings/user/{user_id}` - Get user's bookings
- **POST** `/api/bookings/{id}/confirm` - Confirm with payment
- **POST** `/api/bookings/{id}/cancel` - Cancel booking
- **POST** `/api/bookings/{id}/complete` - One-step complete

### Payments
- **POST** `/api/payments/` - Create payment
- **GET** `/api/payments/{id}` - Get payment details
- **POST** `/api/payments/{id}/process` - Process payment
- **POST** `/api/payments/{id}/refund` - Refund payment

### Seats/Showtimes
- **GET** `/api/showtimes/{id}/seats` - Get booked seats
- **GET** `/api/showtimes/{id}/seat-map` - Get seat map
- **POST** `/api/showtimes/{id}/check-availability` - Check seats
- **POST** `/api/showtimes/booking/{id}/extend-hold` - Extend hold

---

## Timeline Example

```
Time: 10:30:00 - User creates booking (booking_id: 501)
                 Seats A1, A2 held until 10:40:00

Time: 10:35:00 - User reviewing booking, needs more time
                 Extends hold by 5 minutes → 10:45:00

Time: 10:38:00 - User completes payment
                 ✓ Payment successful (payment_id: 301)
                 ✓ Booking confirmed
                 ✓ Seats permanently booked

Time: 10:50:00 - User receives email confirmation
                 Ready to watch movie! 🎬
```

---

## Error Handling & Edge Cases

### Concurrent Booking Attempts
```
User A and User B try to book seat A1 simultaneously

Database ensures atomicity:
- First request succeeds
- Second request fails: "Seat already booked"
- Unique constraint prevents duplicates
```

### Payment Failure
```
1. Booking created (pending)
2. Payment fails
3. Options:
   a) User retries payment
   b) Hold expires → seats released
   c) User cancels → seats released
```

### System Crash During Booking
```
- Database transactions ensure consistency
- Incomplete bookings remain "pending"
- Background job cleans expired holds
```

---

## Performance Considerations

1. **Database Indexing**: Indexed on user_id, showtime_id, seat lookups
2. **Connection Pooling**: 5 connections, recycled every 30 min
3. **Seat Hold Duration**: Configurable (default: 10 minutes)
4. **Cleanup Job**: Periodic task to release expired holds

---

## Security Features

1. **Soft Deletes**: Data preserved for audit trails
2. **Timestamps**: created_at, updated_at for all records
3. **Input Validation**: All requests validated
4. **SQL Injection Protection**: SQLAlchemy ORM
5. **CORS**: Configured for cross-origin requests

---

This is the complete end-to-end flow of your Booking Service! 🎬🎟️