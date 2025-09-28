import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://rhd_estimation_db_user:REInwLwpx6bOuOabJvbnesC04y74jgC5@dpg-d2smeuf5r7bs73akn6g0-a.singapore-postgres.render.com/rhd_estimation_db")

print(f"Using database at {DATABASE_URL}")
