from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv("DATABASE_USERNAME")}:{os.getenv("DATABASE_PASSWORD")}@{os.getenv("DATABASE_HOSTNAME")}:{os.getenv("DATABASE_PORT")}/{os.getenv("DATABASE_NAME")}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
# creates all tables in the database if they dont exist
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# creates a session for the database; opens and closes the database connection preventing leakage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
