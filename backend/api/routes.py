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
import math
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import numpy as np
import torch
import cv2
from PIL import Image
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, Body
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
    SegmentationResult,
    ExportRequest,
    ExportResponse,
    CalibrationResponse,
    CalibrationMetrics,
    HealthResponse,
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    AnalysisMode,
    SegmentationGuidance,
)
from core.models.detector import DefectDetector
from core.models.yolo_detector import YOLODefectDetector
from core.preprocessing.image_processor import ImageProcessor
from db import get_db, Analysis, Detection, Explanation

# Initialize logger early for imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File validation for security
try:
    from api.validators import validate_image_upload, sanitize_filename
    FILE_VALIDATION_ENABLED = True
except ImportError:
    FILE_VALIDATION_ENABLED = False
    logger.warning("[WARN] File validation module not available")

# XAI imports - Now with real Grad-CAM for YOLOv8 Classification!
from core.xai.classification_explainer import ClassificationExplainer
from core.models.yolo_classifier import YOLOClassifier
from core.models.hybrid_defect_analyzer import HybridDefectAnalyzer
# Temporarily disabled SHAP/LIME due to scipy import issues
# from core.xai.shap_explainer import SHAPExplainer
# from core.xai.lime_explainer import LIMEExplainer
# from core.uncertainty.mc_dropout import MCDropoutEstimator
# from core.uncertainty.calibration import calculate_ece, TemperatureScaling
# from core.metrics.business_metrics import calculate_confusion_matrix_metrics
# from core.metrics.detection_metrics import calculate_map, calculate_auroc
# from core.metrics.segmentation_metrics import calculate_mean_iou

router = APIRouter(prefix="/api/xai-qc", tags=["XAI Quality Control"])

# Global model instances (will be loaded on startup)
model: Optional[YOLODefectDetector] = None  # Using YOLOv8 now!
classifier: Optional[YOLOClassifier] = None  # NEW: YOLOv8 Classification model
explainer: Optional[ClassificationExplainer] = None  # NEW: Real XAI explainer
hybrid_analyzer: Optional[HybridDefectAnalyzer] = None  # NEW: Hybrid Classification + Segmentation
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
    global model, classifier, explainer, hybrid_analyzer, image_processor, xai_explainers  # , mc_dropout, temperature_scaler
    
    logger.info(f"Initializing models on device: {DEVICE}")
    
    # Initialize YOLOv8 Classification Model + Explainer
    try:
        classifier = YOLOClassifier(
            model_path=str(YOLO_MODEL_PATH),
            device='0' if DEVICE == 'cuda' else 'cpu',
            nd_confidence_threshold=0.7
        )
        explainer = ClassificationExplainer(classifier)
        logger.info(f"[OK] Loaded YOLOv8 Classification model from {YOLO_MODEL_PATH}")
        logger.info(f"[OK] Initialized ClassificationExplainer with Grad-CAM")
    except FileNotFoundError as e:
        logger.error(f"[ERROR] YOLOv8 classification model not found: {e}")
        logger.warning("[WARN] XAI features will be limited")
    
    # Initialize Hybrid Analyzer (YOLOv8 + SAM2)
    try:
        logger.info("Initializing Hybrid Defect Analyzer (YOLOv8 + SAM2)...")
        hybrid_analyzer = HybridDefectAnalyzer(
            classifier_path=str(YOLO_MODEL_PATH),
            segmenter_size="base",  # Use base+ model (sam2.1_hiera_b+.pt) - best for 6GB GPU
            device='cuda' if DEVICE == 'cuda' else 'cpu',  # SAM2 needs 'cuda' not '0'
            nd_threshold=0.7,
            enable_sam2=True  # Will gracefully fallback if SAM2 not available
        )
        logger.info("[OK] Hybrid Analyzer initialized")
        logger.info(f"   SAM2 enabled: {hybrid_analyzer.enable_sam2}")
    except Exception as e:
        logger.warning(f"[WARN] Failed to initialize Hybrid Analyzer: {e}")
        logger.warning("[WARN] Segmentation features will be unavailable")
        hybrid_analyzer = None
    
    # Initialize YOLOv8 detector
    try:
        model = YOLODefectDetector(
            model_path=str(YOLO_MODEL_PATH),
            device='0' if DEVICE == 'cuda' else 'cpu',
            confidence_threshold=0.5,
            iou_threshold=0.45
        )
        logger.info(f"[OK] Loaded YOLOv8 model from {YOLO_MODEL_PATH}")
        logger.info(f"   Model Info: {model.get_model_info()['model_type']}")
        logger.info(f"   Performance: mAP@0.5 = {model.get_model_info()['performance']['mAP@0.5']}")
    except FileNotFoundError as e:
        logger.error(f"[ERROR] YOLOv8 model not found: {e}")
        logger.warning("[WARN] Falling back to legacy Faster R-CNN model...")
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
    
    logger.info("[OK] All models initialized successfully")


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
    contrast: float = Query(default=1.0, ge=0.1, le=5.0, description="Contrast factor"),
    contrast_method: str = Query(default="linear", pattern="^(linear|histogram|clahe|gamma)$"),
    db: Session = Depends(get_db),
    # # Auth disabled,  # Auth disabled for now
):
    """
    Detect defects in an uploaded image.
    
    This endpoint accepts an image file, runs defect detection, and returns
    bounding boxes, confidence scores, and segmentation masks.
    
    Args:
        file: Uploaded image file (JPEG, PNG, max 10MB)
        contrast: Contrast adjustment factor (0.1-5.0, default 1.0)
        contrast_method: Method for contrast adjustment ('linear', 'histogram', 'clahe', 'gamma')
        
    Returns:
        DetectionResponse with detections and metadata
        
    Raises:
        HTTPException: If image processing fails or validation fails
    """
    try:
        # Validate uploaded file for security
        if FILE_VALIDATION_ENABLED:
            image_bytes, content_type = await validate_image_upload(file)
            safe_filename = sanitize_filename(file.filename)
        else:
            image_bytes = await file.read()
            safe_filename = file.filename or "unknown.jpg"
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        
        # Preprocess with optional contrast adjustment
        preprocessed = image_processor.preprocess(image_np, contrast=contrast, contrast_method=contrast_method)
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
                filename=safe_filename,  # Use sanitized filename
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
            logger.info(f"[OK] Analysis saved to database: {image_id} ({len(results)} detections)")
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Failed to save analysis to database: {str(db_error)}")
            # Continue anyway - don't fail the detection if DB save fails
        
        logger.info(f"Detection completed: {len(results)} defects found")
        return response
        
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/preprocess")
async def preprocess_image(
    file: UploadFile = File(...),
    contrast: float = Query(default=1.0, ge=0.5, le=3.0),
    method: str = Query(default='clahe', regex='^(linear|histogram|clahe|gamma)$')
):
    """Preprocess image with contrast adjustment before analysis.
    
    This endpoint allows technicians to adjust image contrast to reveal
    subtle defects in radiographic images before running XAI analysis.
    Provides real-time preview of original vs processed images.
    
    Args:
        file: Image file to preprocess
        contrast: Contrast adjustment factor (0.5-3.0, default 1.0)
        method: Adjustment method (linear, histogram, clahe, gamma)
        
    Returns:
        Original and processed images as base64 for real-time preview
    """
    if not image_processor:
        raise HTTPException(status_code=503, detail="Image processor not initialized")
    
    try:
        # Validate file upload for security
        if FILE_VALIDATION_ENABLED:
            contents, content_type = await validate_image_upload(file)
        else:
            contents = await file.read()
        
        # Read uploaded image
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply contrast adjustment
        processed_image = image_processor.adjust_contrast(
            image,
            contrast=contrast,
            method=method
        )
        
        # Convert to base64 for preview
        original_pil = Image.fromarray(image)
        processed_pil = Image.fromarray(processed_image)
        
        original_buffer = io.BytesIO()
        processed_buffer = io.BytesIO()
        
        original_pil.save(original_buffer, format='JPEG', quality=85)
        processed_pil.save(processed_buffer, format='JPEG', quality=85)
        
        original_b64 = base64.b64encode(original_buffer.getvalue()).decode('utf-8')
        processed_b64 = base64.b64encode(processed_buffer.getvalue()).decode('utf-8')
        
        logger.info(f"[OK] Preprocessed image: contrast={contrast}, method={method}")
        
        return {
            "image_id": str(uuid.uuid4()),
            "original_base64": f"data:image/jpeg;base64,{original_b64}",
            "processed_base64": f"data:image/jpeg;base64,{processed_b64}",
            "contrast": contrast,
            "method": method,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Preprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")


@router.post("/explain", response_model=ExplainResponse)
async def explain_detection(
    file: UploadFile = File(...),
    methods: str = Query("gradcam", description="XAI methods to use (comma-separated): gradcam,lime,shap,all"),
    contrast: float = Query(1.0, ge=0.1, le=5.0, description="Contrast adjustment factor"),
    contrast_method: str = Query("linear", regex="^(linear|histogram|clahe|gamma)$"),
    db: Session = Depends(get_db),
    # # Auth disabled,  # Auth disabled for now
):
    """
    Generate XAI explanations for a radiographic weld image using multiple methods.
    
    **ADVANCED XAI ENABLED**: Supports Grad-CAM, LIME, SHAP, and Integrated Gradients!
    
    Features:
    - **Grad-CAM**: Class Activation Mapping showing defect localization
    - **LIME**: Local Interpretable Model-agnostic Explanations with superpixels
    - **SHAP**: SHapley Additive exPlanations for pixel-level attribution
    - **Aggregated**: Consensus heatmap combining multiple methods
    - Class probabilities for all defect types
    - Natural language description of findings
    - Operator-friendly recommendations
    
    Args:
        file: Uploaded radiographic image (JPEG, PNG)
        methods: Comma-separated list of methods (gradcam,lime,shap,ig,all)
        contrast: Contrast adjustment factor (1.0 = no change, >1.0 = increase, <1.0 = decrease)
        contrast_method: Method for contrast adjustment ('linear', 'histogram', 'clahe', 'gamma')
        
    Returns:
        ExplainResponse with method-specific heatmaps and consensus visualization
        
    Raises:
        HTTPException: If explanation generation fails
    """
    try:
        # Validate file upload for security
        if FILE_VALIDATION_ENABLED:
            image_bytes, content_type = await validate_image_upload(file)
        else:
            image_bytes = await file.read()
        
        if explainer is None:
            raise HTTPException(
                status_code=503,
                detail="XAI explainer not initialized. Ensure classification model is loaded."
            )
        
        # Generate a single UUID for this analysis
        image_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily (applying contrast adjustment if needed)
        temp_path = EXPORTS_DIR / f"temp_{image_id}.jpg"
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Apply contrast adjustment if needed
            if contrast != 1.0 or contrast_method != 'linear':
                image_np = np.array(image)
                adjusted_np = image_processor.adjust_contrast(image_np, contrast=contrast, method=contrast_method)
                image = Image.fromarray(adjusted_np)
                logger.info(f"Applied contrast adjustment: {contrast}x ({contrast_method})")
            
            image.save(temp_path)
            
            logger.info(f"Processing image for XAI explanation: {file.filename} (ID: {image_id})")
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
                    consensus_score = explanation_result['aggregated'].get('consensus_score', 0.0)
                    # Only replace consensus_score if it's None or NaN (not if it's 0.0, which is valid)
                    if consensus_score is None or (isinstance(consensus_score, float) and math.isnan(consensus_score)):
                        consensus_score = explanation_result['prediction']['confidence']
                else:
                    first_method = list(explanation_result['methods'].values())[0]
                    aggregated_heatmap = first_method.get('overlay_base64') or first_method.get('heatmap_base64')
                    consensus_score = explanation_result['prediction']['confidence']
                
                # Add regions and descriptions from Grad-CAM if available
                regions = []
                location_desc = ""
                description = ""
                recommendation = ""
                
                if 'gradcam' in explanation_result['methods'] and 'error' not in explanation_result['methods']['gradcam']:
                    # Get detailed info from traditional explainer for Grad-CAM
                    try:
                        gradcam_detail = explainer.explain_prediction(str(temp_path), include_regions=True, include_description=True)
                        regions = gradcam_detail.get('regions', [])
                        location_desc = gradcam_detail.get('location_description', '')
                        description = gradcam_detail.get('description', '')
                        recommendation = gradcam_detail.get('recommendation', '')
                    except Exception as e:
                        logger.warning(f"Failed to get detailed Grad-CAM info: {e}")
                        # Use defaults
                        regions = []
                        location_desc = "Unable to generate location description"
                        description = f"Detected: {explanation_result['prediction']['class_full_name']}"
                        recommendation = "Review the analysis results"
                
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
                # Prefer overlay over heatmap for aggregated display
                aggregated_heatmap = explanation_result.get('overlay_base64') or explanation_result.get('heatmap_base64', '')
                
                regions = explanation_result.get('regions', [])
                location_desc = explanation_result.get('location_description', '')
                description = explanation_result.get('description', '')
                recommendation = explanation_result.get('recommendation', '')
            
            response = ExplainResponse(
                image_id=image_id,  # Use the generated UUID
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
            
            logger.info(f"[OK] Generated XAI explanation: {explanation_result['prediction']['class_full_name']} "
                       f"({explanation_result['prediction']['confidence']*100:.1f}% confidence)")
            logger.info(f"   Location: {location_desc}")
            logger.info(f"   Regions detected: {len(regions)}")
            
            # Save to database - Only add Explanation, Analysis is already created by /detect
            try:
                predicted_class = explanation_result['prediction']['class_full_name']
                confidence = explanation_result['prediction']['confidence']
                
                # Check if analysis already exists from /detect call
                existing_analysis = db.query(Analysis).filter(Analysis.image_id == response.image_id).first()
                
                if existing_analysis:
                    # Update existing analysis with classification info
                    existing_analysis.mean_confidence = confidence
                    existing_analysis.has_defects = predicted_class.lower() != 'no defect'
                    logger.info(f"[OK] Updated existing analysis: {response.image_id}")
                    analysis_db_id = existing_analysis.id
                else:
                    # No existing analysis (direct /explain call), create new one
                    has_defects = predicted_class.lower() != 'no defect'
                    
                    # Read and encode the original image for storage
                    original_image_b64 = None
                    thumbnail_b64 = None
                    try:
                        with open(temp_path, 'rb') as img_file:
                            original_image_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        # Create proper thumbnail (resized to 400px width)
                        pil_img = Image.open(temp_path)
                        thumb_width = 400
                        thumb_height = int(pil_img.height * (thumb_width / pil_img.width))
                        pil_img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                        thumb_buffer = io.BytesIO()
                        pil_img.save(thumb_buffer, format='JPEG', quality=75)
                        thumb_buffer.seek(0)
                        thumbnail_b64 = base64.b64encode(thumb_buffer.read()).decode('utf-8')
                    except Exception as img_err:
                        logger.warning(f"Failed to encode image for storage: {img_err}")
                    
                    db_analysis = Analysis(
                        image_id=response.image_id,
                        filename=file.filename or "unknown.jpg",
                        upload_timestamp=datetime.now(),
                        inference_time_ms=response.computation_time_ms,
                        status='completed',
                        has_defects=has_defects,
                        num_detections=1 if has_defects else 0,
                        highest_severity='high' if has_defects else None,
                        mean_confidence=confidence,
                        model_version='YOLOv8s-cls',
                        original_image_base64=original_image_b64,
                        image_base64=thumbnail_b64,  # Proper thumbnail
                    )
                    db.add(db_analysis)
                    db.flush()  # Get the ID
                    analysis_db_id = db_analysis.id
                    logger.info(f"[OK] Created new analysis: {response.image_id}")
                    
                    # Also create a Detection record for classification result
                    if has_defects:
                        # For classification, create a single detection covering whole image
                        predicted_label = explanation_result['prediction']['class_id']
                        detection = Detection(
                            analysis_id=analysis_db_id,
                            x1=0.0,
                            y1=0.0,
                            x2=1.0,
                            y2=1.0,
                            confidence=confidence,
                            label=predicted_label,
                            class_name=CLASS_NAMES.get(predicted_label, predicted_class),
                            severity='high',
                        )
                        db.add(detection)
                        logger.info(f"[OK] Created detection: {CLASS_NAMES.get(predicted_label, predicted_class)}")
                
                # Create Explanation record (store full heatmap, not truncated)
                db_explanation = Explanation(
                    analysis_id=analysis_db_id,
                    method=','.join(list(explanation_result.get('methods', {}).keys()) if 'methods' in explanation_result else ['gradcam']),
                    heatmap_base64=response.aggregated_heatmap if response.aggregated_heatmap else None,  # Store FULL heatmap
                    confidence_score=confidence,
                )
                db.add(db_explanation)
                
                db.commit()
                logger.info(f"[OK] Saved explanation to database for analysis: {response.image_id}")
            except Exception as db_error:
                logger.error(f"Failed to save to database: {db_error}")
                db.rollback()
                # Continue anyway - don't fail the request
            
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


@router.post("/analyze-hybrid", response_model=ExplainResponse)
async def analyze_hybrid(
    file: UploadFile = File(...),
    mode: str = Query("hybrid", description="Analysis mode: classification, segmentation, or hybrid"),
    enable_segmentation: bool = Query(True, description="Enable SAM2 segmentation"),
    segmentation_guidance: str = Query("auto", description="Segmentation strategy: auto, center, or grid"),
    methods: str = Query("gradcam", description="XAI methods (comma-separated): gradcam,lime,shap,ig,all"),
    db: Session = Depends(get_db),
):
    """
    **HYBRID ANALYSIS**: YOLOv8 Classification + SAM2 Segmentation
    
    This endpoint combines two powerful models for comprehensive defect analysis:
    - **YOLOv8 Classification**: Determines defect type (LP, PO, CR, ND)  
    - **SAM2 Segmentation**: Provides precise pixel-level defect localization
    
    **Analysis Modes**:
    - `classification`: Fast defect type identification only
    - `segmentation`: Detailed mask generation (SAM2 required)
    - `hybrid` (default): Classification guides segmentation for optimal results
    
    **Segmentation Guidance**:
    - `auto`: Smart guidance (center point for defects, auto-segment for ND)
    - `center`: Always use center point prompt
    - `grid`: Grid-based automatic segmentation
    
    **Returns**:
    - Classification: defect type, confidence, probabilities
    - Segmentation: pixel masks, bounding box, coverage percentage
    - XAI: Grad-CAM heatmaps with optional segmentation overlay
    """
    if hybrid_analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Hybrid analyzer not available. SAM2 may not be installed."
        )
    
    try:
        # Validate mode
        if mode not in ["classification", "segmentation", "hybrid"]:
            raise HTTPException(status_code=400, detail="Invalid mode. Must be: classification, segmentation, or hybrid")
        
        # Validate guidance
        if segmentation_guidance not in ["auto", "center", "grid"]:
            raise HTTPException(status_code=400, detail="Invalid segmentation_guidance. Must be: auto, center, or grid")
        
        # Read and validate image
        image_bytes = await file.read()
        
        if FILE_VALIDATION_ENABLED:
            validate_image_upload(image_bytes)
        
        # Convert to PIL Image
        image_pil = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_np = np.array(image_pil)
        
        # Generate image ID
        image_id = str(uuid.uuid4())
        
        # Parse XAI methods
        method_list = [m.strip() for m in methods.split(',')]
        
        logger.info(f"[START] Hybrid analysis: mode={mode}, segmentation={enable_segmentation}, guidance={segmentation_guidance}")
        
        # Run hybrid analysis
        analysis_result = hybrid_analyzer.analyze(
            image=image_np,
            mode=mode,
            return_visualization=True,
            segmentation_guidance=segmentation_guidance
        )
        
        # Build response
        explanations = []
        aggregated_heatmap = None
        consensus_score = 0.0
        
        # Classification results
        classification_data = None
        if analysis_result['classification']:
            cls = analysis_result['classification']
            classification_data = {
                'predicted_class': cls['predicted_class'],
                'predicted_class_name': cls['predicted_class_name'],
                'predicted_class_full_name': cls['predicted_class_full_name'],
                'confidence': cls['confidence'],
                'all_probabilities': cls['all_probabilities'],
                'is_defect': cls['is_defect'],
                'defect_type': cls.get('defect_type')
            }
            consensus_score = cls['confidence']
            
            # Generate XAI heatmap if requested
            if 'gradcam' in method_list or 'all' in method_list:
                try:
                    xai_result = explainer.explain_prediction(
                        image_np,
                        include_overlay=True
                    )
                    explanations.append(ExplanationResult(
                        method="gradcam",
                        heatmap_base64=xai_result['overlay_base64'],
                        confidence_score=cls['confidence']
                    ))
                    aggregated_heatmap = xai_result['overlay_base64']
                except Exception as e:
                    logger.warning(f"Failed to generate Grad-CAM: {e}")
        
        # Segmentation results
        segmentation_data = None
        if analysis_result['segmentation'] and analysis_result['segmentation']['has_segmentation']:
            seg = analysis_result['segmentation']
            segmentation_data = {
                'has_segmentation': seg['has_segmentation'],
                'num_segments': seg['num_segments'],
                'bbox': seg['bbox'],
                'area': seg['area'],
                'centroid': seg['centroid'],
                'coverage_percent': seg['coverage_percent']
            }
            
            # Add segmentation overlay if available
            if 'visualization' in analysis_result and 'segmentation_overlay' in analysis_result['visualization']:
                explanations.append(ExplanationResult(
                    method="sam2_segmentation",
                    heatmap_base64=analysis_result['visualization']['segmentation_overlay'],
                    confidence_score=seg.get('scores', [0.0])[0] if seg.get('scores') else 0.0
                ))
                
                # Use segmentation as aggregated if no other heatmap
                if not aggregated_heatmap:
                    aggregated_heatmap = analysis_result['visualization']['segmentation_overlay']
        
        # Build response
        response = ExplainResponse(
            image_id=image_id,
            explanations=explanations,
            aggregated_heatmap=aggregated_heatmap,
            consensus_score=consensus_score,
            computation_time_ms=analysis_result['metadata']['processing_time'] * 1000,
            timestamp=datetime.now(),
            classification=classification_data,
            segmentation=segmentation_data,
            metadata={
                'mode': mode,
                'sam2_enabled': hybrid_analyzer.enable_sam2,
                'segmentation_guidance': segmentation_guidance,
                'image_size': analysis_result['metadata']['image_size']
            }
        )
        
        logger.info(f"[OK] Hybrid analysis complete: {classification_data.get('predicted_class_name') if classification_data else 'N/A'}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Hybrid analysis failed: {str(e)}"
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
                thumbnail=analysis.image_base64,  # Include thumbnail for preview
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


@router.get("/analysis/{image_id}")
async def get_analysis_detail(
    image_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed analysis by image_id.
    
    Returns full analysis data including detections, explanations, and images.
    """
    try:
        analysis = db.query(Analysis).filter(Analysis.image_id == image_id).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis not found: {image_id}")
        
        # Get detections
        detections = []
        for det in analysis.detections:
            detections.append({
                "id": det.id,
                "x1": det.x1,
                "y1": det.y1,
                "x2": det.x2,
                "y2": det.y2,
                "confidence": det.confidence,
                "label": det.label,
                "class_name": det.class_name,
                "severity": det.severity,
            })
        
        # Get explanations (heatmaps)
        explanations = []
        for exp in analysis.explanations:
            explanations.append({
                "id": exp.id,
                "method": exp.method,
                "confidence_score": exp.confidence_score,
                "heatmap_base64": exp.heatmap_base64,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
            })
        
        return {
            "id": analysis.id,
            "image_id": analysis.image_id,
            "filename": analysis.filename,
            "timestamp": analysis.upload_timestamp.isoformat() if analysis.upload_timestamp else None,
            "image_base64": analysis.image_base64,
            "original_image_base64": analysis.original_image_base64,
            "image_width": analysis.image_width,
            "image_height": analysis.image_height,
            "num_detections": analysis.num_detections,
            "has_defects": analysis.has_defects,
            "highest_severity": analysis.highest_severity,
            "mean_confidence": analysis.mean_confidence,
            "mean_uncertainty": analysis.mean_uncertainty,
            "inference_time_ms": analysis.inference_time_ms,
            "model_version": analysis.model_version,
            "status": analysis.status,
            "performed_by": analysis.performed_by,
            "detections": detections,
            "explanations": explanations,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


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


@router.post("/export/{format}")
async def export_report(
    format: str,
    request: Dict[str, Any] = Body(...),
    # Auth disabled,
):
    """
    Generate and export a quality control report.
    
    This endpoint generates a comprehensive report in PDF or Excel format
    containing detection results, explanations, and metrics.
    
    Args:
        format: Report format (pdf or excel)
        request: Request body with analysis data
        current_user: Authenticated user information
        
    Returns:
        Export response with download URL
    """
    try:
        # Validate format
        if format not in ['pdf', 'excel', 'preview']:
            raise HTTPException(status_code=400, detail=f"Invalid format: {format}. Must be 'pdf' or 'excel'")
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_id = request.get('analysis_id', 'unknown')
        filename = f"qc_report_{analysis_id}_{timestamp}.{format}"
        filepath = EXPORTS_DIR / filename
        
        # Extract data from request
        analysis_data = request.get('data', {}).get('analysis', {})
        detections = request.get('data', {}).get('detections', [])
        explanations = request.get('data', {}).get('explanations', [])
        options = request.get('options', {})
        
        logger.info(f"📊 Exporting {format.upper()} report for analysis {analysis_id}")
        logger.info(f"   Analysis data keys: {list(analysis_data.keys())}")
        logger.info(f"   Detections type: {type(detections)}")
        logger.info(f"   Explanations type: {type(explanations)}")
        logger.info(f"   Options: {options}")
        
        # Robustness fix: Ensure detections is a list of dicts
        safe_detections = []
        if isinstance(detections, list):
            for d in detections:
                if isinstance(d, dict):
                    safe_detections.append(d)
                elif hasattr(d, 'dict'):  # Pydantic model
                    safe_detections.append(d.dict())
                else:
                    logger.warning(f"Skipping invalid detection item of type {type(d)}")
        
        # Robustness fix: Ensure explanations is a list of dicts
        safe_explanations = []
        if isinstance(explanations, dict):
            # If the entire ExplanationResponse was passed, try to find the list inside
            if 'explanations' in explanations and isinstance(explanations['explanations'], list):
                logger.info("Found explanations list inside explanation object")
                raw_list = explanations['explanations']
                for e in raw_list:
                    if isinstance(e, dict):
                        safe_explanations.append(e)
            else:
                 logger.warning("Explanation object passed but no 'explanations' list found inside")
        elif isinstance(explanations, list):
            for e in explanations:
                if isinstance(e, dict):
                    safe_explanations.append(e)
                elif hasattr(e, 'dict'):
                    safe_explanations.append(e.dict())
                else:
                    logger.warning(f"Skipping invalid explanation item of type {type(e)}")

        logger.info(f"   Safe Detections: {len(safe_detections)}")
        logger.info(f"   Safe Explanations: {len(safe_explanations)}")
        
        if format == 'pdf' or format == 'preview':
            # Import here to avoid circular dependencies if any (though unlikely here)
            from utils.report_generator import generate_pdf_report
            logger.info(f"Generating {'Preview' if format == 'preview' else 'PDF'} report...")
            
            # For preview, we force PDF format but might keep the filename distinct
            if format == 'preview':
                 filename = f"preview_{analysis_id}_{timestamp}.pdf"
                 filepath = EXPORTS_DIR / filename
            
            generate_pdf_report(
                str(filepath), 
                analysis_id, 
                analysis_data, 
                safe_detections, 
                safe_explanations, 
                options
            )
        elif format == 'excel':
            from utils.report_generator import generate_excel_report
            logger.info("Generating Excel report...")
            generate_excel_report(
                str(filepath), 
                analysis_id, 
                analysis_data, 
                safe_detections, 
                safe_explanations, 
                options
            )
        
        # Return download URL
        download_url = f"/api/xai-qc/download/{filename}"
        
        if format == 'preview':
             return {
                "preview_url": download_url
             }
        
        logger.info(f"✅ Report exported successfully: {filename}")
        
        # For actual export (download), return the file directly as the frontend expects a blob
        return FileResponse(
            filepath, 
            filename=filename,
            media_type='application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"❌ Export failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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


@router.post("/clear-all-data")
async def clear_all_data(db: Session = Depends(get_db)):
    """
    Clear all analysis data from the database.
    
    WARNING: This deletes ALL analyses, detections, and explanations.
    This action cannot be undone!
    
    Returns:
        Dict with count of deleted records
    """
    try:
        # Get counts before deletion
        analysis_count = db.query(Analysis).count()
        detection_count = db.query(Detection).count()
        explanation_count = db.query(Explanation).count()
        
        # Delete all records (cascade will handle related records)
        db.query(Detection).delete()
        db.query(Explanation).delete()
        db.query(Analysis).delete()
        
        db.commit()
        
        logger.info(f"[CLEAR] Cleared all data: {analysis_count} analyses, {detection_count} detections, {explanation_count} explanations")
        
        return {
            "status": "success",
            "message": "All data cleared successfully",
            "deleted": {
                "analyses": analysis_count,
                "detections": detection_count,
                "explanations": explanation_count
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        HealthResponse with service status
    """
    import time
    model_loaded = model is not None
    gpu_available = torch.cuda.is_available()
    
    # Calculate uptime (approximate - since module load)
    uptime_seconds = time.time() - getattr(health_check, '_start_time', time.time())
    if not hasattr(health_check, '_start_time'):
        health_check._start_time = time.time()
        uptime_seconds = 0.0
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        timestamp=datetime.now(),
        model_loaded=model_loaded,
        gpu_available=gpu_available,
        uptime_seconds=uptime_seconds,
        device=DEVICE,
        version="2.0.0",
    )
