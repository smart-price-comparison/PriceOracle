# database/connection.py

from sqlmodel import SQLModel, create_engine, Session
import os

DB_FILE = os.getenv("PRICEORACLE_DB", "priceoracle.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    """Create tables if they do not exist."""
    try:
        from database.models import ScrapedProduct
    except Exception:
        pass
    
    SQLModel.metadata.create_all(engine)


def get_session():
    return Session(engine)
