from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv("DATABASE_USERNAME")}:{os.getenv("DATABASE_PASSWORD")}@{os.getenv("DATABASE_HOSTNAME")}:{os.getenv("DATABASE_PORT")}/{os.getenv("DATABASE_NAME")}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
# creates all tables in the database if they dont exist
Base = declarative_base()
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# creates a session for the database; opens and closes the database connection preventing leakage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
