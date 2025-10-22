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
