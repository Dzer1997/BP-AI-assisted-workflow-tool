from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from realview_chat.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine
)

Base = declarative_base()


def init_db():
    from realview_chat.database import models
    Base.metadata.create_all(bind=engine)