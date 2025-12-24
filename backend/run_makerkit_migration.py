"""
Run Makerkit schema migration on Supabase database
"""
import os
import sys
from pathlib import Path
from db.database import engine
from sqlalchemy import text

def run_migration():
    """Run the Makerkit schema migration"""
    
    # Path to the schema file
    schema_file = Path(__file__).parent.parent / "frontend-makerkit" / "apps" / "web" / "supabase" / "migrations" / "20241219010757_schema.sql"
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)
    
    print(f"📄 Reading schema from: {schema_file}")
    
    # Read the SQL file
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print("🔄 Running migration...")
    
    try:
        # Execute the SQL
        with engine.connect() as conn:
            # Split by statement separator if needed
            # Note: This is a simple approach - for complex migrations, use proper migration tool
            conn.execute(text(sql_content))
            conn.commit()
        
        print("✅ Migration completed successfully!")
        print("\n📊 Created Makerkit tables:")
        print("  - accounts (user accounts)")
        print("  - kit schema (helper functions)")
        print("  - Storage bucket: account_image")
        print("  - RLS policies enabled")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
