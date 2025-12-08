import os
from datetime import timedelta

from dotenv import load_dotenv
load_dotenv()

class Config:
    # Google Cloud SQL Database configuration
    # For Cloud SQL connection via Unix socket (when running on GCP):
    # postgresql+psycopg2://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE
    # For external/public IP connection (local development):
    # postgresql://USER:PASSWORD@PUBLIC_IP:5432/DATABASE

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/booking_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Cloud SQL connection pooling settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'max_overflow': 2
    }

    # Application configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Booking configuration
    SEAT_HOLD_DURATION_MINUTES = int(os.getenv('SEAT_HOLD_DURATION_MINUTES', '10'))
    MAX_SEATS_PER_BOOKING = int(os.getenv('MAX_SEATS_PER_BOOKING', '10'))

    # External services
    MOVIE_SERVICE_URL = os.getenv('MOVIE_SERVICE_URL', 'http://localhost:5001')
    THEATRE_SERVICE_URL = os.getenv('THEATRE_SERVICE_URL', 'http://localhost:5002')
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5004')

    # CORS
    CORS_HEADERS = 'Content-Type'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
