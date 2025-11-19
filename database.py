"""
Database setup for FastAPI with SQLAlchemy
"""

from sqlalchemy import create_engine, Column, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from config import Config

# Create engine
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **Config.SQLALCHEMY_ENGINE_OPTIONS,
    echo=Config.SQLALCHEMY_ECHO
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
