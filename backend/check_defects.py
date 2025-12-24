"""Check what defect types are actually in the database."""
import sys
sys.path.append('.')

from db import get_db, Analysis, Detection
from sqlalchemy.orm import joinedload

db = next(get_db())

# Get all detections
detections = db.query(Detection).join(Analysis).filter(
    Analysis.status == 'completed'
).all()

print(f"\n✅ Total detections found: {len(detections)}\n")

# Group by class_name
from collections import Counter
class_counts = Counter(d.class_name for d in detections)

print("Defect Type Distribution:")
for class_name, count in class_counts.items():
    print(f"  {class_name}: {count}")

print("\nFirst 10 detections:")
for d in detections[:10]:
    print(f"  Detection {d.id}: class=\"{d.class_name}\" (label={d.label}), confidence={d.confidence:.4f}")
