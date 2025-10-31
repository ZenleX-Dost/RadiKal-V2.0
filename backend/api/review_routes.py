"""
Collaborative Review System API Routes

Enables multiple inspectors to:
- Review AI predictions
- Approve or reject analyses
- Add comments and annotations
- Track review status and history
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from db import get_db, Analysis
# from api.middleware import get_current_user  # TODO: Enable authentication

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xai-qc/reviews", tags=["Review System"])


# === Schemas ===

class ReviewCreate(BaseModel):
    analysis_id: str
    status: str  # 'approved', 'rejected', 'needs_second_opinion'
    comments: Optional[str] = None
    reviewer_notes: Optional[str] = None


class Annotation(BaseModel):
    x: float
    y: float
    width: float
    height: float
    note: str
    annotation_type: str  # 'correction', 'highlight', 'question'


class AnnotationCreate(BaseModel):
    review_id: str
    annotations: List[Annotation]


class ReviewResponse(BaseModel):
    id: str
    analysis_id: str
    reviewer_id: str
    reviewer_name: str
    status: str
    comments: Optional[str]
    reviewer_notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewQueueItem(BaseModel):
    analysis_id: str
    image_name: str
    upload_timestamp: datetime
    defect_type: Optional[str]
    severity: Optional[str]
    confidence: float
    review_status: str  # 'pending', 'in_progress', 'completed'
    reviewer_id: Optional[str]


# === Endpoints ===

@router.get("/queue", response_model=List[ReviewQueueItem])
async def get_review_queue(
    status: str = "pending",
    limit: int = 50,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),  # TODO: Enable authentication
):
    """
    Get queue of analyses pending review.
    
    Filters:
    - status: pending, in_progress, completed
    - limit: max items to return
    """
    try:
        # Query analyses that need review
        analyses = db.query(Analysis).filter(
            Analysis.status == "completed"
        ).order_by(Analysis.upload_timestamp.desc()).limit(limit).all()
        
        queue_items = []
        for analysis in analyses:
            # Determine defect type and severity
            defect_type = None
            severity = None
            confidence = analysis.mean_confidence or 0.0
            
            if analysis.detections and len(analysis.detections) > 0:
                first_detection = analysis.detections[0]
                defect_type = first_detection.class_name
                severity = analysis.highest_severity
            
            queue_items.append(ReviewQueueItem(
                analysis_id=analysis.image_id,  # Use image_id (UUID string) not id (integer)
                image_name=analysis.filename,
                upload_timestamp=analysis.upload_timestamp,
                defect_type=defect_type,
                severity=severity,
                confidence=confidence,
                review_status="pending",  # TODO: Add review status to DB
                reviewer_id=None,
            ))
        
        return queue_items
        
    except Exception as e:
        logger.error(f"Failed to get review queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=ReviewResponse)
async def submit_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),  # TODO: Enable authentication
):
    """
    Submit a review for an analysis.
    
    Status options:
    - approved: AI prediction is correct
    - rejected: AI prediction is incorrect
    - needs_second_opinion: Escalate to senior inspector
    """
    try:
        # Verify analysis exists
        analysis = db.query(Analysis).filter(Analysis.id == review.analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Create review record
        # TODO: Add Review model to database
        reviewer_id = 'system'  # TODO: Get from current_user when auth is enabled
        reviewer_name = 'System'  # TODO: Get from current_user when auth is enabled
        
        review_record = {
            "id": f"REV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "analysis_id": review.analysis_id,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "status": review.status,
            "comments": review.comments,
            "reviewer_notes": review.reviewer_notes,
            "created_at": datetime.now(),
        }
        
        logger.info(f"Review submitted for analysis {review.analysis_id} by {reviewer_name}")
        logger.info(f"Review status: {review.status}")
        
        return ReviewResponse(**review_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotations", response_model=dict)
async def add_annotations(
    annotation_data: AnnotationCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),  # TODO: Enable authentication
):
    """
    Add annotations to a review.
    
    Annotations can be:
    - corrections: Mark incorrect AI predictions
    - highlights: Emphasize areas of interest
    - questions: Request clarification
    """
    try:
        # TODO: Store annotations in database
        logger.info(f"Adding {len(annotation_data.annotations)} annotations to review {annotation_data.review_id}")
        
        return {
            "success": True,
            "review_id": annotation_data.review_id,
            "annotations_added": len(annotation_data.annotations),
        }
        
    except Exception as e:
        logger.error(f"Failed to add annotations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{analysis_id}", response_model=List[ReviewResponse])
async def get_review_history(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    Get review history for a specific analysis.
    
    Shows all reviews, approvals, and rejections.
    """
    try:
        # TODO: Query reviews from database
        logger.info(f"Fetching review history for analysis {analysis_id}")
        
        # Placeholder
        return []
        
    except Exception as e:
        logger.error(f"Failed to get review history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_review_stats(
    reviewer_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get review statistics.
    
    Shows:
    - Total reviews
    - Approval rate
    - Average review time
    - Disagreement rate
    """
    try:
        # TODO: Calculate from database
        stats = {
            "total_reviews": 0,
            "approved": 0,
            "rejected": 0,
            "second_opinions": 0,
            "approval_rate": 0.0,
            "avg_review_time_minutes": 0.0,
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get review stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-to-training", response_model=dict)
async def add_review_to_training(
    analysis_id: str,
    corrected_defect_type_id: int,
    confidence: float,
    db: Session = Depends(get_db),
):
    """
    Add a reviewed/corrected analysis to training samples.
    
    When an inspector corrects an AI prediction, this creates:
    1. A training sample with the corrected label
    2. An active learning queue entry for similar uncertain cases
    
    This enables the model to learn from human feedback.
    """
    try:
        from db import TrainingSample, CustomDefectType, ActiveLearningQueue
        
        # Verify analysis exists
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify defect type exists
        defect_type = db.query(CustomDefectType).filter(
            CustomDefectType.id == corrected_defect_type_id
        ).first()
        if not defect_type:
            raise HTTPException(status_code=404, detail="Defect type not found")
        
        # Check if sample already exists
        existing = db.query(TrainingSample).filter(
            TrainingSample.image_id == analysis_id
        ).first()
        
        if existing:
            logger.info(f"Training sample already exists for analysis {analysis_id}")
            return {
                "success": True,
                "message": "Training sample already exists",
                "sample_id": existing.id,
                "created": False,
            }
        
        # Create training sample
        training_sample = TrainingSample(
            defect_type_id=corrected_defect_type_id,
            image_path=analysis.image_path,
            image_id=analysis_id,
            annotations={
                "corrected_from_review": True,
                "original_prediction": analysis.predicted_class,
                "corrected_class": defect_type.name,
                "confidence": confidence,
            },
            annotation_format="review_correction",
            source="review",
            quality_score=confidence,
            used_in_training=False,
            training_set=None,
        )
        
        db.add(training_sample)
        
        # Update defect type sample count
        defect_type.current_sample_count += 1
        if defect_type.current_sample_count >= defect_type.min_samples_required:
            defect_type.requires_retraining = True
        
        # Analyze with active learning (if model was confident but wrong)
        if confidence < 0.7:  # Uncertain prediction
            # Check if already in queue
            existing_al = db.query(ActiveLearningQueue).filter(
                ActiveLearningQueue.analysis_id == analysis_id
            ).first()
            
            if not existing_al:
                al_entry = ActiveLearningQueue(
                    analysis_id=analysis_id,
                    uncertainty_score=1.0 - confidence,
                    confidence_variance=0.5,  # Placeholder
                    entropy=0.8,  # Placeholder
                    selection_method="review_correction",
                    priority_score=0.9,  # High priority for corrections
                    suggested_defect_types=[defect_type.name],
                    status="suggested",
                )
                db.add(al_entry)
        
        db.commit()
        db.refresh(training_sample)
        
        logger.info(
            f"Added review correction to training: analysis={analysis_id}, "
            f"defect_type={defect_type.name}, sample_id={training_sample.id}"
        )
        
        return {
            "success": True,
            "message": "Successfully added to training samples",
            "sample_id": training_sample.id,
            "defect_type": defect_type.name,
            "current_samples": defect_type.current_sample_count,
            "min_required": defect_type.min_samples_required,
            "ready_for_training": defect_type.current_sample_count >= defect_type.min_samples_required,
            "created": True,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add review to training: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
