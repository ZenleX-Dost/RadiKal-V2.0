"""
Clear all sample data from the database.
This will delete all analyses and related records (detections, explanations).
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from db import get_db, Analysis, Detection, Explanation
from sqlalchemy.orm import Session

def clear_all_data(db: Session):
    """Delete all analyses and related records from the database."""
    
    print("🗑️  Clearing all data from database...\n")
    
    try:
        # Count existing records
        analysis_count = db.query(Analysis).count()
        detection_count = db.query(Detection).count()
        explanation_count = db.query(Explanation).count()
        
        print(f"Current database contents:")
        print(f"  Analyses: {analysis_count}")
        print(f"  Detections: {detection_count}")
        print(f"  Explanations: {explanation_count}")
        
        if analysis_count == 0:
            print("\n✅ Database is already empty. Nothing to clear.")
            return
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete ALL {analysis_count} analyses!")
        response = input("Are you sure you want to continue? (yes/N): ")
        
        if response.lower() != 'yes':
            print("\n❌ Cancelled. No data was deleted.")
            return
        
        # Delete all records (CASCADE will handle related records)
        print("\nDeleting records...")
        deleted_analyses = db.query(Analysis).delete()
        
        db.commit()
        
        print(f"\n✅ Successfully deleted {deleted_analyses} analyses!")
        print(f"   (Related detections and explanations were also removed)")
        
        # Verify deletion
        remaining = db.query(Analysis).count()
        if remaining == 0:
            print("\n✅ Database is now completely clean.")
            print("   You can now add your real analysis data.")
        else:
            print(f"\n⚠️  Warning: {remaining} analyses still remain in database.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("  RadiKal Database Cleanup Tool")
    print("=" * 60)
    print()
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        clear_all_data(db)
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
