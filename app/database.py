import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    DATABASE_URL = os.environ.get("DATABASE_URL")
else:
    DATABASE_URL = "sqlite:///./estimation.db"

class Base(DeclarativeBase):
    pass

# Add this block to handle SSL for production
if DATABASE_URL.startswith("postgresql://"):
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

print(f"Using database at {DATABASE_URL}")
