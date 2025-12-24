"""
Database migration script to add missing columns to existing tables.

Run this script to update your database schema without losing data.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to analyses table"""
    
    # Find the database file
    db_path = Path(__file__).parent / "database.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    print(f"📝 Migrating database at {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check which columns exist
        cursor.execute("PRAGMA table_info(analyses)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        print(f"✓ Found {len(existing_columns)} columns in analyses table")
        
        # Add missing columns if they don't exist
        columns_to_add = [
            ("image_base64", "TEXT"),
            ("original_image_base64", "TEXT"),
        ]
        
        added_count = 0
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE analyses ADD COLUMN {column_name} {column_type}")
                    print(f"✓ Added column: {column_name}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Column {column_name} might already exist: {e}")
        
        conn.commit()
        
        if added_count > 0:
            print(f"✅ Successfully added {added_count} columns")
        else:
            print("✅ All columns already exist - no migration needed")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
