from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

DATABASE_URL = settings.DATABASE_URL

class Base(DeclarativeBase):
    pass

connect_args = {}
if DATABASE_URL.startswith("postgresql://") and settings.APP_ENV == "production":
    connect_args["sslmode"] = "require"
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)