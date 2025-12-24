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
    assigned_reviewer_id: Optional[str] = None  # For second opinion requests


class ReviewerInfo(BaseModel):
    id: str
    name: str
    email: Optional[str]
    role: str  # 'technician', 'project_chief', 'manager'
    
    class Config:
        from_attributes = True


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
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
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
    assigned_reviewer_name: Optional[str] = None
    image_base64: Optional[str] = None  # Base64 encoded image for preview
    created_by_name: Optional[str] = None  # Technician who uploaded


# === Endpoints ===

@router.get("/reviewers", response_model=List[ReviewerInfo])
async def get_available_reviewers(
    current_user_id: str = "system",  # TODO: Get from auth
    db: Session = Depends(get_db),
):
    """
    Get list of available reviewers (other technicians + project chief).
    
    Technicians can request review from:
    - Other technicians (peer review)
    - Their assigned project chief (escalation)
    """
    try:
        from sqlalchemy import text
        
        # Get current user's role and project chief
        user_query = text("""
            SELECT role, project_chief_id 
            FROM accounts 
            WHERE id = :user_id
        """)
        user_result = db.execute(user_query, {"user_id": current_user_id}).fetchone()
        
        if not user_result:
            return []
        
        user_role, project_chief_id = user_result
        
        # Get all technicians except current user + project chief
        reviewers_query = text("""
            SELECT id, name, email, role
            FROM accounts
            WHERE (role IN ('technician', 'project_chief') AND id != :user_id)
               OR (role = 'project_chief' AND id = :chief_id)
            ORDER BY role DESC, name ASC
        """)
        
        reviewers = db.execute(reviewers_query, {
            "user_id": current_user_id,
            "chief_id": project_chief_id or current_user_id
        }).fetchall()
        
        return [
            ReviewerInfo(
                id=str(r[0]),
                name=r[1],
                email=r[2],
                role=r[3] or 'technician'
            )
            for r in reviewers
        ]
        
    except Exception as e:
        logger.error(f"Failed to get reviewers: {e}", exc_info=True)
        return []


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
            image_base64 = None
            
            if analysis.detections and len(analysis.detections) > 0:
                first_detection = analysis.detections[0]
                defect_type = first_detection.class_name
                severity = analysis.highest_severity
            
            # Get image: prefer stored original, fallback to heatmap
            if analysis.image_base64:
                image_base64 = analysis.image_base64
            elif analysis.original_image_base64:
                # Use full image if preview not available
                image_base64 = analysis.original_image_base64[:50000] if len(analysis.original_image_base64) > 50000 else analysis.original_image_base64
            elif analysis.explanations and len(analysis.explanations) > 0:
                # Fallback to heatmap if no original image stored
                latest_explanation = analysis.explanations[0]
                if latest_explanation.heatmap_base64:
                    image_base64 = latest_explanation.heatmap_base64
            
            queue_items.append(ReviewQueueItem(
                analysis_id=analysis.image_id,  # Use image_id (UUID string) not id (integer)
                image_name=analysis.filename,
                upload_timestamp=analysis.upload_timestamp,
                defect_type=defect_type,
                severity=severity,
                confidence=confidence,
                review_status="pending",  # TODO: Add review status to DB
                reviewer_id=None,
                image_base64=image_base64,
            ))
        
        return queue_items
        
    except Exception as e:
        logger.error(f"Failed to get review queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=ReviewResponse)
async def submit_review(
    review: ReviewCreate,
    current_user_id: str = "system",
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),  # TODO: Enable authentication
):
    """
    Submit a review for an analysis with hierarchical reviewer assignment.
    
    Status options:
    - approved: AI prediction is correct
    - rejected: AI prediction is incorrect
    - needs_second_opinion: Escalate to assigned reviewer (peer or project chief)
    
    Hierarchical Review Workflow:
    - Technician uploads image and runs analysis
    - Technician can request second opinion from:
      * Other technicians (peer review)
      * Their assigned project chief (escalation)
    - assigned_reviewer_id determines who receives the review request
    """
    try:
        # Verify analysis exists (analysis_id is image_id, a UUID string)
        analysis = db.query(Analysis).filter(Analysis.image_id == review.analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get current user info
        user_query = text("SELECT name, role FROM accounts WHERE id = :user_id")
        user_result = db.execute(user_query, {"user_id": current_user_id}).fetchone()
        reviewer_name = user_result[0] if user_result else "System"
        user_role = user_result[1] if user_result else None
        
        # Get assigned reviewer info if specified
        assigned_reviewer_name = None
        if review.assigned_reviewer_id:
            assigned_query = text("SELECT name, role FROM accounts WHERE id = :reviewer_id")
            assigned_result = db.execute(assigned_query, {"reviewer_id": review.assigned_reviewer_id}).fetchone()
            assigned_reviewer_name = assigned_result[0] if assigned_result else None
            assigned_role = assigned_result[1] if assigned_result else None
            
            logger.info(f"Review assigned to: {assigned_reviewer_name} ({assigned_role})")
        
        # Create review record
        # TODO: Add Review model to database with assigned_reviewer_id column
        review_record = {
            "id": f"REV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "analysis_id": review.analysis_id,
            "reviewer_id": current_user_id,
            "reviewer_name": reviewer_name,
            "assigned_reviewer_id": review.assigned_reviewer_id,
            "assigned_reviewer_name": assigned_reviewer_name,
            "status": review.status,
            "comments": review.comments,
            "reviewer_notes": review.reviewer_notes,
            "created_at": datetime.now(),
        }
        
        # Log hierarchical review action
        if review.status == "needs_second_opinion" and review.assigned_reviewer_id:
            logger.info(f"🔄 Hierarchical review requested: {reviewer_name} → {assigned_reviewer_name}")
        else:
            logger.info(f"✅ Review submitted: {reviewer_name} marked as {review.status}")
        
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
