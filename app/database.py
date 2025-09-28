import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# DATABASE_URL = "sqlite:///./estimation.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://rhd_estimation_db_user:REInwLwpx6bOuOabJvbnesC04y74jgC5@dpg-d2smeuf5r7bs73akn6g0-a.singapore-postgres.render.com/rhd_estimation_db")

class Base(DeclarativeBase):
    pass

# Add this block to handle SSL for production
if DATABASE_URL.startswith("postgresql://"):
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)