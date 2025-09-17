# initalizes database tables

from db.database import engine

# remove models that you don't want to reinitialize
from db.models import  Base, Version, Generation, Route


Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
print("Available tables:")
for table in Base.metadata.tables.keys():
    print(f"  - {table}")
