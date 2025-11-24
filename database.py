"""
Database setup for FastAPI with SQLAlchemy
"""

import os
from sqlalchemy import create_engine, Column, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from config import Config

# Create engine
# --- CONFIGURATION START ---
DB_USER = os.getenv("DB_USER", "transactions-db-user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")     
DB_HOST = os.getenv("DB_HOST", "34.132.246.96")          
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "transactions")         

# Connection String Format: dialect+driver://username:password@host:port/database
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Allow override for testing (e.g. sqlite)
# if hasattr(Config, 'SQLALCHEMY_DATABASE_URI') and Config.SQLALCHEMY_DATABASE_URI and Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
#     DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
# --- CONFIGURATION END ---

# Create engine
engine = create_engine(
    DATABASE_URI,
    # 'pool_pre_ping' is crucial for Cloud SQL to handle dropped connections automatically
    pool_pre_ping=True, 
    # Recycles connections before the cloud firewall cuts them off
    pool_recycle=1800, 
    # Set to True to see raw SQL queries in your terminal (great for debugging)
    echo=True  
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# Create base class for models
Base = declarative_base()
Base.query = db_session.query_property()


class DatabaseManager:
    """Database manager for FastAPI compatibility"""

    def __init__(self):
        self.Base = Base
        self.session = db_session
        self.engine = engine
        self.Column = Column

    def init_app(self, app):
        """Initialize with FastAPI app (for compatibility)"""
        pass

    def create_all(self):
        """Create all tables"""
        Base.metadata.create_all(bind=engine)

    def drop_all(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=engine)


# Create db instance for backward compatibility
db = DatabaseManager()


class BaseModel:
    """Base model with common fields"""
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=False)

    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result


# Dependency for FastAPI routes
def get_db():
    """
    FastAPI dependency to get database session

    Usage:
        @app.get("/items/")
        async def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
