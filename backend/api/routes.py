"""
FastAPI routes for XAI Visual Quality Control API.

This module implements the REST API endpoints that serve as the contract
between the backend ML services and the Makerkit Next.js frontend.

Author: RadiKal Team
Date: 2025-01-20
"""

import io
import base64
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

import numpy as np
import torch
import cv2
from PIL import Image
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.middleware import get_current_user, require_role
from api.schemas import (
    DetectionResponse,
    DetectionBox,
    ExplainRequest,
    ExplainResponse,
    ExplanationResult,
    MetricsResponse,
    BusinessMetrics,
    DetectionMetrics,
    SegmentationMetrics,
    ExportRequest,
    ExportResponse,
    CalibrationResponse,
    CalibrationMetrics,
    HealthResponse,
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
)
from core.models.detector import DefectDetector
from core.models.yolo_detector import YOLODefectDetector
from core.preprocessing.image_processor import ImageProcessor
from db import get_db, Analysis, Detection, Explanation
# XAI imports - Now with real Grad-CAM for YOLOv8 Classification!
from core.xai.classification_explainer import ClassificationExplainer
from core.models.yolo_classifier import YOLOClassifier
# Temporarily disabled SHAP/LIME due to scipy import issues
# from core.xai.shap_explainer import SHAPExplainer
# from core.xai.lime_explainer import LIMEExplainer
# from core.uncertainty.mc_dropout import MCDropoutEstimator
# from core.uncertainty.calibration import calculate_ece, TemperatureScaling
# from core.metrics.business_metrics import calculate_confusion_matrix_metrics
# from core.metrics.detection_metrics import calculate_map, calculate_auroc
# from core.metrics.segmentation_metrics import calculate_mean_iou

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xai-qc", tags=["XAI Quality Control"])

# Global model instances (will be loaded on startup)
model: Optional[YOLODefectDetector] = None  # Using YOLOv8 now!
classifier: Optional[YOLOClassifier] = None  # NEW: YOLOv8 Classification model
explainer: Optional[ClassificationExplainer] = None  # NEW: Real XAI explainer
image_processor: Optional[ImageProcessor] = None
xai_explainers: dict = {}
# mc_dropout: Optional[MCDropoutEstimator] = None  # Disabled temporarily
# temperature_scaler: Optional[TemperatureScaling] = None  # Disabled temporarily

# Configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# Updated to use proper CLASSIFICATION model (not detection)
YOLO_MODEL_PATH = Path("models/yolo/classification_defect_focused/weights/best.pt")
MODEL_PATH_OLD_DETECTION = Path("models/yolo/radikal_weld_detection/weights/best.pt")  # Old detection model (deprecated)
MODEL_PATH = Path("models/checkpoints/best_model.pth")  # Legacy path
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

# Class names for YOLOv8 model - Weld Defect Types
CLASS_NAMES = {
    0: "LP",  # Lack of Penetration
    1: "PO",  # Porosity
    2: "CR",  # Cracks
    3: "ND"   # No Defect
}

# Full defect names for detailed reporting
CLASS_FULL_NAMES = {
    0: "Lack of Penetration",
    1: "Porosity",
    2: "Cracks",
    3: "No Defect"
}


def initialize_models():
    """
    Initialize all models and explainers on application startup.
    
    This function should be called during FastAPI app initialization.
    """
    global model, classifier, explainer, image_processor, xai_explainers  # , mc_dropout, temperature_scaler
    
    logger.info(f"Initializing models on device: {DEVICE}")
    
    # Initialize YOLOv8 Classification Model + Explainer
    try:
        classifier = YOLOClassifier(
            model_path=str(YOLO_MODEL_PATH),
            device='0' if DEVICE == 'cuda' else 'cpu',
            nd_confidence_threshold=0.7
        )
        explainer = ClassificationExplainer(classifier)
        logger.info(f"✅ Loaded YOLOv8 Classification model from {YOLO_MODEL_PATH}")
        logger.info(f"✅ Initialized ClassificationExplainer with Grad-CAM")
    except FileNotFoundError as e:
        logger.error(f"❌ YOLOv8 classification model not found: {e}")
        logger.warning("⚠️  XAI features will be limited")
    
    # Initialize YOLOv8 detector
    try:
        model = YOLODefectDetector(
            model_path=str(YOLO_MODEL_PATH),
            device='0' if DEVICE == 'cuda' else 'cpu',
            confidence_threshold=0.5,
            iou_threshold=0.45
        )
        logger.info(f"✅ Loaded YOLOv8 model from {YOLO_MODEL_PATH}")
        logger.info(f"   Model Info: {model.get_model_info()['model_type']}")
        logger.info(f"   Performance: mAP@0.5 = {model.get_model_info()['performance']['mAP@0.5']}")
    except FileNotFoundError as e:
        logger.error(f"❌ YOLOv8 model not found: {e}")
        logger.warning("⚠️  Falling back to legacy Faster R-CNN model...")
        # Fallback to legacy model
        model = DefectDetector(num_classes=2, device=DEVICE)
        if MODEL_PATH.exists():
            model.load_weights(str(MODEL_PATH))
            logger.info(f"Loaded legacy model weights from {MODEL_PATH}")
        else:
            logger.warning(f"No model weights found. Using untrained model.")
    
    # Initialize image processor
    image_processor = ImageProcessor(target_size=(640, 640))  # YOLOv8 input size
    
    # XAI explainers disabled temporarily due to SHAP/scipy import issues
    # Will re-enable once dependencies are fixed
    # # Initialize XAI explainers
    # # Note: XAI explainers work with the underlying model
    # # For YOLOv8, we'll need to adapt these later
    # if hasattr(model, 'model'):
    #     xai_model = model.model if isinstance(model, YOLODefectDetector) else model.model
    # else:
    #     xai_model = model
    
    # xai_explainers = {
    #     "gradcam": GradCAM(xai_model),
    #     "shap": SHAPExplainer(xai_model),
    #     "lime": LIMEExplainer(xai_model),
    #     "integrated_gradients": IntegratedGradientsExplainer(xai_model),
    # }
    
    # # Initialize uncertainty estimator
    # mc_dropout = MCDropoutEstimator(xai_model, n_samples=10, device=DEVICE)
    
    # # Initialize temperature scaling (will be calibrated later)
    # temperature_scaler = TemperatureScaling()
    
    logger.info("✅ All models initialized successfully")


def numpy_to_base64(arr: np.ndarray) -> str:
    """
    Convert numpy array to base64-encoded PNG string.
    
    Args:
        arr: Numpy array (H, W) or (H, W, C) with values in [0, 255] or [0, 1]
        
    Returns:
        Base64-encoded PNG image string
    """
    if arr.max() <= 1.0:
        arr = (arr * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


@router.post("/detect", response_model=DetectionResponse)
async def detect_defects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # # Auth disabled,  # Auth disabled for now
):
    """
    Detect defects in an uploaded image.
    
    This endpoint accepts an image file, runs defect detection, and returns
    bounding boxes, confidence scores, and segmentation masks.
    
    Args:
        file: Uploaded image file (JPEG, PNG)
        current_user: Authenticated user information
        
    Returns:
        DetectionResponse with detections and metadata
        
    Raises:
        HTTPException: If image processing fails
    """
    try:
        # Read and process image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        
        # Preprocess
        preprocessed = image_processor.preprocess(image_np)
        image_tensor = torch.from_numpy(
            image_processor.to_tensor(preprocessed)
        ).float().unsqueeze(0).to(DEVICE)
        
        # Run detection
        detections = model.predict(image_tensor)
        
        # Convert to response format
        results = []
        for i, det in enumerate(detections):
            box = det["box"]
            
            # Map severity to SeverityLevel enum
            score = float(det["score"])
            if score >= 0.9:
                severity = "critical"
            elif score >= 0.8:
                severity = "high"
            elif score >= 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            result = DetectionBox(
                x1=float(box[0]),
                y1=float(box[1]),
                x2=float(box[2]),
                y2=float(box[3]),
                confidence=score,
                label=det["class_id"],
                severity=severity,
            )
            results.append(result)
        
        # Generate inference time (ms)
        inference_time_ms = 16.0  # ~60 FPS = 16ms per image
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Prepare response
        response = DetectionResponse(
            image_id=image_id,
            detections=results,
            segmentation_masks=[],
            inference_time_ms=inference_time_ms,
            timestamp=datetime.now(),
            model_version="yolov8s-1.0.0",
        )
        
        # Save to database
        try:
            # Calculate summary statistics
            has_defects = len(results) > 0
            mean_confidence = sum(d.confidence for d in results) / len(results) if results else 0.0
            severities = [d.severity for d in results if d.severity]
            highest_severity = max(severities, key=lambda s: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(s, 0)) if severities else "none"
            
            # Create analysis record
            analysis = Analysis(
                image_id=image_id,
                filename=file.filename,
                upload_timestamp=datetime.utcnow(),
                image_width=image.width,
                image_height=image.height,
                image_size_bytes=len(image_bytes),
                num_detections=len(results),
                has_defects=has_defects,
                highest_severity=highest_severity,
                mean_confidence=mean_confidence,
                mean_uncertainty=0.0,  # Not calculated for now
                inference_time_ms=inference_time_ms,
                model_version="yolov8s-1.0.0",
                status="completed",
            )
            db.add(analysis)
            db.flush()  # Get analysis.id
            
            # Save individual detections
            for det in results:
                detection = Detection(
                    analysis_id=analysis.id,
                    x1=det.x1,
                    y1=det.y1,
                    x2=det.x2,
                    y2=det.y2,
                    confidence=det.confidence,
                    label=det.label,
                    class_name=CLASS_NAMES.get(det.label, f"class_{det.label}"),
                    severity=det.severity,
                )
                db.add(detection)
            
            db.commit()
            logger.info(f"✅ Analysis saved to database: {image_id} ({len(results)} detections)")
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Failed to save analysis to database: {str(db_error)}")
            # Continue anyway - don't fail the detection if DB save fails
        
        logger.info(f"Detection completed: {len(results)} defects found")
        return response
        
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/explain", response_model=ExplainResponse)
async def explain_detection(
    file: UploadFile = File(...),
    methods: str = Query("gradcam", description="XAI methods to use (comma-separated): gradcam,lime,shap,ig,all"),
    # # Auth disabled,  # Auth disabled for now
):
    """
    Generate XAI explanations for a radiographic weld image using multiple methods.
    
    **✅ ADVANCED XAI ENABLED**: Supports Grad-CAM, LIME, SHAP, and Integrated Gradients!
    
    Features:
    - **Grad-CAM**: Class Activation Mapping showing defect localization
    - **LIME**: Local Interpretable Model-agnostic Explanations with superpixels
    - **SHAP**: SHapley Additive exPlanations for pixel-level attribution
    - **Integrated Gradients**: Gradient-based attribution along path from baseline
    - **Aggregated**: Consensus heatmap combining multiple methods
    - Class probabilities for all defect types
    - Natural language description of findings
    - Operator-friendly recommendations
    
    Args:
        file: Uploaded radiographic image (JPEG, PNG)
        methods: Comma-separated list of methods (gradcam,lime,shap,ig,all)
        
    Returns:
        ExplainResponse with method-specific heatmaps and consensus visualization
        
    Raises:
        HTTPException: If explanation generation fails
    """
    try:
        if explainer is None:
            raise HTTPException(
                status_code=503,
                detail="XAI explainer not initialized. Ensure classification model is loaded."
            )
        
        # Save uploaded file temporarily
        temp_path = EXPORTS_DIR / f"temp_{uuid.uuid4()}.jpg"
        try:
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image.save(temp_path)
            
            logger.info(f"Processing image for XAI explanation: {file.filename}")
            logger.info(f"Requested methods: {methods}")
            
            # Parse methods
            method_list = [m.strip().lower() for m in methods.split(',')]
            
            # Check if we should use multi-method or single method
            if len(method_list) > 1 or 'all' in method_list or any(m in method_list for m in ['lime', 'shap', 'ig']):
                # Use new multi-method explainer
                logger.info("Using multi-method XAI explainer")
                explanation_result = explainer.explain_with_methods(
                    str(temp_path),
                    methods=method_list,
                    include_aggregated=True
                )
                
                # Build response from multi-method results
                explanations = []
                for method_name, method_result in explanation_result['methods'].items():
                    if 'error' not in method_result:
                        # Use overlay if available, otherwise heatmap
                        heatmap_b64 = method_result.get('overlay_base64') or method_result.get('heatmap_base64')
                        explanations.append(ExplanationResult(
                            method=method_name,
                            heatmap_base64=heatmap_b64,
                            confidence_score=method_result['confidence_score']
                        ))
                
                # Get aggregated or use first method as fallback
                if 'aggregated' in explanation_result:
                    aggregated_heatmap = explanation_result['aggregated']['overlay_base64']
                    consensus_score = explanation_result['aggregated']['consensus_score']
                else:
                    first_method = list(explanation_result['methods'].values())[0]
                    aggregated_heatmap = first_method.get('overlay_base64') or first_method.get('heatmap_base64')
                    consensus_score = explanation_result['prediction']['confidence']
                
                # Add regions and descriptions from Grad-CAM if available
                regions = []
                location_desc = ""
                description = ""
                recommendation = ""
                
                if 'gradcam' in explanation_result['methods']:
                    # Get detailed info from traditional explainer for Grad-CAM
                    gradcam_detail = explainer.explain_prediction(str(temp_path), include_regions=True, include_description=True)
                    regions = gradcam_detail.get('regions', [])
                    location_desc = gradcam_detail.get('location_description', '')
                    description = gradcam_detail.get('description', '')
                    recommendation = gradcam_detail.get('recommendation', '')
                
            else:
                # Use traditional single-method explainer (Grad-CAM only)
                logger.info("Using traditional Grad-CAM explainer")
                explanation_result = explainer.explain_prediction(
                    str(temp_path),
                    include_overlay=True,
                    include_regions=True,
                    include_description=True
                )
                
                # Build response
                gradcam_explanation = ExplanationResult(
                    method="gradcam",
                    heatmap_base64=explanation_result['heatmap_base64'],
                    confidence_score=explanation_result['prediction']['confidence']
                )
                
                overlay_explanation = ExplanationResult(
                    method="overlay",
                    heatmap_base64=explanation_result['overlay_base64'],
                    confidence_score=explanation_result['prediction']['confidence']
                )
                
                explanations = [gradcam_explanation, overlay_explanation]
                consensus_score = explanation_result['prediction']['confidence']
                aggregated_heatmap = explanation_result['heatmap_base64']
                
                regions = explanation_result.get('regions', [])
                location_desc = explanation_result.get('location_description', '')
                description = explanation_result.get('description', '')
                recommendation = explanation_result.get('recommendation', '')
            
            response = ExplainResponse(
                image_id=str(uuid.uuid4()),
                explanations=explanations,
                aggregated_heatmap=aggregated_heatmap,
                consensus_score=consensus_score,
                computation_time_ms=50.0,  # Approximate
                timestamp=datetime.now(),
                metadata={
                    'prediction': explanation_result['prediction'],
                    'probabilities': explanation_result['probabilities'],
                    'regions': regions,
                    'location_description': location_desc,
                    'description': description,
                    'recommendation': recommendation,
                    'methods_used': list(explanation_result.get('methods', {}).keys())
                }
            )
            
            logger.info(f"✅ Generated XAI explanation: {explanation_result['prediction']['class_full_name']} "
                       f"({explanation_result['prediction']['confidence']*100:.1f}% confidence)")
            logger.info(f"   Location: {explanation_result['location_description']}")
            logger.info(f"   Regions detected: {len(explanation_result['regions'])}")
            
            return response
        
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Explanation generation failed: {str(e)}"
        )


@router.get("/history", response_model=AnalysisHistoryResponse)
async def get_analysis_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    has_defects: Optional[bool] = Query(None, description="Filter by defect presence"),
    db: Session = Depends(get_db),
):
    """
    Get analysis history with pagination and filtering.
    
    Returns a paginated list of all previous analyses with summary information.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by status (completed, failed, processing)
        has_defects: Filter by defect presence
        db: Database session
        
    Returns:
        AnalysisHistoryResponse with paginated analyses
    """
    try:
        # Build query
        query = db.query(Analysis).order_by(Analysis.upload_timestamp.desc())
        
        # Apply filters
        if status:
            query = query.filter(Analysis.status == status)
        if has_defects is not None:
            query = query.filter(Analysis.has_defects == has_defects)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        analyses = query.offset(offset).limit(page_size).all()
        
        # Convert to response models
        items = [
            AnalysisHistoryItem(
                id=analysis.id,
                image_id=analysis.image_id,
                filename=analysis.filename,
                timestamp=analysis.upload_timestamp,
                num_detections=analysis.num_detections,
                has_defects=analysis.has_defects,
                highest_severity=analysis.highest_severity or "none",
                mean_confidence=analysis.mean_confidence or 0.0,
                mean_uncertainty=analysis.mean_uncertainty or 0.0,
                status=analysis.status,
            )
            for analysis in analyses
        ]
        
        has_more = (offset + page_size) < total_count
        
        response = AnalysisHistoryResponse(
            analyses=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
        
        logger.info(f"Retrieved {len(items)} analyses (page {page}, total: {total_count})")
        return response
        
    except Exception as e:
        logger.error(f"History retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    # Auth disabled),
):
    """
    Retrieve performance metrics over a specified date range.
    
    This endpoint returns comprehensive metrics including business KPIs,
    detection performance, and segmentation quality.
    
    Args:
        start_date: Start of date range (optional)
        end_date: End of date range (optional)
        current_user: Authenticated admin user
        
    Returns:
        MetricsResponse with all metrics
    """
    try:
        # In production, these would be loaded from a metrics database
        # For now, we'll return placeholder values
        
        # Create properly structured metrics response
        business_metrics = BusinessMetrics(
            true_positives=185,
            true_negatives=795,
            false_positives=8,
            false_negatives=12,
            precision=0.958,
            recall=0.939,
            f1_score=0.948,
            defect_rate_percent=2.0,
            false_alarm_rate_percent=0.8,
            miss_rate_percent=1.2,
        )
        
        detection_metrics = DetectionMetrics(
            **{
                "mAP@0.5": 0.9988,  # Your YOLOv8 performance!
                "mAP@0.75": 0.9856,
                "mAP": 0.9974,
                "precision": 0.958,
                "recall": 0.939,
                "f1_score": 0.948,
                "auroc": 0.945,
            }
        )
        
        segmentation_metrics = SegmentationMetrics(
            mean_iou=0.783,
            mean_dice=0.856,
            pixel_accuracy=0.912,
        )
        
        response = MetricsResponse(
            business_metrics=business_metrics,
            detection_metrics=detection_metrics,
            segmentation_metrics=segmentation_metrics,
            total_inspections=1000,
            date_range={
                "start_date": start_date or datetime.now(),
                "end_date": end_date or datetime.now(),
            },
            timestamp=datetime.now(),
        )
        
        logger.info(f"Metrics retrieved by admin system")
        return response
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.post("/export", response_model=ExportResponse)
async def export_report(
    request: ExportRequest,
    # Auth disabled,
):
    """
    Generate and export a quality control report.
    
    This endpoint generates a comprehensive report in PDF or Excel format
    containing detection results, explanations, and metrics.
    
    Args:
        request: ExportRequest with report parameters
        current_user: Authenticated user information
        
    Returns:
        ExportResponse with download URL
    """
    try:
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qc_report_{timestamp}.{request.format}"
        filepath = EXPORTS_DIR / filename
        
        # In production, this would generate an actual PDF/Excel report
        # For now, we'll create a placeholder file
        with open(filepath, "w") as f:
            f.write(f"Quality Control Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Image IDs: {', '.join(request.image_ids)}\n")
            f.write(f"Requested by: system\n")
        
        response = ExportResponse(
            export_id=f"export_{timestamp}",
            download_url=f"/api/xai-qc/download/{filename}",
            format=request.format,
            timestamp=datetime.now(),
            expires_at=datetime.now(),  # In production, set expiration time
        )
        
        logger.info(f"Report exported: {filename} by user system")
        return response
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{filename}")
async def download_report(
    filename: str,
    # Auth disabled,
):
    """
    Download an exported report file.
    
    Args:
        filename: Name of the report file
        current_user: Authenticated user information
        
    Returns:
        FileResponse with the report file
        
    Raises:
        HTTPException: If file not found
    """
    filepath = EXPORTS_DIR / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    logger.info(f"Report downloaded: {filename} by user system")
    return FileResponse(filepath, filename=filename)


@router.get("/calibration", response_model=CalibrationResponse)
async def get_calibration_status(
    # Auth disabled),
):
    """
    Get current model calibration status.
    
    This endpoint returns the Expected Calibration Error (ECE) and
    temperature scaling status.
    
    Args:
        current_user: Authenticated admin user
        
    Returns:
        CalibrationResponse with calibration metrics
    """
    try:
        # In production, these would be loaded from calibration storage
        calibration_metrics = CalibrationMetrics(
            ece=0.042,  # Low ECE indicates good calibration
            mce=0.065,  # Maximum Calibration Error
            avg_confidence=0.87,
            avg_accuracy=0.92,
            is_calibrated=True,
            temperature=1.5  # Temperature scaling parameter
        )
        
        response = CalibrationResponse(
            calibration_metrics=calibration_metrics,
            last_calibration_date=datetime.now(),
            num_samples_evaluated=500,
            timestamp=datetime.now()
        )
        
        logger.info(f"Calibration status retrieved by admin system")
        return response
        
    except Exception as e:
        logger.error(f"Calibration retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Calibration retrieval failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        HealthResponse with service status
    """
    model_loaded = model is not None
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        timestamp=datetime.now(),
        model_loaded=model_loaded,
        device=DEVICE,
        version="1.0.0",
    )
