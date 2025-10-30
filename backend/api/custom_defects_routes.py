"""
API routes for Custom Defect Types, Training, and Active Learning.

This module provides endpoints for:
- Creating and managing custom defect categories
- Managing training datasets and samples
- Triggering model retraining
- Active learning suggestions
- Model versioning and deployment
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import logging

from db import get_db
from db.models import (
    CustomDefectType,
    TrainingSample,
    ModelVersion,
    TrainingDataset,
    TrainingJob,
    ActiveLearningQueue,
    Analysis,
    Review
)
from api.schemas import (
    CustomDefectTypeCreate,
    CustomDefectTypeUpdate,
    CustomDefectTypeResponse,
    TrainingSampleCreate,
    TrainingSampleResponse,
    ModelVersionResponse,
    TrainingDatasetCreate,
    TrainingDatasetResponse,
    TrainingJobCreate,
    TrainingJobResponse,
    TrainingJobProgress,
    ActiveLearningSuggestion,
    ModelDeploymentRequest,
    ModelRollbackRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/xai-qc/custom-defects",
    tags=["Custom Defect Types & Training"]
)


# ===== Custom Defect Type Management =====

@router.post("/types", response_model=CustomDefectTypeResponse, status_code=201)
async def create_custom_defect_type(
    defect_type: CustomDefectTypeCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)  # TODO: Enable auth
):
    """
    Create a new custom defect type category.
    
    **Example**: Creating "Weld Mismatch" (WM) as a custom defect type.
    """
    # Check for duplicate names/codes
    existing = db.query(CustomDefectType).filter(
        (CustomDefectType.name == defect_type.name) | 
        (CustomDefectType.code == defect_type.code)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Defect type with name '{defect_type.name}' or code '{defect_type.code}' already exists"
        )
    
    # Create new defect type
    db_defect_type = CustomDefectType(
        name=defect_type.name,
        code=defect_type.code,
        description=defect_type.description,
        severity_default=defect_type.severity_default,
        expected_features=defect_type.expected_features,
        color=defect_type.color,
        compliance_standards=defect_type.compliance_standards,
        min_samples_required=defect_type.min_samples_required,
        created_by="system",  # Replace with current_user.id when auth enabled
        requires_retraining=True  # New type requires model retraining
    )
    
    db.add(db_defect_type)
    db.commit()
    db.refresh(db_defect_type)
    
    logger.info(f"Created custom defect type: {db_defect_type.name} ({db_defect_type.code})")
    
    return db_defect_type


@router.get("/types", response_model=List[CustomDefectTypeResponse])
async def list_custom_defect_types(
    active_only: bool = Query(True, description="Only show active defect types"),
    db: Session = Depends(get_db)
):
    """
    List all custom defect types.
    
    **Filters**:
    - `active_only`: If True, only returns active types (default: True)
    """
    query = db.query(CustomDefectType)
    
    if active_only:
        query = query.filter(CustomDefectType.is_active == True)
    
    defect_types = query.order_by(CustomDefectType.created_at.desc()).all()
    
    return defect_types


@router.get("/types/{defect_type_id}", response_model=CustomDefectTypeResponse)
async def get_custom_defect_type(
    defect_type_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific custom defect type by ID."""
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == defect_type_id).first()
    
    if not defect_type:
        raise HTTPException(status_code=404, detail="Custom defect type not found")
    
    return defect_type


@router.patch("/types/{defect_type_id}", response_model=CustomDefectTypeResponse)
async def update_custom_defect_type(
    defect_type_id: int,
    updates: CustomDefectTypeUpdate,
    db: Session = Depends(get_db)
):
    """Update a custom defect type."""
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == defect_type_id).first()
    
    if not defect_type:
        raise HTTPException(status_code=404, detail="Custom defect type not found")
    
    # Apply updates
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(defect_type, field, value)
    
    defect_type.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(defect_type)
    
    logger.info(f"Updated custom defect type: {defect_type.name}")
    
    return defect_type


@router.delete("/types/{defect_type_id}", status_code=204)
async def delete_custom_defect_type(
    defect_type_id: int,
    force: bool = Query(False, description="Force delete even with existing samples"),
    db: Session = Depends(get_db)
):
    """
    Delete a custom defect type.
    
    **Warning**: This will cascade delete all training samples unless `force=True`.
    """
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == defect_type_id).first()
    
    if not defect_type:
        raise HTTPException(status_code=404, detail="Custom defect type not found")
    
    # Check for existing samples
    sample_count = db.query(TrainingSample).filter(
        TrainingSample.defect_type_id == defect_type_id
    ).count()
    
    if sample_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete defect type with {sample_count} training samples. Use force=true to override."
        )
    
    db.delete(defect_type)
    db.commit()
    
    logger.warning(f"Deleted custom defect type: {defect_type.name} (ID: {defect_type_id})")
    
    return None


# ===== Training Sample Management =====

@router.post("/samples", response_model=TrainingSampleResponse, status_code=201)
async def create_training_sample(
    sample: TrainingSampleCreate,
    db: Session = Depends(get_db)
):
    """
    Add a labeled training sample for a custom defect type.
    
    **Use Cases**:
    - Manual image upload with annotations
    - Converting review corrections to training data
    - Active learning suggestions being labeled
    """
    # Verify defect type exists
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == sample.defect_type_id).first()
    
    if not defect_type:
        raise HTTPException(status_code=404, detail="Custom defect type not found")
    
    # Create training sample
    db_sample = TrainingSample(
        defect_type_id=sample.defect_type_id,
        image_path=sample.image_path,
        image_id=sample.image_id,
        annotations=sample.annotations,
        annotation_format=sample.annotation_format,
        source=sample.source,
        quality_score=sample.quality_score,
        training_set=sample.training_set,
        labeled_by="system"  # Replace with current_user.id when auth enabled
    )
    
    db.add(db_sample)
    
    # Increment sample count for defect type
    defect_type.current_sample_count += 1
    defect_type.requires_retraining = True  # New data requires retraining
    
    db.commit()
    db.refresh(db_sample)
    
    logger.info(f"Added training sample for defect type {defect_type.name} (total: {defect_type.current_sample_count})")
    
    return db_sample


@router.get("/samples", response_model=List[TrainingSampleResponse])
async def list_training_samples(
    defect_type_id: Optional[int] = Query(None, description="Filter by defect type"),
    training_set: Optional[str] = Query(None, description="Filter by train/val/test set"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """List training samples with optional filters."""
    query = db.query(TrainingSample)
    
    if defect_type_id:
        query = query.filter(TrainingSample.defect_type_id == defect_type_id)
    
    if training_set:
        query = query.filter(TrainingSample.training_set == training_set)
    
    samples = query.order_by(TrainingSample.created_at.desc()).offset(skip).limit(limit).all()
    
    return samples


@router.get("/samples/{sample_id}", response_model=TrainingSampleResponse)
async def get_training_sample(
    sample_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific training sample by ID."""
    sample = db.query(TrainingSample).filter(TrainingSample.id == sample_id).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Training sample not found")
    
    return sample


@router.delete("/samples/{sample_id}", status_code=204)
async def delete_training_sample(
    sample_id: int,
    db: Session = Depends(get_db)
):
    """Delete a training sample."""
    sample = db.query(TrainingSample).filter(TrainingSample.id == sample_id).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Training sample not found")
    
    # Decrement defect type sample count
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == sample.defect_type_id).first()
    if defect_type:
        defect_type.current_sample_count = max(0, defect_type.current_sample_count - 1)
    
    db.delete(sample)
    db.commit()
    
    return None


# ===== Training Dataset Management =====

@router.post("/datasets", response_model=TrainingDatasetResponse, status_code=201)
async def create_training_dataset(
    dataset: TrainingDatasetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new training dataset snapshot.
    
    This captures the current state of training samples for model training.
    """
    db_dataset = TrainingDataset(
        name=dataset.name,
        description=dataset.description,
        dataset_path=dataset.dataset_path,
        total_images=dataset.total_images,
        train_images=dataset.train_images,
        val_images=dataset.val_images,
        test_images=dataset.test_images,
        class_distribution=dataset.class_distribution,
        includes_custom_types=dataset.includes_custom_types,
        custom_types_included=dataset.custom_types_included,
        augmentation_config=dataset.augmentation_config,
        created_by="system"  # Replace with current_user.id
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    logger.info(f"Created training dataset: {db_dataset.name} ({db_dataset.total_images} images)")
    
    return db_dataset


@router.get("/datasets", response_model=List[TrainingDatasetResponse])
async def list_training_datasets(
    db: Session = Depends(get_db)
):
    """List all training datasets."""
    datasets = db.query(TrainingDataset).order_by(TrainingDataset.created_at.desc()).all()
    return datasets


@router.get("/datasets/{dataset_id}", response_model=TrainingDatasetResponse)
async def get_training_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific training dataset."""
    dataset = db.query(TrainingDataset).filter(TrainingDataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Training dataset not found")
    
    return dataset


# ===== Model Training & Versioning =====

@router.post("/train", response_model=TrainingJobResponse, status_code=202)
async def start_training_job(
    job_config: TrainingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a model training job (runs in background).
    
    **Job Types**:
    - `full_training`: Train from scratch
    - `fine_tuning`: Fine-tune existing model
    - `transfer_learning`: Transfer learning from base model
    
    **Returns**: Training job ID for monitoring progress.
    """
    # Verify model version exists
    model_version = db.query(ModelVersion).filter(ModelVersion.id == job_config.model_version_id).first()
    
    if not model_version:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    # Create training job
    db_job = TrainingJob(
        model_version_id=job_config.model_version_id,
        job_type=job_config.job_type,
        hyperparameters=job_config.hyperparameters,
        total_epochs=job_config.total_epochs,
        status="pending"
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    # Schedule background training task
    # background_tasks.add_task(run_training_job, db_job.id)
    
    logger.info(f"Started training job {db_job.id} for model version {model_version.version_number}")
    
    return db_job


@router.get("/training-jobs", response_model=List[TrainingJobResponse])
async def list_training_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """List training jobs with optional status filter."""
    query = db.query(TrainingJob)
    
    if status:
        query = query.filter(TrainingJob.status == status)
    
    jobs = query.order_by(TrainingJob.created_at.desc()).limit(limit).all()
    
    return jobs


@router.get("/training-jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get training job details including real-time progress."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return job


@router.get("/training-jobs/{job_id}/progress", response_model=TrainingJobProgress)
async def get_training_progress(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get real-time training progress for monitoring dashboard.
    
    **Poll this endpoint** to update training visualization.
    """
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    latest_metrics = {
        "train_loss": job.latest_train_loss,
        "val_loss": job.latest_val_loss,
        "accuracy": job.latest_accuracy,
        "map50": job.latest_map50,
    }
    
    return TrainingJobProgress(
        job_id=job.id,
        status=job.status,
        progress_percent=job.progress_percent,
        current_epoch=job.current_epoch,
        latest_metrics=latest_metrics,
        estimated_time_remaining=job.estimated_time_remaining_minutes,
        timestamp=datetime.utcnow()
    )


@router.post("/training-jobs/{job_id}/cancel", status_code=200)
async def cancel_training_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Cancel a running training job."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    if job.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status '{job.status}'")
    
    job.status = "cancelled"
    db.commit()
    
    logger.info(f"Cancelled training job {job_id}")
    
    return {"message": "Training job cancelled successfully"}


# ===== Model Versions =====

@router.get("/models", response_model=List[ModelVersionResponse])
async def list_model_versions(
    active_only: bool = Query(False, description="Only show active models"),
    db: Session = Depends(get_db)
):
    """List all model versions."""
    query = db.query(ModelVersion)
    
    if active_only:
        query = query.filter(ModelVersion.is_active == True)
    
    models = query.order_by(ModelVersion.created_at.desc()).all()
    
    return models


@router.get("/models/{model_id}", response_model=ModelVersionResponse)
async def get_model_version(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific model version."""
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    return model


@router.get("/models/active/current", response_model=ModelVersionResponse)
async def get_active_model(
    db: Session = Depends(get_db)
):
    """Get the currently active/deployed model."""
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    
    if not active_model:
        raise HTTPException(status_code=404, detail="No active model found")
    
    return active_model


@router.post("/models/deploy", status_code=200)
async def deploy_model_version(
    deployment: ModelDeploymentRequest,
    db: Session = Depends(get_db)
):
    """
    Deploy a trained model version to production.
    
    **Strategies**:
    - `replace`: Immediately replace current model
    - `canary`: Gradual rollout (future)
    - `blue_green`: Parallel deployment (future)
    """
    # Get model to deploy
    new_model = db.query(ModelVersion).filter(ModelVersion.id == deployment.model_version_id).first()
    
    if not new_model:
        raise HTTPException(status_code=404, detail="Model version not found")
    
    if new_model.deployment_status != "trained":
        raise HTTPException(status_code=400, detail=f"Model status is '{new_model.deployment_status}', must be 'trained'")
    
    # Deactivate current active model
    current_active = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    if current_active:
        current_active.is_active = False
        logger.info(f"Deactivated previous model: {current_active.version_number}")
    
    # Activate new model
    new_model.is_active = True
    new_model.deployment_status = "deployed"
    new_model.deployed_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Deployed model version: {new_model.version_number}")
    
    return {
        "message": f"Model {new_model.version_number} deployed successfully",
        "previous_model": current_active.version_number if current_active else None,
        "new_model": new_model.version_number
    }


@router.post("/models/rollback", status_code=200)
async def rollback_model_version(
    rollback: ModelRollbackRequest,
    db: Session = Depends(get_db)
):
    """
    Rollback to a previous model version.
    
    **Use Case**: New model underperforms, rollback to stable version.
    """
    # Get target model
    target_model = db.query(ModelVersion).filter(ModelVersion.id == rollback.target_version_id).first()
    
    if not target_model:
        raise HTTPException(status_code=404, detail="Target model version not found")
    
    if target_model.deployment_status not in ["deployed", "archived"]:
        raise HTTPException(status_code=400, detail="Can only rollback to previously deployed models")
    
    # Deactivate current model
    current_active = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    if current_active:
        current_active.is_active = False
        current_active.deployment_status = "archived"
    
    # Reactivate target model
    target_model.is_active = True
    target_model.deployment_status = "deployed"
    target_model.deployed_at = datetime.utcnow()
    
    db.commit()
    
    logger.warning(f"Rolled back to model version: {target_model.version_number}. Reason: {rollback.reason}")
    
    return {
        "message": f"Rolled back to model {target_model.version_number}",
        "previous_model": current_active.version_number if current_active else None,
        "current_model": target_model.version_number,
        "reason": rollback.reason
    }


# ===== Active Learning =====

@router.get("/active-learning/suggestions", response_model=List[ActiveLearningSuggestion])
async def get_active_learning_suggestions(
    limit: int = Query(20, le=100, description="Number of suggestions to return"),
    min_uncertainty: float = Query(0.3, ge=0.0, le=1.0, description="Minimum uncertainty score"),
    db: Session = Depends(get_db)
):
    """
    Get images suggested by active learning for labeling.
    
    **Active Learning**: System identifies uncertain predictions that would most improve the model.
    
    **Returns**: Images ranked by uncertainty/priority score.
    """
    suggestions = db.query(ActiveLearningQueue).filter(
        ActiveLearningQueue.status == "pending",
        ActiveLearningQueue.uncertainty_score >= min_uncertainty
    ).order_by(ActiveLearningQueue.priority_score.desc()).limit(limit).all()
    
    # Join with Analysis to get image_id
    results = []
    for suggestion in suggestions:
        analysis = db.query(Analysis).filter(Analysis.id == suggestion.analysis_id).first()
        if analysis:
            results.append(ActiveLearningSuggestion(
                id=suggestion.id,
                analysis_id=suggestion.analysis_id,
                image_id=analysis.image_id,
                uncertainty_score=suggestion.uncertainty_score,
                priority_score=suggestion.priority_score,
                selection_method=suggestion.selection_method,
                suggested_defect_types=suggestion.suggested_defect_types or [],
                status=suggestion.status,
                added_at=suggestion.added_at
            ))
    
    return results


@router.post("/active-learning/{suggestion_id}/accept", status_code=200)
async def accept_active_learning_suggestion(
    suggestion_id: int,
    sample: TrainingSampleCreate,
    db: Session = Depends(get_db)
):
    """
    Accept an active learning suggestion and add it as a training sample.
    
    **Workflow**:
    1. User reviews suggested image
    2. User provides correct labels/annotations
    3. Image is added to training dataset
    4. Active learning queue item is marked as labeled
    """
    # Get suggestion
    suggestion = db.query(ActiveLearningQueue).filter(ActiveLearningQueue.id == suggestion_id).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Active learning suggestion not found")
    
    # Create training sample
    db_sample = TrainingSample(
        defect_type_id=sample.defect_type_id,
        image_path=sample.image_path,
        image_id=sample.image_id,
        annotations=sample.annotations,
        annotation_format=sample.annotation_format,
        source="active_learning",
        quality_score=1.0 - suggestion.uncertainty_score,  # Higher uncertainty = lower quality
        labeled_by="system"
    )
    
    db.add(db_sample)
    
    # Update suggestion status
    suggestion.status = "labeled"
    suggestion.reviewed_at = datetime.utcnow()
    
    # Increment defect type sample count
    defect_type = db.query(CustomDefectType).filter(CustomDefectType.id == sample.defect_type_id).first()
    if defect_type:
        defect_type.current_sample_count += 1
        defect_type.requires_retraining = True
    
    db.commit()
    
    logger.info(f"Accepted active learning suggestion {suggestion_id}, added as training sample")
    
    return {"message": "Training sample created from active learning suggestion"}


@router.post("/active-learning/{suggestion_id}/skip", status_code=200)
async def skip_active_learning_suggestion(
    suggestion_id: int,
    reason: Optional[str] = Query(None, description="Reason for skipping"),
    db: Session = Depends(get_db)
):
    """Skip an active learning suggestion."""
    suggestion = db.query(ActiveLearningQueue).filter(ActiveLearningQueue.id == suggestion_id).first()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Active learning suggestion not found")
    
    suggestion.status = "skipped"
    suggestion.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Active learning suggestion skipped"}


# ===== Statistics & Monitoring =====

@router.get("/stats/summary", status_code=200)
async def get_custom_defects_stats(
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for custom defect types and training.
    
    **Includes**:
    - Total custom defect types
    - Total training samples
    - Training readiness status
    - Active model info
    """
    # Count custom defect types
    total_defect_types = db.query(CustomDefectType).filter(CustomDefectType.is_active == True).count()
    
    # Count training samples
    total_samples = db.query(TrainingSample).count()
    
    # Get defect types needing more samples
    defect_types_needing_samples = db.query(CustomDefectType).filter(
        CustomDefectType.is_active == True,
        CustomDefectType.current_sample_count < CustomDefectType.min_samples_required
    ).all()
    
    # Get active model
    active_model = db.query(ModelVersion).filter(ModelVersion.is_active == True).first()
    
    # Check if retraining needed
    retraining_needed = db.query(CustomDefectType).filter(
        CustomDefectType.requires_retraining == True
    ).count() > 0
    
    # Count active learning queue
    active_learning_pending = db.query(ActiveLearningQueue).filter(
        ActiveLearningQueue.status == "pending"
    ).count()
    
    # Count running training jobs
    running_jobs = db.query(TrainingJob).filter(
        TrainingJob.status == "running"
    ).count()
    
    return {
        "custom_defect_types": {
            "total": total_defect_types,
            "needing_more_samples": len(defect_types_needing_samples),
            "ready_for_training": total_defect_types - len(defect_types_needing_samples)
        },
        "training_samples": {
            "total": total_samples,
            "by_set": {
                "train": db.query(TrainingSample).filter(TrainingSample.training_set == "train").count(),
                "val": db.query(TrainingSample).filter(TrainingSample.training_set == "val").count(),
                "test": db.query(TrainingSample).filter(TrainingSample.training_set == "test").count()
            }
        },
        "model": {
            "active_version": active_model.version_number if active_model else None,
            "total_versions": db.query(ModelVersion).count(),
            "retraining_needed": retraining_needed
        },
        "active_learning": {
            "pending_suggestions": active_learning_pending
        },
        "training_jobs": {
            "running": running_jobs,
            "total": db.query(TrainingJob).count()
        }
    }
