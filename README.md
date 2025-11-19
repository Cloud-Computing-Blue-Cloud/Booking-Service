# Booking Service - FastAPI

A high-performance microservice for managing movie ticket bookings, seat reservations, and payments built with **FastAPI**.

## 🚀 Features

- ✅ Create and manage bookings
- ✅ Seat selection with temporary holds (10 minutes)
- ✅ Payment processing
- ✅ Booking confirmation and cancellation
- ✅ Real-time seat availability checking
- ✅ Automatic release of expired seat holds
- ✅ **Interactive API documentation** (Swagger UI)
- ✅ **Automatic request validation** (Pydantic)
- ✅ **Google Cloud SQL integration**

## 📋 Project Structure

```
Booking Service/
├── app.py                      # FastAPI application
├── config.py                   # Configuration settings
├── database.py                 # SQLAlchemy database setup
├── schemas.py                  # Pydantic models for validation
├── requirements.txt            # Python dependencies
├── start.sh                    # Quick start script
├── models/
│   ├── booking.py             # Booking database model
│   ├── booked_seat.py         # Booked seat model
│   ├── payment.py             # Payment model
│   └── showtime.py            # Showtime reference model
├── routers/
│   ├── booking_routes.py      # Booking API endpoints
│   ├── payment_routes.py      # Payment API endpoints
│   └── showtime_routes.py     # Showtime/seat API endpoints
├── services/
│   ├── booking_service.py     # Booking business logic
│   ├── payment_service.py     # Payment business logic
│   └── seat_service.py        # Seat management logic
└── utils/
    ├── validators.py          # Input validation utilities
    └── decorators.py          # Custom decorators
```

## 🛠️ Installation

### Quick Start

```bash
# Use the start script
./start.sh
```

### Manual Setup

1. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Cloud SQL credentials
```

4. **Run the service:**
```bash
# Option 1: Direct
python3 app.py

# Option 2: With uvicorn
uvicorn app:app --reload --port 5003
```

The service will start on `http://localhost:5003`

## 📚 Interactive API Documentation

**Visit: http://localhost:5003/docs**

FastAPI provides automatic, interactive API documentation where you can:
- 📖 View all endpoints and schemas
- 🧪 Test APIs directly in your browser
- 📋 See request/response examples
- ✅ Validate data in real-time

Alternative documentation: http://localhost:5003/redoc

## 🔌 API Endpoints

All endpoints are documented interactively at `/docs`. Quick reference:

### Bookings

```bash
# Create booking
POST /api/bookings/
{
  "user_id": 1,
  "showtime_id": 1,
  "seats": [
    {"row": "A", "col": 1},
    {"row": "A", "col": 2}
  ]
}

# Get booking details
GET /api/bookings/{booking_id}

# Get user's bookings
GET /api/bookings/user/{user_id}
GET /api/bookings/user/{user_id}?include_cancelled=true

# Confirm booking with payment
POST /api/bookings/{booking_id}/confirm
{
  "payment_id": 1
}

# Cancel booking
POST /api/bookings/{booking_id}/cancel

# Complete booking (payment + confirm in one step)
POST /api/bookings/{booking_id}/complete
```

### Payments

```bash
# Create payment
POST /api/payments/
{
  "amount": 20.00,
  "created_by": 1
}

# Get payment details
GET /api/payments/{payment_id}

# Process payment
POST /api/payments/{payment_id}/process

# Refund payment
POST /api/payments/{payment_id}/refund
```

### Showtimes & Seats

```bash
# Get booked seats
GET /api/showtimes/{showtime_id}/seats

# Get seat map with availability
GET /api/showtimes/{showtime_id}/seat-map?rows=A,B,C&cols=10

# Check seat availability
POST /api/showtimes/{showtime_id}/check-availability
{
  "seats": [
    {"row": "A", "col": 1}
  ]
}

# Extend seat hold time
POST /api/showtimes/booking/{booking_id}/extend-hold
{
  "additional_minutes": 5
}
```

### Health & Info

```bash
# Health check
GET /health

# API information
GET /
```

## 🗄️ Database

Uses **Google Cloud SQL (PostgreSQL)** with the following tables:

- **bookings** - Main booking records
- **booked_seats** - Individual seat reservations with hold times
- **payments** - Payment transactions
- **showtimes** - Reference to showtimes from Theatre Service

See [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md) for database setup instructions.

## ⚙️ Configuration

Edit `.env` file:

```bash
# Google Cloud SQL
DATABASE_URL=postgresql://user:password@PUBLIC_IP:5432/booking_db

# Application
SECRET_KEY=your-secret-key
DEBUG=True
SEAT_HOLD_DURATION_MINUTES=10
MAX_SEATS_PER_BOOKING=10

# External Services
MOVIE_SERVICE_URL=http://localhost:5001
THEATRE_SERVICE_URL=http://localhost:5002
USER_SERVICE_URL=http://localhost:5004
```

## 🔄 Booking Flow

1. **Create Booking** → Seats on hold (10 min timer)
2. **User Pays** → Payment processed
3. **Confirm Booking** → Seats permanently booked
4. **Auto-Release** → Expired holds released automatically

### Seat States
- `on_hold` - Temporarily reserved (10 minutes)
- `booked` - Permanently reserved after payment
- `released` - Freed up (cancelled or expired)

### Payment States
- `pending` - Payment initiated
- `completed` - Payment successful
- `failed` - Payment failed
- `refunded` - Payment refunded

## 🧪 Testing

### Quick Test
```bash
# Start service
python3 app.py

# Run tests
python3 test_api.py

# Comprehensive tests
python3 test_comprehensive.py
```

### Using Swagger UI (Easiest!)
1. Go to http://localhost:5003/docs
2. Click any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"

### Using cURL
```bash
# Health check
curl http://localhost:5003/health

# Create booking
curl -X POST http://localhost:5003/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "showtime_id": 1,
    "seats": [{"row": "A", "col": 1}]
  }'
```

## 🚀 Deployment

### Development
```bash
# Auto-reload on code changes
uvicorn app:app --reload --port 5003
```

### Production
```bash
# Multiple workers for better performance
uvicorn app:app --host 0.0.0.0 --port 5003 --workers 4
```

### Google Cloud Run
```bash
gcloud run deploy booking-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🎯 Why FastAPI?

- ⚡ **Performance** - 2-3x faster than Flask
- 📚 **Auto Documentation** - Swagger UI built-in
- ✅ **Type Safety** - Automatic validation with Pydantic
- 🔄 **Async Support** - Better concurrency
- 💻 **Developer Experience** - Auto-completion and type hints

## 🤝 Integration with Other Services

- **Movie Service** (port 5001) - Movie information
- **Theatre Service** (port 5002) - Showtime and screen details
- **User Service** (port 5004) - User authentication

## 📖 Documentation

- **Interactive API Docs**: http://localhost:5003/docs
- [SYSTEM_FLOW.md](SYSTEM_FLOW.md) - Complete end-to-end flow
- [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md) - Database setup guide
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing instructions
- [FASTAPI_SETUP.md](FASTAPI_SETUP.md) - FastAPI setup guide

## 💡 Key Features

### Automatic Validation
```python
# Pydantic automatically validates all requests
class BookingCreate(BaseModel):
    user_id: int  # Must be integer
    showtime_id: int
    seats: List[SeatBase]  # Max 10 seats, validated automatically
```

### Type Safety
```python
async def get_booking(booking_id: int):
    # booking_id is guaranteed to be an int
    # IDE provides auto-completion
```

### Better Error Messages
```json
{
  "error": "Validation error",
  "details": [
    "body -> user_id: value is not a valid integer",
    "body -> seats: ensure this value has at least 1 items"
  ]
}
```

## 🔧 Development Tips

```bash
# View logs
uvicorn app:app --log-level debug

# Test database connection
python3 cloud_sql_connector.py

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

## ⚠️ Notes

- Seat holds automatically expire after 10 minutes (configurable)
- Run periodic cleanup: `BookingService.release_expired_holds()`
- Payment processing is simulated - integrate real gateway in production
- Use `SQLALCHEMY_ECHO=True` in development to see SQL queries

## 📝 Quick Commands

```bash
# Install
pip install -r requirements.txt

# Run
./start.sh
# or
python3 app.py

# Test
python3 test_comprehensive.py

# View docs
open http://localhost:5003/docs
```

---

**Built with FastAPI** 🚀 | **Version 2.0.0** | **Python 3.11+**

For questions, check the interactive documentation at http://localhost:5003/docs