"""
Database Migration Script for Role-Based Access Control

This script migrates the database to support the new role system:
- Updates User table with new role values and supervisor_id
- Creates ChangeRequest table
- Creates AnalysisComment table
- Creates ActivityLog table
- Creates UserActivitySummary table
- Adds performed_by column to Analysis table

Run this script once to update your database schema.

Usage:
    python migrate_roles.py

Author: RadiKal Team
Date: 2026-01-11
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from db.database import engine, SessionLocal
from db.models import Base, UserRole

def get_table_names():
    """Get list of existing tables."""
    inspector = inspect(engine)
    return inspector.get_table_names()

def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_roles():
    """Run the role migration."""
    print("=" * 80)
    print("RadiKal Role-Based Access Control Migration")
    print("=" * 80)
    
    existing_tables = get_table_names()
    
    # Step 1: Create new tables
    print("\n[1/5] Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    new_tables = get_table_names()
    created_tables = set(new_tables) - set(existing_tables)
    if created_tables:
        print(f"  ✅ Created tables: {', '.join(created_tables)}")
    else:
        print("  ℹ️  All tables already exist")
    
    # Step 2: Add supervisor_id to users table if not exists
    print("\n[2/5] Checking users table schema...")
    with engine.connect() as conn:
        if 'users' in new_tables:
            if not column_exists('users', 'supervisor_id'):
                print("  Adding supervisor_id column to users...")
                try:
                    conn.execute(text("""
                        ALTER TABLE users ADD COLUMN supervisor_id INTEGER REFERENCES users(id)
                    """))
                    conn.commit()
                    print("  ✅ Added supervisor_id column")
                except Exception as e:
                    print(f"  ⚠️  Could not add supervisor_id: {e}")
            else:
                print("  ✅ supervisor_id column already exists")
        else:
            print("  ⚠️  users table not found")
    
    # Step 3: Add performed_by to analyses table if not exists
    print("\n[3/5] Checking analyses table schema...")
    with engine.connect() as conn:
        if 'analyses' in new_tables:
            if not column_exists('analyses', 'performed_by'):
                print("  Adding performed_by column to analyses...")
                try:
                    conn.execute(text("""
                        ALTER TABLE analyses ADD COLUMN performed_by INTEGER REFERENCES users(id)
                    """))
                    conn.commit()
                    print("  ✅ Added performed_by column")
                except Exception as e:
                    print(f"  ⚠️  Could not add performed_by: {e}")
            else:
                print("  ✅ performed_by column already exists")
        else:
            print("  ⚠️  analyses table not found")
    
    # Step 4: Migrate existing user roles
    print("\n[4/5] Migrating user roles...")
    db = SessionLocal()
    try:
        # Map old roles to new roles
        role_mapping = {
            'technician': UserRole.RADIKAL_USER,
            'project_chief': UserRole.CHIEF,
            'manager': UserRole.MANAGER,
        }
        
        # Update existing users with old roles
        result = db.execute(text("SELECT id, role FROM users"))
        users = result.fetchall()
        
        migrated_count = 0
        for user_id, old_role in users:
            if old_role in role_mapping:
                new_role = role_mapping[old_role]
                db.execute(
                    text("UPDATE users SET role = :new_role WHERE id = :user_id"),
                    {"new_role": new_role, "user_id": user_id}
                )
                migrated_count += 1
                print(f"  Migrated user {user_id}: {old_role} → {new_role}")
        
        db.commit()
        
        if migrated_count > 0:
            print(f"  ✅ Migrated {migrated_count} user(s)")
        else:
            print("  ℹ️  No users needed role migration")
            
    except Exception as e:
        print(f"  ⚠️  Role migration error: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Step 5: Create indexes
    print("\n[5/5] Creating indexes...")
    with engine.connect() as conn:
        indexes_to_create = [
            ("ix_change_requests_status", "change_requests", "status"),
            ("ix_change_requests_requested_by", "change_requests", "requested_by_id"),
            ("ix_change_requests_assigned_to", "change_requests", "assigned_to_id"),
            ("ix_analysis_comments_analysis", "analysis_comments", "analysis_id"),
            ("ix_activity_logs_user", "activity_logs", "user_id"),
            ("ix_activity_logs_created", "activity_logs", "created_at"),
            ("ix_user_activity_summaries_user", "user_activity_summaries", "user_id"),
        ]
        
        for idx_name, table_name, column_name in indexes_to_create:
            if table_name in new_tables:
                try:
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({column_name})
                    """))
                    conn.commit()
                except Exception as e:
                    # Index might already exist
                    pass
        
        print("  ✅ Indexes verified")
    
    print("\n" + "=" * 80)
    print("Migration completed successfully!")
    print("=" * 80)
    print("\nNew Role System:")
    print("  • radikal_user: Can use models, perform analyses, view other users' results")
    print("  • chief: Supervise RadikalUsers, review, request changes, add comments")
    print("  • manager: View history, analysis results, activity charts, change requests")
    print("\nNew API Endpoints:")
    print("  • /api/roles/radikal-user/* - RadikalUser-specific endpoints")
    print("  • /api/roles/chief/* - Chief-specific endpoints")
    print("  • /api/roles/manager/* - Manager-specific endpoints")
    print("  • /api/roles/permissions - Get current user permissions")
    print("=" * 80)


def rollback_migration():
    """Rollback the migration (for testing)."""
    print("Rolling back migration...")
    
    db = SessionLocal()
    try:
        # Map new roles back to old roles
        role_mapping = {
            UserRole.RADIKAL_USER: 'technician',
            UserRole.CHIEF: 'project_chief',
            UserRole.MANAGER: 'manager',
        }
        
        for new_role, old_role in role_mapping.items():
            db.execute(
                text("UPDATE users SET role = :old_role WHERE role = :new_role"),
                {"old_role": old_role, "new_role": new_role}
            )
        
        db.commit()
        print("✅ Rollback completed")
    except Exception as e:
        print(f"⚠️  Rollback error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RadiKal Role Migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        migrate_roles()
