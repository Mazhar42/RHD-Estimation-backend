from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings
import os

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

class Base(DeclarativeBase):
    pass

connect_args = {}
# Check for production environment or if running on Render
is_production = settings.APP_ENV == "production" or os.getenv("RENDER")

if "postgresql" in DATABASE_URL and is_production:
    connect_args["sslmode"] = "require"
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)