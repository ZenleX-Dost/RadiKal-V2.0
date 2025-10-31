"""
Add sample analysis data to the database for testing Analytics page.
"""
import sys
import os
from datetime import datetime, timedelta
import random
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from db import get_db, Analysis, Detection, Explanation
from sqlalchemy.orm import Session

# Defect types from your system
DEFECT_TYPES = [
    'Crack', 'Porosity', 'Slag Inclusion', 'Lack of Fusion', 
    'Undercut', 'Incomplete Penetration', 'No Defect'
]

def create_sample_analyses(db: Session, num_days: int = 30, analyses_per_day: int = 5):
    """Create sample analysis data over the past N days."""
    
    print(f"Creating {num_days * analyses_per_day} sample analyses...")
    
    for day_offset in range(num_days):
        date = datetime.now() - timedelta(days=day_offset)
        
        for _ in range(analyses_per_day):
            # Random defect type with weighted probability (more no-defect)
            has_defect = random.random() > 0.7  # 30% defect rate
            if has_defect:
                predicted_class = random.choice(DEFECT_TYPES[:-1])  # Exclude 'No Defect'
            else:
                predicted_class = 'No Defect'
            
            confidence = random.uniform(0.75, 0.99)
            
            # Create Analysis record
            analysis_id = str(uuid.uuid4())
            db_analysis = Analysis(
                image_id=analysis_id,
                filename=f"sample_weld_{day_offset}_{random.randint(1000, 9999)}.jpg",
                upload_timestamp=date - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                ),
                inference_time_ms=random.uniform(50, 200),
                status='completed',
                has_defects=has_defect,
                num_detections=1 if has_defect else 0,
                highest_severity='high' if has_defect else None,
                mean_confidence=confidence,
                model_version='YOLOv8s-cls'
            )
            db.add(db_analysis)
            db.flush()  # Get the ID without committing
            
            # Create Explanation record
            db_explanation = Explanation(
                analysis_id=db_analysis.id,
                method='gradcam',
                heatmap_base64='sample_heatmap_' + str(random.randint(1000, 9999)),
                confidence_score=confidence
            )
            db.add(db_explanation)
    
    try:
        db.commit()
        print(f"✅ Successfully created {num_days * analyses_per_day} sample analyses!")
        
        # Print summary
        total = db.query(Analysis).count()
        with_defects = db.query(Analysis).filter(Analysis.has_defects == True).count()
        defect_rate = (with_defects / total * 100) if total > 0 else 0
        
        print(f"\nDatabase Summary:")
        print(f"  Total Analyses: {total}")
        print(f"  With Defects: {with_defects}")
        print(f"  Defect Rate: {defect_rate:.1f}%")
        
        # Count by type
        print(f"\nDefect Type Distribution:")
        for defect_type in DEFECT_TYPES:
            count = db.query(Analysis).filter(Analysis.predicted_class == defect_type).count()
            if count > 0:
                print(f"  {defect_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise

if __name__ == "__main__":
    print("Adding sample data to database...\n")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check existing data
        existing_count = db.query(Analysis).count()
        print(f"Current analyses in database: {existing_count}")
        
        if existing_count > 0:
            response = input(f"\nDatabase already has {existing_count} analyses. Add more? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                sys.exit(0)
        
        # Add sample data
        create_sample_analyses(db, num_days=30, analyses_per_day=5)
        
        print("\n✅ Sample data added successfully!")
        print("You can now view the Analytics page with real data.")
        
    finally:
        db.close()
