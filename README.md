# Booking Service - FastAPI

A high-performance microservice for managing movie ticket bookings, seat reservations, and payments built with **FastAPI**.

## 🚀 Features

- ✅ Create and manage bookings
- ✅ Seat selection 
- ✅ Payment processing
- ✅ Booking confirmation and cancellation
- ✅ Real-time seat availability checking
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
# Create booking (202 Accepted - async processing)
POST /api/bookings/
{
  "user_id": 1,
  "showtime_id": 1,
  "seats": [
    {"row": 5, "col": 3},
    {"row": 5, "col": 4}
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
# Create payment (201 Created - synchronous)
POST /api/payments/
{
  "booking_id": 1,
  "amount": 20.00
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

```

### Health & Info

```bash
# Health check
GET /health

# API information
GET /
```

## 🗄️ Database

Uses **Google Cloud SQL (MySQL)** with the following tables:

- **bookings** - Main booking records
- **booked_seats** - Individual seat reservations 
- **payments** - Payment transactions
- **showtimes** - Reference to showtimes from Theatre Service

See [CLOUD_SQL_SETUP.md](CLOUD_SQL_SETUP.md) for database setup instructions.

## ⚙️ Configuration

Edit `.env` file:

```bash
# Google Cloud SQL (MySQL)
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=34.132.246.96
DB_PORT=3306
DB_NAME=transactions

# Application
SECRET_KEY=your-secret-key
DEBUG=True
MAX_SEATS_PER_BOOKING=10

# External Services
MOVIE_SERVICE_URL=http://localhost:5001
THEATRE_SERVICE_URL=http://localhost:5002
USER_SERVICE_URL=http://localhost:5004
```

## 🔄 Booking Flow

1. **Create Booking** (`POST /api/bookings/`) → Returns **202 Accepted** with booking ID
   - Background processing handles seat reservation
2. **Poll Status** (`GET /api/bookings/{id}`) → Check booking status
3. **User Pays** (`POST /api/payments/`) → Returns **201 Created** with payment ID
4. **Confirm Booking** (`POST /api/bookings/{id}/confirm`) → Seats permanently booked

### Seat States
- `on_hold` - Temporarily reserved (seat holding functionality exists in code)
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

# Create booking (returns 202 Accepted)
curl -i -X POST http://localhost:5003/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "showtime_id": 1,
    "seats": [{"row": 5, "col": 3}]
  }'
```

## 🚀 Deployment

### Development
```bash
# Auto-reload on code changes
uvicorn app:app --reload --port 5003
```



## 🤝 Integration with Other Services

- **Movie Service** (port 5001) - Movie information
- **Theatre Service** (port 5002) - Showtime and screen details
- **User Service** (port 5004) - User authentication

## 📖 Documentation

- **Interactive API Docs**: http://localhost:5003/docs
- [SYSTEM_FLOW.md](SYSTEM_FLOW.md) - Complete end-to-end flow


## 🔧 Development Tips

```bash
# View logs
uvicorn app:app --log-level debug

# Test database connection
python3 cloud_sql_connector.py

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```



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