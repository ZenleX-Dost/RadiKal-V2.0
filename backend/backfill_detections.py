"""
Backfill Detection records for existing analyses.

This script creates Detection records for analyses that don't have them yet.
"""
import sys
sys.path.append('.')

from db import get_db, Analysis, Detection
from sqlalchemy.orm import joinedload

# Class names mapping
CLASS_NAMES = {
    0: "LP",  # Lack of Penetration
    1: "PO",  # Porosity
    2: "CR",  # Cracks
    3: "ND"   # No Defect
}

def backfill_detections():
    """Add Detection records to analyses that don't have them."""
    db = next(get_db())
    
    try:
        # Get all completed analyses
        analyses = db.query(Analysis).options(
            joinedload(Analysis.detections)
        ).filter(
            Analysis.status == 'completed'
        ).all()
        
        print(f"Found {len(analyses)} analyses")
        
        fixed = 0
        for analysis in analyses:
            # Skip if already has detections
            if len(analysis.detections) > 0:
                print(f"  Analysis {analysis.id} already has {len(analysis.detections)} detections")
                continue
            
            # Skip if no defects
            if not analysis.has_defects:
                print(f"  Analysis {analysis.id} has no defects, skipping")
                continue
            
            # Create a detection record
            # We'll assume Porosity (label=1) for now since we don't have the original classification
            detection = Detection(
                analysis_id=analysis.id,
                x1=0.0,
                y1=0.0,
                x2=1.0,
                y2=1.0,
                confidence=analysis.mean_confidence or 0.99,
                label=1,  # Porosity
                class_name="PO",  # Porosity
                severity='high',
            )
            db.add(detection)
            fixed += 1
            print(f"  ✅ Created detection for analysis {analysis.id} (assumed PO)")
        
        db.commit()
        print(f"\n✅ Backfilled {fixed} detection records")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_detections()
