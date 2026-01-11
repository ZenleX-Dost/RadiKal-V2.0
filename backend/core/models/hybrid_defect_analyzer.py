"""
Hybrid Defect Analyzer: YOLOv8 Classification + SAM2 Segmentation

This module combines two powerful models for comprehensive weld defect analysis:
    1. YOLOv8 Classification: Determines defect type (LP, PO, CR, ND)
    2. SAM2 Segmentation: Provides precise pixel-level defect localization

Architecture Flow:
    Input Image 
        → YOLOv8 Classifier → Defect Type + Confidence
        → SAM2 Segmenter → Pixel Mask + Location
        → Unified Output: Type, Mask, Metrics, XAI

Author: RadiKal Team
Date: 2026-01-09
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from PIL import Image
import logging

from core.models.yolo_classifier import YOLOClassifier
from core.models.sam2_segmenter import SAM2Segmenter

logger = logging.getLogger(__name__)


class HybridDefectAnalyzer:
    """
    Unified defect analysis combining classification and segmentation.
    
    Modes of Operation:
        1. Classification Only: Fast defect type identification
        2. Segmentation Only: Detailed mask generation (requires manual review)
        3. Hybrid (Recommended): Classification guides segmentation for optimal results
    """
    
    def __init__(
        self,
        classifier_path: str = "models/yolo/classification_defect_focused/weights/best.pt",
        segmenter_size: str = "small",
        segmenter_path: Optional[str] = None,
        device: Optional[str] = None,
        nd_threshold: float = 0.7,
        enable_sam2: bool = True
    ):
        """
        Initialize hybrid analyzer.
        
        Args:
            classifier_path: Path to YOLOv8 classification weights
            segmenter_size: SAM2 model size ('tiny', 'small', 'base', 'large')
            segmenter_path: Optional custom SAM2 checkpoint path
            device: Device for inference ('cuda', 'cpu', None=auto)
            nd_threshold: Confidence threshold for "No Defect" classification
            enable_sam2: Whether to enable SAM2 segmentation (can disable for faster inference)
        """
        self.device = device
        self.enable_sam2 = enable_sam2
        
        # Initialize YOLOv8 classifier
        logger.info("Initializing YOLOv8 Classifier...")
        self.classifier = YOLOClassifier(
            model_path=classifier_path,
            device=device,
            nd_confidence_threshold=nd_threshold
        )
        logger.info("[OK] YOLOv8 Classifier loaded")
        
        # Initialize SAM2 segmenter (optional)
        self.segmenter = None
        if enable_sam2:
            try:
                logger.info("Initializing SAM2 Segmenter...")
                self.segmenter = SAM2Segmenter(
                    model_size=segmenter_size,
                    model_path=segmenter_path,
                    device=device,
                    conf_threshold=0.1,  # Very low threshold for radiographic images
                    mask_threshold=0.3   # Lower for more permissive mask generation
                )
                logger.info("[OK] SAM2 Segmenter loaded")
            except ImportError as e:
                logger.warning(f"[WARN] SAM2 not available: {e}")
                logger.warning("[WARN] Segmentation features will be disabled")
                self.enable_sam2 = False
            except Exception as e:
                logger.error(f"[ERROR] Failed to load SAM2: {e}")
                logger.warning("[WARN] Continuing with classification only")
                self.enable_sam2 = False
    
    def analyze(
        self,
        image: Union[np.ndarray, Image.Image, str],
        mode: str = "hybrid",
        return_visualization: bool = True,
        segmentation_guidance: str = "auto"
    ) -> Dict[str, Any]:
        """
        Comprehensive defect analysis.
        
        Args:
            image: Input radiographic image
            mode: Analysis mode ('classification', 'segmentation', 'hybrid')
            return_visualization: Whether to return overlay visualizations
            segmentation_guidance: How to guide SAM2 ('auto', 'center', 'grid')
                - 'auto': Use image center for defect images, auto-segment for ND
                - 'center': Always use center point prompt
                - 'grid': Use grid-based automatic segmentation
        
        Returns:
            Dictionary with comprehensive analysis results:
                classification: {
                    predicted_class: int
                    predicted_class_name: str (LP, PO, CR, ND)
                    predicted_class_full_name: str
                    confidence: float
                    all_probabilities: dict
                    is_defect: bool
                    defect_type: Optional[str]
                }
                segmentation: {
                    has_segmentation: bool
                    masks: List of binary masks
                    scores: List of confidence scores
                    num_segments: int
                    primary_mask: Binary mask array
                    bbox: [x, y, w, h]
                    area: int (pixels)
                    centroid: [x, y]
                    coverage_percent: float
                }
                metadata: {
                    mode: str
                    sam2_enabled: bool
                    image_size: tuple
                    processing_time: float
                }
                visualization: Optional[{
                    classification_heatmap: base64 image
                    segmentation_overlay: base64 image
                    combined_overlay: base64 image
                }]
        """
        import time
        start_time = time.time()
        
        # Convert image to numpy if needed
        if isinstance(image, str):
            image_np = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            image_np = np.array(image.convert('RGB'))
        else:
            image_np = image
        
        result = {
            'classification': None,
            'segmentation': None,
            'metadata': {
                'mode': mode,
                'sam2_enabled': self.enable_sam2,
                'image_size': image_np.shape[:2],
                'processing_time': 0.0
            }
        }
        
        # Step 1: Classification (always run unless mode='segmentation')
        if mode in ['classification', 'hybrid']:
            logger.info("Running YOLOv8 classification...")
            classification_result = self.classifier.classify(
                image_np,
                apply_nd_threshold=True
            )
            result['classification'] = classification_result
            logger.info(
                f"Classification: {classification_result['predicted_class_name']} "
                f"({classification_result['confidence']:.3f})"
            )
        
        # Step 2: Segmentation (if enabled and requested)
        if mode in ['segmentation', 'hybrid'] and self.enable_sam2:
            logger.info("Running SAM2 segmentation...")
            
            # Determine segmentation strategy based on classification
            if mode == 'hybrid' and result['classification']:
                is_defect = result['classification']['is_defect']
                
                if is_defect:
                    # Defect detected: Use center point prompting for faster inference
                    # This targets the main defect region which is typically centered
                    logger.info("Defect detected - using center-point segmentation (fast mode)")
                    
                    h, w = image_np.shape[:2]
                    center_point = np.array([[w // 2, h // 2]], dtype=np.float32)
                    
                    seg_result = self.segmenter.segment_defect(
                        image=image_np,
                        prompt_points=center_point,
                        auto_segment=False
                    )
                    
                    # If center point gives no result, try intensity-based fallback
                    if seg_result.get('num_segments', 0) == 0:
                        logger.info("Center point gave no result, trying intensity-based detection...")
                        seg_result = self.segmenter.segment_defect(
                            image=image_np,
                            auto_segment=True  # This will trigger intensity fallback
                        )
                else:
                    # No defect: Just use center point for quick verification
                    h, w = image_np.shape[:2]
                    center_point = np.array([[w // 2, h // 2]], dtype=np.float32)
                    
                    seg_result = self.segmenter.segment_defect(
                        image=image_np,
                        prompt_points=center_point,
                        auto_segment=False
                    )
            else:
                # Segmentation-only mode: use center point for speed
                h, w = image_np.shape[:2]
                center_point = np.array([[w // 2, h // 2]], dtype=np.float32)
                
                seg_result = self.segmenter.segment_defect(
                    image=image_np,
                    prompt_points=center_point,
                    auto_segment=False
                )
            
            # Calculate coverage
            if seg_result['primary_mask'] is not None:
                primary_mask_np = np.array(seg_result['primary_mask'])
                total_pixels = image_np.shape[0] * image_np.shape[1]
                coverage_percent = (seg_result['area'] / total_pixels) * 100
                seg_result['coverage_percent'] = coverage_percent
            else:
                seg_result['coverage_percent'] = 0.0
            
            seg_result['has_segmentation'] = seg_result['num_segments'] > 0
            result['segmentation'] = seg_result
            
            logger.info(
                f"Segmentation: {seg_result['num_segments']} masks, "
                f"coverage={seg_result['coverage_percent']:.2f}%"
            )
        else:
            result['segmentation'] = {'has_segmentation': False}
        
        # Step 3: Generate visualizations (if requested)
        if return_visualization:
            result['visualization'] = self._generate_visualizations(
                image_np,
                result
            )
        
        # Finalize
        result['metadata']['processing_time'] = time.time() - start_time
        
        return result
    
    def _generate_visualizations(
        self,
        image: np.ndarray,
        result: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate visualization overlays with prominent defect outlines.
        
        Returns base64-encoded images for frontend display.
        """
        import base64
        from io import BytesIO
        
        vis = {}
        
        # Segmentation overlay with prominent outlines
        if result['segmentation'] and result['segmentation']['has_segmentation']:
            seg = result['segmentation']
            
            # Create mask overlay
            overlay = image.copy()
            
            # Define colors for different defect types
            defect_colors = {
                'LP': (255, 50, 50),    # Red for Lack of Penetration
                'PO': (255, 165, 0),    # Orange for Porosity
                'CR': (200, 0, 200),    # Purple for Cracks
                'ND': (0, 200, 0),      # Green for No Defect
            }
            
            # Get defect type from classification
            defect_type = result.get('classification', {}).get('predicted_class_name', 'LP')
            outline_color = defect_colors.get(defect_type, (255, 50, 50))
            fill_color = tuple(int(c * 0.7) for c in outline_color)  # Slightly darker fill
            
            # Draw all masks if available
            masks_to_draw = seg.get('masks', [])
            if not masks_to_draw and seg.get('primary_mask') is not None:
                masks_to_draw = [seg['primary_mask']]
            
            for i, mask_data in enumerate(masks_to_draw):
                mask = np.array(mask_data, dtype=np.uint8)
                
                # Create colored overlay for mask fill
                colored_mask = np.zeros_like(image)
                colored_mask[mask > 0] = fill_color
                
                # Blend fill with lower opacity
                alpha = 0.3
                overlay = cv2.addWeighted(overlay, 1, colored_mask, alpha, 0)
                
                # Find and draw contours with thick, prominent lines
                contours, _ = cv2.findContours(
                    mask,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                
                # Draw thick outline (3 layers for glow effect)
                cv2.drawContours(overlay, contours, -1, (0, 0, 0), 6)  # Black outer shadow
                cv2.drawContours(overlay, contours, -1, outline_color, 4)  # Main outline
                cv2.drawContours(overlay, contours, -1, (255, 255, 255), 1)  # White inner highlight
            
            # Draw bounding box with dashed effect
            if seg.get('bbox') and any(seg['bbox']):
                x, y, w, h = seg['bbox']
                # Outer box shadow
                cv2.rectangle(overlay, (x-1, y-1), (x + w+1, y + h+1), (0, 0, 0), 3)
                # Main bounding box
                cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Add corner markers
                corner_len = min(w, h) // 4
                cv2.line(overlay, (x, y), (x + corner_len, y), (0, 255, 255), 3)
                cv2.line(overlay, (x, y), (x, y + corner_len), (0, 255, 255), 3)
                cv2.line(overlay, (x + w, y), (x + w - corner_len, y), (0, 255, 255), 3)
                cv2.line(overlay, (x + w, y), (x + w, y + corner_len), (0, 255, 255), 3)
                cv2.line(overlay, (x, y + h), (x + corner_len, y + h), (0, 255, 255), 3)
                cv2.line(overlay, (x, y + h), (x, y + h - corner_len), (0, 255, 255), 3)
                cv2.line(overlay, (x + w, y + h), (x + w - corner_len, y + h), (0, 255, 255), 3)
                cv2.line(overlay, (x + w, y + h), (x + w, y + h - corner_len), (0, 255, 255), 3)
            
            # Draw centroid with crosshair
            if seg.get('centroid'):
                cx, cy = int(seg['centroid'][0]), int(seg['centroid'][1])
                crosshair_size = 15
                cv2.line(overlay, (cx - crosshair_size, cy), (cx + crosshair_size, cy), (255, 255, 0), 2)
                cv2.line(overlay, (cx, cy - crosshair_size), (cx, cy + crosshair_size), (255, 255, 0), 2)
                cv2.circle(overlay, (cx, cy), 8, (255, 255, 0), 2)
                cv2.circle(overlay, (cx, cy), 3, (255, 255, 0), -1)
            
            # Add defect label
            if result.get('classification'):
                cls = result['classification']
                label = f"{cls['predicted_class_name']} ({cls['confidence']*100:.1f}%)"
                
                # Position label above bounding box or at top
                if seg.get('bbox') and any(seg['bbox']):
                    x, y, w, h = seg['bbox']
                    label_pos = (x, max(y - 10, 25))
                else:
                    label_pos = (10, 30)
                
                # Draw label background
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(overlay, 
                            (label_pos[0] - 2, label_pos[1] - text_h - 5),
                            (label_pos[0] + text_w + 2, label_pos[1] + 5),
                            (0, 0, 0), -1)
                
                # Draw label text
                cv2.putText(overlay, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, outline_color, 2)
            
            # Convert to base64
            pil_img = Image.fromarray(overlay)
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            vis['segmentation_overlay'] = base64.b64encode(buffered.getvalue()).decode()
        
        # Classification info overlay
        if result['classification']:
            cls = result['classification']
            overlay = image.copy()
            
            # Add text overlay
            text = f"{cls['predicted_class_name']}: {cls['confidence']:.2f}"
            color = (0, 255, 0) if cls['is_defect'] else (255, 255, 0)
            
            cv2.putText(
                overlay,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                color,
                2
            )
            
            # Convert to base64
            pil_img = Image.fromarray(overlay)
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            vis['classification_overlay'] = base64.b64encode(buffered.getvalue()).decode()
        
        return vis
    
    def classify_only(self, image: Union[np.ndarray, Image.Image, str]) -> Dict[str, Any]:
        """Quick classification without segmentation."""
        return self.analyze(image, mode='classification', return_visualization=False)
    
    def segment_only(self, image: Union[np.ndarray, Image.Image, str]) -> Dict[str, Any]:
        """Segmentation without classification (requires SAM2)."""
        if not self.enable_sam2:
            raise RuntimeError("SAM2 segmentation is not enabled")
        return self.analyze(image, mode='segmentation', return_visualization=False)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        info = {
            'classifier': self.classifier.get_model_info() if hasattr(self.classifier, 'get_model_info') else None,
            'segmenter': self.segmenter.get_model_info() if self.segmenter else None,
            'sam2_enabled': self.enable_sam2,
            'device': self.device
        }
        return info
    
    def enable_segmentation(self, enable: bool = True):
        """Enable or disable SAM2 segmentation at runtime."""
        if enable and self.segmenter is None:
            raise RuntimeError("SAM2 was not initialized. Restart analyzer with enable_sam2=True")
        self.enable_sam2 = enable
        logger.info(f"SAM2 segmentation {'enabled' if enable else 'disabled'}")
