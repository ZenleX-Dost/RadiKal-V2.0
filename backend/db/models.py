"""
Database models for RadiKal XAI Quality Control system.

This module defines SQLAlchemy models for persisting analysis history,
detection results, and XAI explanations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Analysis(Base):
    """
    Main analysis record - one per uploaded image.
    """
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Image metadata
    image_width = Column(Integer)
    image_height = Column(Integer)
    image_size_bytes = Column(Integer)
    
    # Analysis results summary
    num_detections = Column(Integer, default=0)
    has_defects = Column(Boolean, default=False)
    highest_severity = Column(String)  # critical, high, medium, low
    mean_confidence = Column(Float)
    mean_uncertainty = Column(Float, default=0.0)
    
    # Processing info
    inference_time_ms = Column(Float)
    model_version = Column(String)
    status = Column(String, default="completed")  # completed, failed, processing
    
    # Relationships
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="analysis", cascade="all, delete-orphan")


class Detection(Base):
    """
    Individual detection/bounding box from YOLOv8.
    """
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    
    # Bounding box coordinates
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    
    # Detection metadata
    confidence = Column(Float, nullable=False)
    label = Column(Integer, nullable=False)  # Class index
    class_name = Column(String, nullable=False)  # Human-readable class name
    severity = Column(String)  # critical, high, medium, low
    
    # Relationship
    analysis = relationship("Analysis", back_populates="detections")


class Explanation(Base):
    """
    XAI explanation heatmap for an analysis.
    """
    __tablename__ = "explanations"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    
    # XAI method info
    method = Column(String, nullable=False)  # gradcam, lime, shap, integrated_gradients
    confidence_score = Column(Float)
    
    # Heatmap stored as base64 (could also store file path)
    heatmap_base64 = Column(String)  # Base64 encoded PNG
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="explanations")


class SystemMetrics(Base):
    """
    System-wide metrics snapshots over time.
    """
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Business metrics
    true_positives = Column(Integer, default=0)
    true_negatives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    
    # Detection metrics
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    map50 = Column(Float)
    auroc = Column(Float)
    
    # Segmentation metrics
    mean_iou = Column(Float)
    mean_dice = Column(Float)
    pixel_accuracy = Column(Float)
    
    # Summary
    total_analyses = Column(Integer, default=0)
    period_start = Column(DateTime)
    period_end = Column(DateTime)


class Review(Base):
    """
    Collaborative review system - inspector reviews of analyses.
    """
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String, nullable=False)
    
    # Review decision
    status = Column(String, nullable=False, index=True)  # approved, rejected, needs_second_opinion
    comments = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis = relationship("Analysis", backref="reviews")
    annotations = relationship("ReviewAnnotation", back_populates="review", cascade="all, delete-orphan")


class ReviewAnnotation(Base):
    """
    Annotations added during review (regions of interest, corrections).
    """
    __tablename__ = "review_annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    
    # Bounding box for annotation
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    
    # Annotation details
    annotation_type = Column(String, nullable=False)  # correction, note, highlight, question
    comment = Column(String)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    review = relationship("Review", back_populates="annotations")


class ComplianceCertificate(Base):
    """
    Compliance certificates for regulatory standards.
    """
    __tablename__ = "compliance_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Certificate details
    standard = Column(String, nullable=False, index=True)  # AWS_D1_1, ASME_BPVC, ISO_5817_B, etc.
    certificate_number = Column(String, unique=True, nullable=False)
    
    # Compliance result
    compliant = Column(Boolean, nullable=False)
    severity_level = Column(String, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, ACCEPTABLE
    
    # Timestamps and validity
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime)
    
    # Metadata
    generated_by = Column(String, nullable=False)
    pdf_path = Column(String)
    
    # Relationship
    analysis = relationship("Analysis", backref="certificates")


class OperatorPerformance(Base):
    """
    Operator performance tracking for analytics.
    """
    __tablename__ = "operator_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(String, nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    
    # Performance metrics
    processing_time_seconds = Column(Float, nullable=False)
    accuracy_score = Column(Float)
    review_status = Column(String)  # approved, rejected, pending
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    analysis = relationship("Analysis", backref="operator_metrics")


class CustomDefectType(Base):
    """
    User-defined custom defect categories beyond the base LP/PO/CR/ND classes.
    """
    __tablename__ = "custom_defect_types"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Defect definition
    name = Column(String, unique=True, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False)  # Short code (e.g., "WM" for weld mismatch)
    description = Column(String)
    severity_default = Column(String, default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW, ACCEPTABLE
    
    # Visual characteristics for model training
    expected_features = Column(JSON)  # {"shape": "linear", "texture": "rough", "size_range": [10, 50]}
    color = Column(String, default="#FF6B6B")  # UI color for visualization
    
    # Training metadata
    is_active = Column(Boolean, default=True, index=True)
    requires_retraining = Column(Boolean, default=True)
    min_samples_required = Column(Integer, default=50)  # Minimum images needed for training
    current_sample_count = Column(Integer, default=0)
    
    # Standards compliance
    compliance_standards = Column(JSON)  # List of standards this defect applies to
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_samples = relationship("TrainingSample", back_populates="defect_type", cascade="all, delete-orphan")


class TrainingSample(Base):
    """
    Labeled training samples for custom defect types.
    """
    __tablename__ = "training_samples"
    
    id = Column(Integer, primary_key=True, index=True)
    defect_type_id = Column(Integer, ForeignKey("custom_defect_types.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image reference
    image_path = Column(String, nullable=False)
    image_id = Column(String, index=True)  # Links to Analysis.image_id if from existing analysis
    
    # Annotation data (YOLO format or bounding boxes)
    annotations = Column(JSON, nullable=False)  # {"bbox": [x, y, w, h], "class": "WM", "confidence": 1.0}
    annotation_format = Column(String, default="yolo")  # yolo, coco, pascal_voc
    
    # Sample metadata
    source = Column(String, nullable=False)  # "manual_upload", "review_correction", "active_learning"
    quality_score = Column(Float, default=1.0)  # 0.0-1.0, from active learning or review
    
    # Training status
    used_in_training = Column(Boolean, default=False)
    training_set = Column(String)  # "train", "val", "test"
    split_ratio = Column(Float)  # For automatic train/val/test split
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    labeled_by = Column(String, nullable=False)
    verified_by = Column(String)  # Optional second verification
    verified_at = Column(DateTime)
    
    # Relationship
    defect_type = relationship("CustomDefectType", back_populates="training_samples")


class ModelVersion(Base):
    """
    Model version tracking for rollback and A/B testing.
    """
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Version info
    version_number = Column(String, unique=True, nullable=False, index=True)  # "v1.0.0", "v1.1.0"
    model_name = Column(String, nullable=False)  # "yolov8s-cls-custom", "yolov8n-cls"
    
    # Model files
    model_path = Column(String, nullable=False)  # Path to .pt file
    config_path = Column(String)  # Path to YAML config
    model_size_mb = Column(Float)
    
    # Training details
    base_model = Column(String, default="yolov8s-cls.pt")  # Transfer learning base
    training_dataset_id = Column(Integer, ForeignKey("training_datasets.id"), index=True)
    epochs_trained = Column(Integer)
    final_map50 = Column(Float)  # Mean Average Precision at IoU 0.5
    final_accuracy = Column(Float)
    
    # Class information
    classes = Column(JSON, nullable=False)  # ["LP", "PO", "CR", "ND", "WM", "UC"]
    num_classes = Column(Integer, nullable=False)
    custom_classes = Column(JSON)  # List of custom class names added
    
    # Deployment status
    is_active = Column(Boolean, default=False, index=True)  # Only one can be active
    deployment_status = Column(String, default="trained")  # trained, deployed, archived, failed
    
    # Performance metrics (from validation)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    confusion_matrix = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trained_by = Column(String, nullable=False)
    deployed_at = Column(DateTime)
    archived_at = Column(DateTime)
    
    # Relationships
    training_dataset = relationship("TrainingDataset", back_populates="model_versions")
    training_jobs = relationship("TrainingJob", back_populates="model_version", cascade="all, delete-orphan")


class TrainingDataset(Base):
    """
    Dataset snapshots used for model training.
    """
    __tablename__ = "training_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Dataset info
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    dataset_path = Column(String, nullable=False)  # Path to dataset directory
    
    # Dataset composition
    total_images = Column(Integer, nullable=False)
    train_images = Column(Integer, nullable=False)
    val_images = Column(Integer, nullable=False)
    test_images = Column(Integer, nullable=False)
    
    # Class distribution
    class_distribution = Column(JSON, nullable=False)  # {"LP": 150, "PO": 200, "CR": 100, ...}
    includes_custom_types = Column(Boolean, default=False)
    custom_types_included = Column(JSON)  # List of custom defect type IDs
    
    # Data augmentation settings
    augmentation_config = Column(JSON)  # Augmentation pipeline used
    
    # Quality metrics
    mean_annotation_quality = Column(Float, default=1.0)
    has_validation_errors = Column(Boolean, default=False)
    validation_report = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=False)
    
    # Relationships
    model_versions = relationship("ModelVersion", back_populates="training_dataset")


class TrainingJob(Base):
    """
    Training job execution tracking with real-time progress.
    """
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), index=True)
    
    # Job configuration
    job_type = Column(String, nullable=False)  # "full_training", "fine_tuning", "transfer_learning"
    hyperparameters = Column(JSON, nullable=False)  # {"epochs": 50, "batch_size": 16, "lr": 0.001}
    
    # Execution status
    status = Column(String, default="pending", index=True)  # pending, running, completed, failed, cancelled
    progress_percent = Column(Float, default=0.0)
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer, nullable=False)
    
    # Real-time metrics
    latest_train_loss = Column(Float)
    latest_val_loss = Column(Float)
    latest_accuracy = Column(Float)
    latest_map50 = Column(Float)
    
    # Training history (loss/accuracy per epoch)
    training_history = Column(JSON)  # {"epoch": [1,2,3], "train_loss": [0.5, 0.3, 0.2], ...}
    
    # Resource usage
    estimated_time_remaining_minutes = Column(Integer)
    gpu_utilization_percent = Column(Float)
    memory_usage_gb = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error handling
    error_message = Column(String)
    error_traceback = Column(String)
    
    # Relationships
    model_version = relationship("ModelVersion", back_populates="training_jobs")


class ActiveLearningQueue(Base):
    """
    Queue of images suggested by active learning for labeling.
    """
    __tablename__ = "active_learning_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    
    # Uncertainty metrics
    uncertainty_score = Column(Float, nullable=False, index=True)  # Higher = more uncertain
    confidence_variance = Column(Float)  # Variance across ensemble predictions
    entropy = Column(Float)  # Prediction entropy
    
    # Selection reason
    selection_method = Column(String, nullable=False)  # "uncertainty", "diversity", "disagreement"
    priority_score = Column(Float, nullable=False, index=True)  # Combined priority metric
    
    # Review status
    status = Column(String, default="pending", index=True)  # pending, in_review, labeled, skipped
    assigned_to = Column(String)  # User assigned to label this image
    
    # Suggested labels (from model predictions)
    suggested_defect_types = Column(JSON)  # [{"type": "LP", "confidence": 0.45}, ...]
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime)
    
    # Relationship
    analysis = relationship("Analysis", backref="active_learning_suggestions")
