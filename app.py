"""
FastAPI Booking Service Application
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from config import Config
from database import db
from routers import booking_router, payment_router
from schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Booking Service...")
    logger.info(
        f"Database: {Config.SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in Config.SQLALCHEMY_DATABASE_URI else 'Not configured'}"
    )

    # Create database tables
    try:
        from database import db
        from models import Booking, BookedSeat, Payment

        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Could not connect to database: {e}")
        logger.warning(
            "Application will start, but database operations will fail until database is available"
        )

    yield

    # Shutdown
    logger.info("Shutting down Booking Service...")


# Create FastAPI app
app = FastAPI(
    title="Booking Service",
    description="""
    Movie Ticket Booking Microservice

    This service handles:
    * Seat reservations with temporary holds (10 minutes)
    * Booking management (create, confirm, cancel)
    * Payment processing
    * Seat availability checking

    ## Features
    * Automatic seat hold expiration
    * Real-time seat availability
    * Secure payment processing
    * Cloud SQL integration
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "details": errors},
    )


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


# Include routers
app.include_router(booking_router, prefix="/api/bookings", tags=["Bookings"])

app.include_router(payment_router, prefix="/api/payments", tags=["Payments"])


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if the service is running",
)
def health_check():
    """
    Health check endpoint.

    Returns the service status.
    """
    return {"status": "healthy", "service": "booking-service"}


# Root endpoint
@app.get("/", tags=["Info"], summary="API information")
def root():
    """
    Get API information and available endpoints.
    """
    return {
        "service": "Booking Service",
        "version": "2.0.0",
        "framework": "FastAPI",
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "bookings": "/api/bookings/",
            "payments": "/api/payments/",
            "showtimes": "/api/showtimes/",
        },
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    # Create database tables
    try:
        from models import Booking, BookedSeat, Payment

        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Could not connect to database: {e}")
        logger.warning(
            "Application will start, but database operations will fail until database is available"
        )

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5003,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info",
    )
