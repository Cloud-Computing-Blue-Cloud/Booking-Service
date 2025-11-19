"""
Google Cloud SQL Connection Helper

This module provides utility functions for connecting to Google Cloud SQL
using both Unix socket (for GCP environments) and TCP (for local development).
"""

import os
from google.cloud.sql.connector import Connector
import sqlalchemy

def get_cloud_sql_engine():
    """
    Create a SQLAlchemy engine for Google Cloud SQL.
    Automatically detects if running on GCP or locally.

    Returns:
        sqlalchemy.engine.Engine: Database engine
    """
    # Check if using Cloud SQL connector
    instance_connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')

    if instance_connection_name:
        # Running on GCP - use Cloud SQL Connector
        return create_cloud_sql_engine_with_connector(instance_connection_name)
    else:
        # Use standard connection string from DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        return sqlalchemy.create_engine(
            database_url,
            pool_size=5,
            pool_recycle=1800,
            pool_pre_ping=True,
            max_overflow=2
        )

def create_cloud_sql_engine_with_connector(instance_connection_name):
    """
    Create engine using Cloud SQL Python Connector (for GCP deployment).

    Args:
        instance_connection_name: Format "project:region:instance"

    Returns:
        sqlalchemy.engine.Engine: Database engine
    """
    connector = Connector()

    def getconn():
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            db=os.getenv('DB_NAME')
        )
        return conn

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        max_overflow=2
    )

    return engine

def test_connection():
    """Test database connection"""
    try:
        engine = get_cloud_sql_engine()
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            print("✓ Database connection successful!")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection when run directly
    from dotenv import load_dotenv
    load_dotenv()
    test_connection()