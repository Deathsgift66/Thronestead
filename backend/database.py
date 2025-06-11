import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db_base import Base

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/postgres')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
