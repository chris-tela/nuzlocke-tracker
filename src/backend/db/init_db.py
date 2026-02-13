# initalizes database tables

from database import engine
from models import Base


Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
print("Available tables:")
for table in Base.metadata.tables.keys():
    print(f"  - {table}")
