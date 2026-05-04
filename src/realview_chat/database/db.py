import os

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from realview_chat.config import settings
from pathlib import Path
from sqlalchemy.engine import make_url

Base = declarative_base()

engine = None
SessionLocal = None

def init_db():
    global engine, SessionLocal

    db_path = Path("/app/data")
    db_path.mkdir(parents=True, exist_ok=True)
    
    print("CWD =", os.getcwd())
    print("DATABASE_URL =", settings.DATABASE_URL)
    print("Parsed URL =", make_url(settings.DATABASE_URL))
      
    engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

    SessionLocal = sessionmaker(
        bind=engine
    )

    from realview_chat.database import models
    Base.metadata.create_all(bind=engine)