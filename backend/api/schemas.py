"""Pydantic schemas for API request and response models."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SeverityLevel(str, Enum):
    """Defect severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class XAIMethod(str, Enum):
    """Available XAI explanation methods."""
    GRADCAM = "gradcam"
    SHAP = "shap"
    LIME = "lime"
    ALL = "all"


class AnalysisMode(str, Enum):
    """Analysis mode for hybrid defect analyzer."""
    CLASSIFICATION = "classification"
    SEGMENTATION = "segmentation"
    HYBRID = "hybrid"


class SegmentationGuidance(str, Enum):
    """Segmentation guidance strategy."""
    AUTO = "auto"
    CENTER = "center"
    GRID = "grid"


class DetectionBox(BaseModel):
    """Bounding box for detection."""
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    label: int
    severity: Optional[SeverityLevel] = None


class DetectionResponse(BaseModel):
    """Response model for defect detection."""
    image_id: str
    detections: List[DetectionBox]
    segmentation_masks: List[str] = Field(default_factory=list, description="Base64-encoded masks")
    inference_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "0.1.0"


class ExplainRequest(BaseModel):
    """Request model for XAI explanation."""
    image_id: str
    methods: List[XAIMethod] = Field(default=[XAIMethod.ALL])
    target_class: Optional[int] = None
    # New SAM2 options
    analysis_mode: AnalysisMode = Field(default=AnalysisMode.HYBRID, description="Analysis mode")
    enable_segmentation: bool = Field(default=True, description="Enable SAM2 segmentation")
    segmentation_guidance: SegmentationGuidance = Field(default=SegmentationGuidance.AUTO, description="Segmentation strategy")


class ExplanationResult(BaseModel):
    """Individual explanation result."""
    model_config = ConfigDict(populate_by_name=True)
    
    method: str
    heatmap_base64: str = Field(..., description="Base64-encoded heatmap image")
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class ExplainResponse(BaseModel):
    """Response model for XAI explanations."""
    image_id: str
    explanations: List[ExplanationResult]
    aggregated_heatmap: Optional[str] = None
    consensus_score: float = Field(..., ge=0.0, le=1.0)
    computation_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
    # New segmentation fields
    segmentation: Optional[Dict[str, Any]] = Field(default=None, description="SAM2 segmentation results")
    classification: Optional[Dict[str, Any]] = Field(default=None, description="YOLOv8 classification results")


class MetricsRequest(BaseModel):
    """Request model for metrics retrieval."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metric_types: List[str] = Field(default=["business", "detection", "segmentation"])


class BusinessMetrics(BaseModel):
    """Business metrics data."""
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    defect_rate_percent: float
    false_alarm_rate_percent: float
    miss_rate_percent: float


class DetectionMetrics(BaseModel):
    """Detection metrics data."""
    model_config = ConfigDict(populate_by_name=True)
    
    map50: float = Field(default=0.9988, alias="mAP@0.5", description="mAP at IoU threshold 0.5")
    map75: float = Field(default=0.9856, alias="mAP@0.75", description="mAP at IoU threshold 0.75")
    map: float = Field(default=0.9974, alias="mAP", description="mAP average across IoU thresholds 0.5:0.95")
    precision: float = Field(default=0.958, description="Precision score")
    recall: float = Field(default=0.939, description="Recall score")
    f1_score: float = Field(default=0.948, description="F1 score")
    auroc: float = Field(default=0.945, description="AUROC score")


class SegmentationMetrics(BaseModel):
    """Segmentation metrics data."""
    mean_iou: float
    mean_dice: float
    pixel_accuracy: float


class SegmentationResult(BaseModel):
    """SAM2 segmentation result."""
    has_segmentation: bool
    num_segments: int
    masks: List[List[List[int]]] = Field(default_factory=list, description="Binary masks (H, W)")
    scores: List[float] = Field(default_factory=list, description="Confidence scores for each mask")
    primary_mask: Optional[List[List[int]]] = Field(default=None, description="Best mask")
    bbox: List[int] = Field(default=[0, 0, 0, 0], description="Bounding box [x, y, w, h]")
    area: int = Field(default=0, description="Area in pixels")
    centroid: List[float] = Field(default=[0.0, 0.0], description="Centroid [x, y]")
    coverage_percent: float = Field(default=0.0, description="Percentage of image covered")


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    model_config = ConfigDict(populate_by_name=True)
    
    business_metrics: Optional[BusinessMetrics] = None
    detection_metrics: Optional[DetectionMetrics] = None
    segmentation_metrics: Optional[SegmentationMetrics] = None
    total_inspections: int
    date_range: Dict[str, Optional[datetime]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Request model for report export."""
    format: ExportFormat = ExportFormat.PDF
    image_ids: List[str] = Field(default_factory=list, description="List of image IDs to include in report")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_images: bool = True
    include_heatmaps: bool = True


class ExportResponse(BaseModel):
    """Response model for report export."""
    export_id: str = Field(..., alias="report_id", description="Export report ID")
    download_url: str
    format: ExportFormat
    file_size_bytes: Optional[int] = 0
    generation_time_ms: Optional[float] = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    model_config = ConfigDict(populate_by_name=True)


class CalibrationMetrics(BaseModel):
    """Model calibration metrics."""
    ece: float = Field(..., description="Expected Calibration Error")
    mce: float = Field(..., description="Maximum Calibration Error")
    avg_confidence: float
    avg_accuracy: float
    is_calibrated: bool
    temperature: Optional[float] = None


class CalibrationResponse(BaseModel):
    """Response model for calibration status."""
    calibration_metrics: CalibrationMetrics
    last_calibration_date: Optional[datetime] = None
    num_samples_evaluated: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PreprocessRequest(BaseModel):
    """Request model for image preprocessing with contrast adjustment."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contrast": 1.5,
                "method": "clahe"
            }
        }
    )
    
    contrast: float = Field(default=1.0, ge=0.5, le=3.0)
    method: str = Field(default='clahe', pattern='^(linear|histogram|clahe|gamma)$')


class PreprocessResponse(BaseModel):
    """Response model for image preprocessing."""
    image_id: str
    original_base64: str
    processed_base64: str
    contrast: float
    method: str
    timestamp: datetime


class UncertaintyMetrics(BaseModel):
    """Uncertainty quantification metrics."""
    predictive_entropy: float
    mutual_information: float
    mean_variance: float
    confidence_interval_95: List[float]


class HealthStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: HealthStatus
    version: str = "2.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    gpu_available: bool
    model_loaded: bool
    uptime_seconds: float
    device: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisHistoryItem(BaseModel):
    """Single analysis history item for frontend display."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_id: str
    filename: str
    timestamp: datetime
    num_detections: int
    has_defects: bool
    highest_severity: str
    mean_confidence: float
    mean_uncertainty: float
    status: str
    thumbnail: Optional[str] = None  # Base64 encoded thumbnail image


class AnalysisHistoryResponse(BaseModel):
    """Response model for analysis history list."""
    analyses: List[AnalysisHistoryItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool


# ===== Analytics Schemas =====

class DefectTrendData(BaseModel):
    """Defect trend data point."""
    period: str
    total_inspections: int
    defect_count: int
    defect_rate: float
    avg_confidence: float
    defect_types: Dict[str, int] = Field(default_factory=dict)


class TrendAnalysisResponse(BaseModel):
    """Response for trend analysis endpoint."""
    trends: List[DefectTrendData]
    summary: Dict[str, Any] = Field(default_factory=dict)
    date_range: Dict[str, Optional[datetime]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComparativeAnalysis(BaseModel):
    """Comparative analysis between periods."""
    period1: Dict[str, Any]
    period2: Dict[str, Any]
    changes: Dict[str, float] = Field(default_factory=dict)
    significant_changes: List[str] = Field(default_factory=list)
    defect_rate_change: float = 0.0
    quality_improvement_percent: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OperatorPerformance(BaseModel):
    """Operator performance metrics."""
    operator_id: str
    total_analyses: int
    avg_processing_time: float
    accuracy_score: float
    defect_detection_rate: float
    false_positive_rate: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProjectQualityScore(BaseModel):
    """Project quality score metrics."""
    project_id: str
    quality_score: float
    defect_density: float
    trend: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Custom Defect Types Schemas =====

class CustomDefectTypeCreate(BaseModel):
    """Schema for creating a new custom defect type."""
    name: str = Field(..., min_length=1, max_length=100, description="Defect type name")
    code: str = Field(..., min_length=1, max_length=10, description="Short code")
    description: Optional[str] = Field(None, max_length=500)
    severity_default: str = Field(default="MEDIUM", description="Default severity level")
    expected_features: Optional[Dict[str, Any]] = Field(default_factory=dict)
    color: str = Field(default="#FF6B6B", description="Hex color for UI visualization")
    compliance_standards: Optional[List[str]] = Field(default_factory=list)
    min_samples_required: int = Field(default=50, ge=1, description="Minimum samples for training")


class CustomDefectTypeUpdate(BaseModel):
    """Schema for updating a custom defect type."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    severity_default: Optional[str] = None
    expected_features: Optional[Dict[str, Any]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    compliance_standards: Optional[List[str]] = None
    min_samples_required: Optional[int] = Field(None, ge=1)


class CustomDefectTypeResponse(BaseModel):
    """Response schema for custom defect type."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    code: str
    description: Optional[str]
    severity_default: str
    expected_features: Optional[Dict[str, Any]]
    color: str
    is_active: bool
    requires_retraining: bool
    min_samples_required: int
    current_sample_count: int
    compliance_standards: Optional[List[str]]
    created_at: datetime
    created_by: str
    updated_at: datetime


class TrainingSampleCreate(BaseModel):
    """Schema for creating a training sample."""
    defect_type_id: int
    image_path: str
    image_id: Optional[str] = None
    annotations: Dict[str, Any] = Field(..., description="Annotation data")
    annotation_format: str = Field(default="yolo", description="Annotation format")
    source: str = Field(..., description="Source of the sample")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    training_set: Optional[str] = Field(None, description="train/val/test")


class TrainingSampleResponse(BaseModel):
    """Response schema for training sample."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    defect_type_id: int
    image_path: str
    image_id: Optional[str]
    annotations: Dict[str, Any]
    annotation_format: str
    source: str
    quality_score: float
    used_in_training: bool
    training_set: Optional[str]
    created_at: datetime
    labeled_by: str
    verified_by: Optional[str]
    verified_at: Optional[datetime]


class ModelVersionResponse(BaseModel):
    """Response schema for model version."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    version_number: str
    model_name: str
    model_path: str
    model_size_mb: Optional[float]
    base_model: str
    epochs_trained: Optional[int]
    final_map50: Optional[float]
    final_accuracy: Optional[float]
    classes: List[str]
    num_classes: int
    custom_classes: Optional[List[str]]
    is_active: bool
    deployment_status: str
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    created_at: datetime
    trained_by: str
    deployed_at: Optional[datetime]


class TrainingDatasetCreate(BaseModel):
    """Schema for creating a training dataset."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    dataset_path: str
    total_images: int = Field(..., ge=0)
    train_images: int = Field(..., ge=0)
    val_images: int = Field(..., ge=0)
    test_images: int = Field(..., ge=0)
    class_distribution: Dict[str, int] = Field(...)
    includes_custom_types: bool = Field(default=False)
    custom_types_included: Optional[List[int]] = Field(default_factory=list)
    augmentation_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TrainingDatasetResponse(BaseModel):
    """Response schema for training dataset."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    dataset_path: str
    total_images: int
    train_images: int
    val_images: int
    test_images: int
    class_distribution: Dict[str, int]
    includes_custom_types: bool
    custom_types_included: Optional[List[int]]
    mean_annotation_quality: float
    has_validation_errors: bool
    created_at: datetime
    created_by: str


class TrainingJobCreate(BaseModel):
    """Schema for creating a training job."""
    model_version_id: int
    job_type: str = Field(..., description="full_training, fine_tuning, transfer_learning")
    hyperparameters: Dict[str, Any] = Field(...)
    total_epochs: int = Field(..., ge=1)


class TrainingJobResponse(BaseModel):
    """Response schema for training job."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    model_version_id: int
    job_type: str
    status: str
    progress_percent: float
    current_epoch: int
    total_epochs: int
    latest_train_loss: Optional[float]
    latest_val_loss: Optional[float]
    latest_accuracy: Optional[float]
    latest_map50: Optional[float]
    estimated_time_remaining_minutes: Optional[int]
    gpu_utilization_percent: Optional[float]
    memory_usage_gb: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class TrainingJobProgress(BaseModel):
    """Real-time training progress update."""
    job_id: int
    status: str
    progress_percent: float
    current_epoch: int
    latest_metrics: Dict[str, float]
    estimated_time_remaining: Optional[int]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ActiveLearningSuggestion(BaseModel):
    """Active learning suggestion response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    analysis_id: int
    image_id: str
    uncertainty_score: float
    priority_score: float
    selection_method: str
    suggested_defect_types: List[Dict[str, Any]]
    status: str
    added_at: datetime


class ModelDeploymentRequest(BaseModel):
    """Request to deploy a model version."""
    model_version_id: int
    deployment_strategy: str = Field(default="replace", description="replace, canary, blue_green")
    rollback_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class ModelRollbackRequest(BaseModel):
    """Request to rollback to a previous model version."""
    target_version_id: int
    reason: str = Field(..., min_length=1, max_length=500)


# ============================================================================
# Role-Based Access Control Schemas
# ============================================================================

class UserRoleEnum(str, Enum):
    """User roles in the RadiKal system."""
    RADIKAL_USER = "radikal_user"
    CHIEF = "chief"
    MANAGER = "manager"


class ChangeRequestStatus(str, Enum):
    """Status values for change requests."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChangeRequestPriority(str, Enum):
    """Priority levels for change requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommentType(str, Enum):
    """Types of comments on analyses."""
    GENERAL = "general"
    FEEDBACK = "feedback"
    CORRECTION = "correction"
    APPROVAL = "approval"
    CONCERN = "concern"


class ActivityType(str, Enum):
    """Types of user activities."""
    LOGIN = "login"
    LOGOUT = "logout"
    ANALYSIS_CREATED = "analysis_created"
    ANALYSIS_VIEWED = "analysis_viewed"
    COMMENT_ADDED = "comment_added"
    CHANGE_REQUEST_CREATED = "change_request_created"
    CHANGE_REQUEST_COMPLETED = "change_request_completed"
    REVIEW_SUBMITTED = "review_submitted"


# === Change Request Schemas ===

class ChangeRequestCreate(BaseModel):
    """Schema for creating a change request (Chief only)."""
    analysis_id: int
    assigned_to_id: int
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    reason: Optional[str] = Field(None, max_length=1000)
    priority: ChangeRequestPriority = ChangeRequestPriority.MEDIUM
    due_date: Optional[datetime] = None


class ChangeRequestUpdate(BaseModel):
    """Schema for updating a change request."""
    status: Optional[ChangeRequestStatus] = None
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    resolved_analysis_id: Optional[int] = None


class ChangeRequestResponse(BaseModel):
    """Response schema for a change request."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    analysis_id: int
    requested_by_id: int
    requested_by_name: Optional[str] = None
    assigned_to_id: int
    assigned_to_name: Optional[str] = None
    title: str
    description: str
    reason: Optional[str]
    priority: str
    status: str
    resolution_notes: Optional[str]
    resolved_analysis_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]


class ChangeRequestListResponse(BaseModel):
    """Response schema for list of change requests."""
    items: List[ChangeRequestResponse]
    total: int
    page: int
    page_size: int


# === Comment Schemas ===

class CommentCreate(BaseModel):
    """Schema for creating a comment on an analysis (Chief only)."""
    analysis_id: int
    content: str = Field(..., min_length=1, max_length=5000)
    comment_type: CommentType = CommentType.GENERAL
    region_x: Optional[float] = None
    region_y: Optional[float] = None
    region_width: Optional[float] = None
    region_height: Optional[float] = None
    is_internal: bool = False


class CommentResponse(BaseModel):
    """Response schema for a comment."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    analysis_id: int
    author_id: int
    author_name: Optional[str] = None
    content: str
    comment_type: str
    region_x: Optional[float]
    region_y: Optional[float]
    region_width: Optional[float]
    region_height: Optional[float]
    is_internal: bool
    created_at: datetime
    updated_at: datetime


# === Activity Schemas ===

class ActivityLogResponse(BaseModel):
    """Response schema for activity log entry."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    user_name: Optional[str] = None
    action_type: str
    action_description: Optional[str]
    analysis_id: Optional[int]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    created_at: datetime


class UserActivitySummaryResponse(BaseModel):
    """Response schema for user activity summary."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    user_name: Optional[str] = None
    period_type: str
    period_start: datetime
    period_end: datetime
    analyses_performed: int
    analyses_reviewed: int
    change_requests_received: int
    change_requests_completed: int
    comments_made: int
    login_count: int
    defects_found: int
    average_confidence: float
    average_processing_time_ms: float


class UserActivityChartData(BaseModel):
    """Chart data for user activity visualization."""
    labels: List[str]  # Date labels
    datasets: List[Dict[str, Any]]  # Chart.js compatible datasets


# === User Statistics Schemas ===

class RadikalUserStats(BaseModel):
    """Statistics for a RadikalUser."""
    user_id: int
    user_name: str
    total_analyses: int
    analyses_this_week: int
    analyses_this_month: int
    pending_change_requests: int
    completed_change_requests: int
    average_confidence: float
    defects_found: int
    last_activity: Optional[datetime]


class ChiefDashboardStats(BaseModel):
    """Dashboard statistics for a Chief."""
    supervised_users_count: int
    total_analyses_by_team: int
    pending_reviews: int
    change_requests_sent: int
    change_requests_completed: int
    recent_activity: List[ActivityLogResponse]


class ManagerDashboardStats(BaseModel):
    """Dashboard statistics for a Manager."""
    total_users: int
    total_radikal_users: int
    total_chiefs: int
    total_analyses: int
    pending_change_requests: int
    completed_change_requests: int
    analyses_this_week: int
    analyses_this_month: int
    top_performers: List[RadikalUserStats]
