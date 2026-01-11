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
    
    # Image storage (base64 encoded)
    image_base64 = Column(String)  # Compressed preview for thumbnails
    original_image_base64 = Column(String)  # Full resolution original
    
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
    
    # User tracking - who performed this analysis
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Relationships
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="analysis", cascade="all, delete-orphan")
    performed_by_user = relationship("User", back_populates="analyses_performed", foreign_keys=[performed_by])
    comments = relationship("AnalysisComment", back_populates="analysis", cascade="all, delete-orphan")
    change_requests = relationship("ChangeRequest", back_populates="analysis", cascade="all, delete-orphan", foreign_keys="ChangeRequest.analysis_id")


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


class UserRole:
    """User role constants for RadiKal system."""
    RADIKAL_USER = "radikal_user"  # Can use models, perform analyses, view other users' results
    CHIEF = "chief"  # Supervises RadikalUsers, reviews, requests changes, adds comments
    MANAGER = "manager"  # Views history, analysis results, activity diagrams, change request list
    
    @classmethod
    def all_roles(cls):
        return [cls.RADIKAL_USER, cls.CHIEF, cls.MANAGER]
    
    @classmethod
    def can_use_models(cls, role: str) -> bool:
        """Check if role can use classification/analysis models."""
        return role == cls.RADIKAL_USER
    
    @classmethod
    def can_review(cls, role: str) -> bool:
        """Check if role can review analyses."""
        return role == cls.CHIEF
    
    @classmethod
    def can_request_changes(cls, role: str) -> bool:
        """Check if role can request changes to analyses."""
        return role == cls.CHIEF
    
    @classmethod
    def can_add_comments(cls, role: str) -> bool:
        """Check if role can add comments to analyses."""
        return role in [cls.CHIEF, cls.MANAGER]
    
    @classmethod
    def can_view_all_users(cls, role: str) -> bool:
        """Check if role can view all users and their activity."""
        return role in [cls.CHIEF, cls.MANAGER]
    
    @classmethod
    def can_view_change_requests(cls, role: str) -> bool:
        """Check if role can view change requests list."""
        return role == cls.MANAGER


class User(Base):
    """
    User model for authentication and role-based access.
    
    Roles:
    - radikal_user: Can use models, perform classification/segmentation, view other RadikalUsers' results
    - chief: Supervises RadikalUsers, reviews analyses, requests changes, adds comments, views activity charts
    - manager: Views history, analysis results, activity diagrams, sees change requests from chiefs
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)  # bcrypt hashed password
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)  # 'radikal_user', 'chief', 'manager'
    
    # Supervisor assignment (for RadikalUsers)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - reviews requested by this user
    reviews_submitted = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_requested = relationship("Review", foreign_keys="Review.requested_by_id", back_populates="requester")
    
    # Relationships - supervisor hierarchy
    supervisor = relationship("User", remote_side="User.id", backref="supervised_users", foreign_keys=[supervisor_id])
    
    # Relationships - analyses performed by this user
    analyses_performed = relationship("Analysis", back_populates="performed_by_user", foreign_keys="Analysis.performed_by")
    
    # Relationships - comments added by this user
    comments = relationship("AnalysisComment", back_populates="author")
    
    # Relationships - change requests
    change_requests_created = relationship("ChangeRequest", foreign_keys="ChangeRequest.requested_by_id", back_populates="requested_by")
    change_requests_assigned = relationship("ChangeRequest", foreign_keys="ChangeRequest.assigned_to_id", back_populates="assigned_to")
    
    # Relationships - activity logs
    activity_logs = relationship("ActivityLog", back_populates="user")


class Review(Base):
    """
    Collaborative review system - inspector reviews of analyses.
    Supports second opinion requests between technicians and project chiefs.
    """
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Reviewer who submitted this review
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # For second opinion requests - who requested and target reviewer
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Review decision
    status = Column(String, nullable=False, index=True)  # approved, rejected, needs_second_opinion, pending_review
    comments = Column(String)
    request_notes = Column(String)  # Notes when requesting second opinion
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    analysis = relationship("Analysis", backref="reviews")
    annotations = relationship("ReviewAnnotation", back_populates="review", cascade="all, delete-orphan")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_submitted")
    requester = relationship("User", foreign_keys=[requested_by_id], back_populates="reviews_requested")
    target_reviewer = relationship("User", foreign_keys=[target_reviewer_id])


class ComplianceCheck(Base):
    """
    Compliance check record - stores each compliance verification.
    """
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to analysis (optional - can check manually too)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # User who performed the check
    inspector_name = Column(String, nullable=True)
    inspector_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Defect details
    defect_type = Column(String, nullable=False)
    length_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    depth_mm = Column(Float, nullable=True)
    density_percent = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    
    # Material details
    material_type = Column(String, nullable=True)  # Carbon Steel, Stainless Steel, etc.
    material_thickness = Column(Float, nullable=True)  # in mm
    
    # Standard used
    standard_code = Column(String, nullable=False, index=True)  # AWS D1.1, ASME, etc.
    standard_name = Column(String, nullable=True)
    
    # Compliance result
    severity = Column(String, nullable=False)  # critical, major, minor
    compliance_status = Column(String, nullable=False)  # pass, fail
    pass_fail = Column(Boolean, nullable=False)
    recommended_action = Column(String, nullable=True)
    reasons = Column(JSON, nullable=True)  # List of reasons
    
    # Certificate
    certificate_id = Column(String, unique=True, index=True, nullable=True)
    certificate_path = Column(String, nullable=True)  # Path to generated PDF
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    analysis = relationship("Analysis", backref="compliance_checks")
    inspector = relationship("User", backref="compliance_checks")


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


# ============================================================================
# NEW ROLE-BASED ACCESS CONTROL MODELS
# ============================================================================

class ChangeRequest(Base):
    """
    Change requests created by Chiefs for RadikalUsers to redo/modify analyses.
    Managers can view a list of all change requests.
    """
    __tablename__ = "change_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to the analysis that needs changes
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Who requested the change (Chief)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Who should make the change (RadikalUser)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Request details
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)  # What needs to be changed
    reason = Column(String)  # Why the change is needed
    priority = Column(String, default="medium", index=True)  # low, medium, high, urgent
    
    # Status tracking
    status = Column(String, default="pending", nullable=False, index=True)  # pending, in_progress, completed, cancelled
    
    # Resolution
    resolution_notes = Column(String)  # Notes from RadikalUser when completing
    resolved_analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)  # Link to new analysis if redone
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="change_requests", foreign_keys=[analysis_id])
    requested_by = relationship("User", back_populates="change_requests_created", foreign_keys=[requested_by_id])
    assigned_to = relationship("User", back_populates="change_requests_assigned", foreign_keys=[assigned_to_id])
    resolved_analysis = relationship("Analysis", foreign_keys=[resolved_analysis_id])


class AnalysisComment(Base):
    """
    Comments on analyses - Chiefs can add comments for feedback.
    """
    __tablename__ = "analysis_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to analysis
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Author of the comment
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Comment content
    content = Column(String, nullable=False)
    comment_type = Column(String, default="general")  # general, feedback, correction, approval, concern
    
    # Optional: Link to specific region of image
    region_x = Column(Float, nullable=True)
    region_y = Column(Float, nullable=True)
    region_width = Column(Float, nullable=True)
    region_height = Column(Float, nullable=True)
    
    # Visibility
    is_internal = Column(Boolean, default=False)  # If True, only Chiefs and Managers can see
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="comments")
    author = relationship("User", back_populates="comments")


class ActivityLog(Base):
    """
    Activity tracking for users - used by Chiefs and Managers to monitor RadikalUser activity.
    """
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity details
    action_type = Column(String, nullable=False, index=True)  # login, logout, analysis_created, analysis_viewed, etc.
    action_description = Column(String)
    
    # Related entities (optional)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    related_entity_type = Column(String, nullable=True)  # analysis, review, change_request, etc.
    related_entity_id = Column(Integer, nullable=True)
    
    # Additional context (renamed from 'metadata' which is reserved)
    extra_data = Column(JSON, nullable=True)  # Any additional context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    analysis = relationship("Analysis", backref="activity_logs")


class UserActivitySummary(Base):
    """
    Daily/Weekly aggregated activity summary for dashboards.
    Pre-computed for performance on activity charts.
    """
    __tablename__ = "user_activity_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Time period
    period_type = Column(String, nullable=False, index=True)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    # Activity counts
    analyses_performed = Column(Integer, default=0)
    analyses_reviewed = Column(Integer, default=0)
    change_requests_received = Column(Integer, default=0)
    change_requests_completed = Column(Integer, default=0)
    comments_made = Column(Integer, default=0)
    login_count = Column(Integer, default=0)
    
    # Quality metrics
    defects_found = Column(Integer, default=0)
    average_confidence = Column(Float, default=0.0)
    average_processing_time_ms = Column(Float, default=0.0)
    
    # Computed at
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="activity_summaries")
