"""
Migration script to add new columns to the User table.
Run this once to add hashed_password, email, oauth_provider, and oauth_provider_id columns.
"""
from sqlalchemy import text
from db.database import engine

def migrate_user_table():
    """Add new columns to the User table if they don't exist."""
    with engine.connect() as conn:
        # Check if columns exist and add them if they don't
        try:
            # Add hashed_password column
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS hashed_password VARCHAR
            """))
            print("✓ Added hashed_password column")
        except Exception as e:
            print(f"Note: hashed_password column - {e}")
        
        try:
            # Add email column
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE
            """))
            print("✓ Added email column")
        except Exception as e:
            print(f"Note: email column - {e}")
        
        try:
            # Add oauth_provider column
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR
            """))
            print("✓ Added oauth_provider column")
        except Exception as e:
            print(f"Note: oauth_provider column - {e}")
        
        try:
            # Add oauth_provider_id column
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS oauth_provider_id VARCHAR
            """))
            print("✓ Added oauth_provider_id column")
        except Exception as e:
            print(f"Note: oauth_provider_id column - {e}")
        
        conn.commit()
        print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_user_table()

