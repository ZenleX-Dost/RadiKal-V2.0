"""
Clear all analyses and detections so user can re-run with correct classifications.
"""
import sys
sys.path.append('.')

from db import get_db, Analysis, Detection, Explanation

db = next(get_db())

try:
    # Get counts
    analysis_count = db.query(Analysis).count()
    detection_count = db.query(Detection).count()
    explanation_count = db.query(Explanation).count()
    
    print(f"\n📊 Current database state:")
    print(f"   Analyses: {analysis_count}")
    print(f"   Detections: {detection_count}")
    print(f"   Explanations: {explanation_count}")
    
    # Delete all
    db.query(Detection).delete()
    db.query(Explanation).delete()
    db.query(Analysis).delete()
    
    db.commit()
    
    print(f"\n✅ Cleared all data!")
    print(f"   Deleted {analysis_count} analyses")
    print(f"   Deleted {detection_count} detections")
    print(f"   Deleted {explanation_count} explanations")
    print(f"\n💡 Now re-run your analyses through the Analysis page to get correct defect types.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
