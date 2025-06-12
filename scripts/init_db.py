#!/usr/bin/env python3
"""Initialize the database with tables and sample data."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models.base import Base
from src.core.logging import get_logger


logger = get_logger(__name__)


def init_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created successfully!")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Add any initial data here if needed
        # For example, create default namespaces, admin user, etc.
        
        session.commit()
        logger.info("Initial data added successfully!")
        
    except Exception as e:
        logger.error(f"Error adding initial data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        init_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)