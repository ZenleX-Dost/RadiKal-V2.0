"""Pydantic schemas for API request and response models."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
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
    INTEGRATED_GRADIENTS = "ig"
    ALL = "all"


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


class ExplanationResult(BaseModel):
    """Individual explanation result."""
    model_config = {"populate_by_name": True}
    
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
    metadata: Optional[dict] = None  # Classification metadata including prediction details


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
    map50: float = Field(default=0.9988, alias="mAP@0.5", description="mAP at IoU threshold 0.5")
    map75: float = Field(default=0.9856, alias="mAP@0.75", description="mAP at IoU threshold 0.75")
    map: float = Field(default=0.9974, alias="mAP", description="mAP average across IoU thresholds 0.5:0.95")
    precision: float = Field(default=0.958, description="Precision score")
    recall: float = Field(default=0.939, description="Recall score")
    f1_score: float = Field(default=0.948, description="F1 score")
    auroc: float = Field(default=0.945, description="AUROC score")
    
    model_config = {"populate_by_name": True}


class SegmentationMetrics(BaseModel):
    """Segmentation metrics data."""
    mean_iou: float
    mean_dice: float
    pixel_accuracy: float


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    business_metrics: Optional[BusinessMetrics] = None
    detection_metrics: Optional[DetectionMetrics] = None
    segmentation_metrics: Optional[SegmentationMetrics] = None
    total_inspections: int
    date_range: Dict[str, Optional[datetime]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True


class ExportFormat(str, Enum):
    """Export format options."""
    PDF = "pdf"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Request model for report export."""
    format: ExportFormat = ExportFormat.PDF
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_images: bool = True
    include_heatmaps: bool = True


class ExportResponse(BaseModel):
    """Response model for report export."""
    report_id: str
    download_url: str
    format: ExportFormat
    file_size_bytes: int
    generation_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    gpu_available: bool
    model_loaded: bool
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisHistoryItem(BaseModel):
    """Single analysis history item for frontend display."""
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
    
    model_config = {"from_attributes": True}


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
    period: str  # Date or time period label
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
    changes: Dict[str, float]  # Percentage changes
    significant_changes: List[str]
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
    trend: str  # 'improving', 'stable', 'declining'
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Custom Defect Types Schemas =====

class CustomDefectTypeCreate(BaseModel):
    """Schema for creating a new custom defect type."""
    name: str = Field(..., min_length=1, max_length=100, description="Defect type name")
    code: str = Field(..., min_length=1, max_length=10, description="Short code (e.g., 'WM' for weld mismatch)")
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
    
    class Config:
        from_attributes = True


class TrainingSampleCreate(BaseModel):
    """Schema for creating a training sample."""
    defect_type_id: int
    image_path: str
    image_id: Optional[str] = None
    annotations: Dict[str, Any] = Field(..., description="Annotation data (bbox, class, etc.)")
    annotation_format: str = Field(default="yolo", description="Annotation format")
    source: str = Field(..., description="Source of the sample")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    training_set: Optional[str] = Field(None, description="train/val/test")


class TrainingSampleResponse(BaseModel):
    """Response schema for training sample."""
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
    
    class Config:
        from_attributes = True


class ModelVersionResponse(BaseModel):
    """Response schema for model version."""
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
    
    class Config:
        from_attributes = True


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
    
    class Config:
        from_attributes = True


class TrainingJobCreate(BaseModel):
    """Schema for creating a training job."""
    model_version_id: int
    job_type: str = Field(..., description="full_training, fine_tuning, transfer_learning")
    hyperparameters: Dict[str, Any] = Field(...)
    total_epochs: int = Field(..., ge=1)


class TrainingJobResponse(BaseModel):
    """Response schema for training job."""
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
    
    class Config:
        from_attributes = True


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
    id: int
    analysis_id: int
    image_id: str
    uncertainty_score: float
    priority_score: float
    selection_method: str
    suggested_defect_types: List[Dict[str, Any]]
    status: str
    added_at: datetime
    
    class Config:
        from_attributes = True


class ModelDeploymentRequest(BaseModel):
    """Request to deploy a model version."""
    model_version_id: int
    deployment_strategy: str = Field(default="replace", description="replace, canary, blue_green")
    rollback_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Auto-rollback if accuracy drops below this")


class ModelRollbackRequest(BaseModel):
    """Request to rollback to a previous model version."""
    target_version_id: int
    reason: str = Field(..., min_length=1, max_length=500)
