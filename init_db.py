#!/usr/bin/env python3
"""Initialize the database with all tables"""

from app import app, db

def init_database():
    """Create all database tables"""
    with app.app_context():
        # Drop all tables first (for development)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database initialized successfully!")
        print("Tables created:")
        for table in db.metadata.tables:
            print(f"  - {table}")

if __name__ == '__main__':
    init_database()