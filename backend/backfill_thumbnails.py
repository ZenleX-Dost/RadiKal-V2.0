"""
Backfill thumbnails for existing analyses.

This script regenerates proper thumbnails from original images stored in the database.
"""

import io
import base64
import logging
from PIL import Image
from sqlalchemy.orm import Session

from db import get_db, Analysis, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_thumbnail(original_b64: str, width: int = 400) -> str:
    """Create a properly sized thumbnail from base64 image."""
    try:
        # Decode the original image
        img_data = base64.b64decode(original_b64)
        pil_img = Image.open(io.BytesIO(img_data))
        
        # Calculate new height maintaining aspect ratio
        thumb_height = int(pil_img.height * (width / pil_img.width))
        pil_img.thumbnail((width, thumb_height), Image.Resampling.LANCZOS)
        
        # Convert to JPEG for smaller size
        if pil_img.mode in ('RGBA', 'P'):
            pil_img = pil_img.convert('RGB')
        
        thumb_buffer = io.BytesIO()
        pil_img.save(thumb_buffer, format='JPEG', quality=75)
        thumb_buffer.seek(0)
        
        return base64.b64encode(thumb_buffer.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}")
        return None


def backfill_thumbnails():
    """Update all analyses with proper thumbnails."""
    db = next(get_db())
    
    try:
        # Get analyses that have original image but might need thumbnail update
        analyses = db.query(Analysis).filter(
            Analysis.original_image_base64.isnot(None)
        ).all()
        
        logger.info(f"Found {len(analyses)} analyses with original images")
        
        updated = 0
        for analysis in analyses:
            # Check if current thumbnail is corrupted (truncated) or missing
            needs_update = False
            
            if not analysis.image_base64:
                needs_update = True
            elif len(analysis.image_base64) == 50000:  # Truncated
                needs_update = True
            else:
                # Try to decode to check if valid
                try:
                    img_data = base64.b64decode(analysis.image_base64)
                    Image.open(io.BytesIO(img_data))
                except:
                    needs_update = True
            
            if needs_update:
                thumbnail = create_thumbnail(analysis.original_image_base64)
                if thumbnail:
                    analysis.image_base64 = thumbnail
                    updated += 1
                    logger.info(f"Updated thumbnail for analysis {analysis.id} ({analysis.image_id})")
        
        db.commit()
        logger.info(f"[OK] Updated {updated} thumbnails successfully")
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_thumbnails()
