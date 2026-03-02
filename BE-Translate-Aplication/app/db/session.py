from sqlalchemy import create_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Aquí leemos la URL que pusimos en el .env ayer
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/tms_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)