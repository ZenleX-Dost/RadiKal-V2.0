"""
Test script to verify database setup and basic operations
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db import init_db, get_db, Analysis, Detection, Explanation
from datetime import datetime
import uuid

def test_database():
    """Test database initialization and basic operations"""
    
    print("=" * 60)
    print("Testing Database Setup")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("✅ Database initialized successfully")
        db_path = backend_dir / "data" / "radikal.db"
        if db_path.exists():
            print(f"✅ Database file created at: {db_path}")
            print(f"   File size: {db_path.stat().st_size} bytes")
        else:
            print(f"❌ Database file not found at: {db_path}")
            return False
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    # Step 2: Create a test analysis
    print("\n2. Creating test analysis...")
    try:
        db = next(get_db())
        
        # Create analysis
        image_id = str(uuid.uuid4())
        analysis = Analysis(
            image_id=image_id,
            filename="test_image.png",
            upload_timestamp=datetime.utcnow(),
            num_detections=2,
            has_defects=True,
            highest_severity="Difetto1",
            mean_confidence=0.92,
            mean_uncertainty=0.08,
            inference_time_ms=145.5,
            status="completed"
        )
        db.add(analysis)
        db.flush()
        
        print(f"✅ Created analysis record (ID: {analysis.id}, Image ID: {image_id})")
        
        # Create detections
        detection1 = Detection(
            analysis_id=analysis.id,
            x1=100, y1=100, x2=200, y2=200,
            confidence=0.95,
            label=0,
            class_name="Difetto1",
            severity="high"
        )
        detection2 = Detection(
            analysis_id=analysis.id,
            x1=300, y1=150, x2=400, y2=250,
            confidence=0.89,
            label=1,
            class_name="Difetto2",
            severity="medium"
        )
        db.add(detection1)
        db.add(detection2)
        db.flush()
        
        print(f"✅ Created {2} detection records")
        
        # Create explanation
        explanation = Explanation(
            analysis_id=analysis.id,
            method="GradCAM",
            confidence_score=0.92,
            heatmap_base64="fake_base64_data_for_testing"
        )
        db.add(explanation)
        
        db.commit()
        print("✅ All records committed to database")
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    # Step 3: Query the data
    print("\n3. Querying database...")
    try:
        db = next(get_db())
        
        # Query analyses
        analyses = db.query(Analysis).all()
        print(f"✅ Found {len(analyses)} analysis records")
        
        for analysis in analyses:
            print(f"   - {analysis.filename}: {analysis.num_detections} detections, "
                  f"confidence={analysis.mean_confidence:.2f}")
            
            # Query detections for this analysis
            detections = db.query(Detection).filter(Detection.analysis_id == analysis.id).all()
            print(f"     → {len(detections)} detections in database")
            
            # Query explanations
            explanations = db.query(Explanation).filter(Explanation.analysis_id == analysis.id).all()
            print(f"     → {len(explanations)} explanations in database")
        
        db.close()
        print("✅ Query successful")
        
    except Exception as e:
        print(f"❌ Failed to query database: {e}")
        return False
    
    # Step 4: Test pagination query (like /history endpoint)
    print("\n4. Testing pagination query...")
    try:
        db = next(get_db())
        
        page = 1
        page_size = 20
        offset = (page - 1) * page_size
        
        query = db.query(Analysis).order_by(Analysis.upload_timestamp.desc())
        total_count = query.count()
        analyses = query.offset(offset).limit(page_size).all()
        has_more = (offset + len(analyses)) < total_count
        
        print(f"✅ Pagination works: {len(analyses)} results, total={total_count}, has_more={has_more}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Failed pagination test: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All database tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
