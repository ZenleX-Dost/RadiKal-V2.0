"""
Classification Explainability Service for RadiKal

Provides comprehensive explainability features for the YOLOv8 classification model:
- Grad-CAM heatmaps showing defect locations
- Class probability visualizations
- Defect region localization
- Operator-friendly explanations
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import cv2
import base64
from pathlib import Path
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from core.xai.grad_cam_classifier import YOLOv8ClassifierGradCAM
from core.xai.lime_explainer import LIMEExplainer
from core.xai.shap_explainer import SHAPExplainer
from core.xai.integrated_gradients import IntegratedGradientsExplainer
from core.xai.aggregator import XAIAggregator, AggregationMethod
from core.models.yolo_classifier import YOLOClassifier

logger = logging.getLogger(__name__)


class ClassificationExplainer:
    """
    Main service for generating explainability outputs for classification model.
    """
    
    # Class info
    CLASS_INFO = {
        0: {
            'code': 'LP',
            'name': 'Lack of Penetration',
            'color': (255, 100, 100),  # BGR: Light Red
            'severity': 'CRITICAL',
            'description': 'Incomplete fusion at weld root - requires repair'
        },
        1: {
            'code': 'PO',
            'name': 'Porosity',
            'color': (100, 200, 255),  # BGR: Light Orange
            'severity': 'MEDIUM',
            'description': 'Gas pockets in weld metal - assess density and size'
        },
        2: {
            'code': 'CR',
            'name': 'Cracks',
            'color': (100, 100, 255),  # BGR: Red
            'severity': 'CRITICAL',
            'description': 'Linear discontinuities - immediate rejection required'
        },
        3: {
            'code': 'ND',
            'name': 'No Defect',
            'color': (100, 255, 100),  # BGR: Light Green
            'severity': 'ACCEPTABLE',
            'description': 'Weld meets quality standards'
        }
    }
    
    def __init__(self, classifier: YOLOClassifier):
        """
        Initialize explainer with a classifier.
        
        Args:
            classifier: Loaded YOLOClassifier instance
        """
        self.classifier = classifier
        self.gradcam = YOLOv8ClassifierGradCAM(classifier.model)
        
        # Initialize additional XAI methods (lazy loading to save memory)
        self._lime = None
        self._shap = None
        self._ig = None
        self._aggregator = XAIAggregator(method=AggregationMethod.MEAN)
        
        logger.info("ClassificationExplainer initialized with Grad-CAM (LIME/SHAP/IG available)")
    
    @property
    def lime(self) -> LIMEExplainer:
        """Lazy load LIME explainer."""
        if self._lime is None:
            logger.info("Initializing LIME explainer...")
            self._lime = LIMEExplainer(
                self.classifier.model,
                num_samples=500,  # Lower for faster inference
                num_features=10
            )
        return self._lime
    
    @property
    def shap_explainer(self) -> SHAPExplainer:
        """Lazy load SHAP explainer."""
        if self._shap is None:
            logger.info("Initializing SHAP explainer...")
            self._shap = SHAPExplainer(
                self.classifier.model,
                num_background=20  # Lower for faster inference
            )
        return self._shap
    
    @property
    def ig_explainer(self) -> IntegratedGradientsExplainer:
        """Lazy load Integrated Gradients explainer."""
        if self._ig is None:
            logger.info("Initializing Integrated Gradients explainer...")
            self._ig = IntegratedGradientsExplainer(
                self.classifier.model,
                n_steps=50
            )
        return self._ig
    
    def explain_prediction(
        self,
        image_path: str,
        include_overlay: bool = True,
        include_regions: bool = True,
        include_description: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete explanation for a prediction.
        
        Args:
            image_path: Path to radiographic image
            include_overlay: Include heatmap overlay image
            include_regions: Detect and describe defect regions
            include_description: Generate natural language description
        
        Returns:
            Dict with explanation data:
                - prediction: Predicted class info
                - probabilities: All class probabilities
                - heatmap_base64: Grad-CAM heatmap as base64 PNG
                - overlay_base64: Heatmap overlay on original image
                - regions: Detected defect regions
                - description: Natural language explanation
                - recommendation: Action recommendation
        """
        logger.info(f"Explaining prediction for: {image_path}")
        
        # Load original image
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Get classifier prediction (pass image path, YOLO can handle it)
        pred_result = self.classifier.classify(image_path)
        
        # Generate Grad-CAM
        heatmap, cam_info = self.gradcam.generate_heatmap(
            image_path,
            target_class=pred_result['predicted_class']
        )
        
        # Create heatmap base64
        heatmap_base64 = self._heatmap_to_base64(heatmap)
        
        # Create overlay if requested
        overlay_base64 = None
        if include_overlay:
            overlay = self.gradcam.generate_overlay(original_image, heatmap, alpha=0.4)
            overlay_base64 = self._image_to_base64(overlay)
        
        # Detect regions if requested
        regions = []
        location_desc = ""
        if include_regions:
            raw_regions = self.gradcam.find_defect_regions(heatmap, threshold=0.5, min_area=50)
            # Transform regions to frontend format
            regions = [
                {
                    'x': r['bbox'][0],
                    'y': r['bbox'][1],
                    'width': r['bbox'][2],
                    'height': r['bbox'][3],
                    'coverage': r['area'] / (heatmap.shape[0] * heatmap.shape[1]),  # Normalized coverage
                    'intensity': r['score']  # Average activation score
                }
                for r in raw_regions
            ]
            if raw_regions:
                location_desc = self.gradcam.describe_defect_location(raw_regions, heatmap.shape)
        
        # Generate description
        description = ""
        recommendation = ""
        if include_description:
            description, recommendation = self._generate_description(
                pred_result,
                regions,
                location_desc
            )
        
        # Compile result
        result = {
            'prediction': {
                'class_id': pred_result['predicted_class'],
                'class_code': pred_result['predicted_class_name'],  # 'LP', 'PO', etc.
                'class_full_name': pred_result['predicted_class_full_name'],  # 'Lack of Penetration', etc.
                'confidence': pred_result['confidence'],
                'is_defect': pred_result['is_defect'],
                'severity': self.CLASS_INFO[pred_result['predicted_class']]['severity']
            },
            'probabilities': [
                {
                    'class_id': i,
                    'class_code': self.classifier.CLASS_NAMES[i],
                    'class_name': self.CLASS_INFO[i]['name'],
                    'probability': float(pred_result['all_probabilities'][self.classifier.CLASS_NAMES[i]]),
                    'color': self.CLASS_INFO[i]['color']
                }
                for i in range(4)  # LP, PO, CR, ND
            ],
            'heatmap_base64': heatmap_base64,
            'overlay_base64': overlay_base64,
            'regions': regions,
            'location_description': location_desc,
            'description': description,
            'recommendation': recommendation,
            'cam_info': cam_info
        }
        
        return result
    
    def generate_comparison_heatmaps(
        self,
        image_path: str
    ) -> Dict[str, str]:
        """
        Generate Grad-CAM heatmaps for all classes (useful for comparison).
        
        Args:
            image_path: Path to image
        
        Returns:
            Dict mapping class codes to base64 heatmaps
        """
        heatmaps = {}
        
        for class_id in range(4):
            try:
                heatmap, _ = self.gradcam.generate_heatmap(
                    image_path,
                    target_class=class_id
                )
                class_code = self.classifier.CLASS_NAMES[class_id]
                heatmaps[class_code] = self._heatmap_to_base64(heatmap)
            except Exception as e:
                logger.error(f"Failed to generate heatmap for class {class_id}: {e}")
        
        return heatmaps
    
    def explain_with_methods(
        self,
        image_path: str,
        methods: List[str] = None,
        include_aggregated: bool = True
    ) -> Dict[str, Any]:
        """
        Generate explanations using multiple XAI methods.
        
        Args:
            image_path: Path to radiographic image
            methods: List of methods to use ('gradcam', 'lime', 'shap', 'ig', 'all')
                    If None or 'all', uses all available methods
            include_aggregated: Whether to include aggregated consensus heatmap
            
        Returns:
            Dict with method-specific explanations and optional aggregated result
        """
        if methods is None or 'all' in methods:
            methods = ['gradcam', 'lime', 'shap', 'ig']
        
        logger.info(f"Generating multi-method explanations: {methods}")
        
        # Load image
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Get prediction first
        pred_result = self.classifier.classify(image_path)
        target_class = pred_result['predicted_class']
        
        results = {
            'prediction': {
                'class_id': pred_result['predicted_class'],
                'class_code': pred_result['predicted_class_name'],
                'class_full_name': pred_result['predicted_class_full_name'],
                'confidence': pred_result['confidence'],
                'is_defect': pred_result['is_defect'],
                'severity': self.CLASS_INFO[pred_result['predicted_class']]['severity']
            },
            'probabilities': [
                {
                    'class_id': i,
                    'class_code': self.classifier.CLASS_NAMES[i],
                    'class_name': self.CLASS_INFO[i]['name'],
                    'probability': float(pred_result['all_probabilities'][self.classifier.CLASS_NAMES[i]]),
                }
                for i in range(4)
            ],
            'methods': {}
        }
        
        heatmaps_for_aggregation = {}
        
        # Generate Grad-CAM
        if 'gradcam' in methods:
            try:
                logger.info("Generating Grad-CAM...")
                heatmap, cam_info = self.gradcam.generate_heatmap(image_path, target_class=target_class)
                overlay = self.gradcam.generate_overlay(original_image, heatmap, alpha=0.4)
                
                results['methods']['gradcam'] = {
                    'heatmap_base64': self._heatmap_to_base64(heatmap),
                    'overlay_base64': self._image_to_base64(overlay),
                    'confidence_score': float(pred_result['confidence']),
                    'metadata': cam_info
                }
                heatmaps_for_aggregation['gradcam'] = heatmap
                
            except Exception as e:
                logger.error(f"Grad-CAM failed: {e}")
                results['methods']['gradcam'] = {'error': str(e)}
        
        # Generate LIME
        if 'lime' in methods:
            try:
                logger.info("Generating LIME explanation...")
                lime_overlay, lime_metadata = self.lime.explain(
                    original_image,
                    target_class=target_class,
                    num_samples=300,  # Faster inference
                    num_features=8
                )
                
                results['methods']['lime'] = {
                    'overlay_base64': self._image_to_base64(lime_overlay),
                    'confidence_score': lime_metadata.get('explanation_score', 0.0),
                    'metadata': lime_metadata
                }
                # Note: LIME doesn't produce a clean heatmap for aggregation
                
            except Exception as e:
                logger.error(f"LIME failed: {e}")
                results['methods']['lime'] = {'error': str(e)}
        
        # Generate SHAP
        if 'shap' in methods:
            try:
                logger.info("Generating SHAP explanation...")
                # SHAP requires tensor input
                import torch
                from torchvision import transforms
                
                transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.Resize((224, 224)),
                    transforms.ToTensor()
                ])
                
                img_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                img_tensor = transform(img_rgb).unsqueeze(0)
                
                shap_values = self.shap_explainer.explain(img_tensor, target_class=target_class)
                shap_heatmap = self.shap_explainer.visualize(shap_values, img_tensor)
                
                # Convert to BGR for consistency
                shap_heatmap_bgr = cv2.cvtColor(shap_heatmap, cv2.COLOR_RGB2BGR)
                
                results['methods']['shap'] = {
                    'overlay_base64': self._image_to_base64(shap_heatmap_bgr),
                    'confidence_score': float(pred_result['confidence']),
                    'metadata': {'method': 'shap', 'target_class': target_class}
                }
                
            except Exception as e:
                logger.error(f"SHAP failed: {e}")
                results['methods']['shap'] = {'error': str(e)}
        
        # Generate Integrated Gradients
        if 'ig' in methods:
            try:
                logger.info("Generating Integrated Gradients...")
                import torch
                from torchvision import transforms
                
                transform = transforms.Compose([
                    transforms.ToPILImage(),
                    transforms.Resize((224, 224)),
                    transforms.ToTensor()
                ])
                
                img_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                img_tensor = transform(img_rgb).unsqueeze(0)
                
                ig_attributions = self.ig_explainer.explain(img_tensor, target_class=target_class)
                ig_heatmap = self.ig_explainer.visualize(ig_attributions, img_tensor)
                
                # Convert to BGR
                ig_heatmap_bgr = cv2.cvtColor(ig_heatmap, cv2.COLOR_RGB2BGR)
                
                results['methods']['ig'] = {
                    'overlay_base64': self._image_to_base64(ig_heatmap_bgr),
                    'confidence_score': float(pred_result['confidence']),
                    'metadata': {'method': 'integrated_gradients', 'target_class': target_class}
                }
                
            except Exception as e:
                logger.error(f"Integrated Gradients failed: {e}")
                results['methods']['ig'] = {'error': str(e)}
        
        # Aggregate heatmaps if requested and multiple methods succeeded
        if include_aggregated and len(heatmaps_for_aggregation) > 1:
            try:
                logger.info(f"Aggregating {len(heatmaps_for_aggregation)} heatmaps...")
                aggregated_heatmap = self._aggregator.aggregate(heatmaps_for_aggregation)
                aggregated_overlay = self.gradcam.generate_overlay(original_image, aggregated_heatmap, alpha=0.4)
                
                results['aggregated'] = {
                    'heatmap_base64': self._heatmap_to_base64(aggregated_heatmap),
                    'overlay_base64': self._image_to_base64(aggregated_overlay),
                    'consensus_score': float(pred_result['confidence']),
                    'methods_used': list(heatmaps_for_aggregation.keys())
                }
                
            except Exception as e:
                logger.error(f"Aggregation failed: {e}")
        
        logger.info(f"Multi-method explanation complete. Methods: {list(results['methods'].keys())}")
        return results
    
    def create_visualization_panel(
        self,
        image_path: str,
        output_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Create comprehensive visualization panel for operators.
        
        Panel includes:
        - Original image
        - Grad-CAM heatmap overlay
        - Class probabilities bar chart
        - Prediction details
        - Recommendations
        
        Args:
            image_path: Path to image
            output_path: Optional path to save panel
        
        Returns:
            Visualization panel as numpy array
        """
        # Get explanation
        explanation = self.explain_prediction(image_path)
        
        # Load images
        original = cv2.imread(str(image_path))
        overlay_base64 = explanation['overlay_base64']
        overlay = self._base64_to_image(overlay_base64)
        
        # Create panel (side-by-side layout)
        h, w = original.shape[:2]
        panel_width = w * 2 + 100  # Space between images
        panel_height = h + 400  # Extra space for info at bottom
        
        panel = np.ones((panel_height, panel_width, 3), dtype=np.uint8) * 255
        
        # Place original image (left)
        panel[0:h, 0:w] = original
        
        # Place overlay (right)
        panel[0:h, w+100:w*2+100] = overlay
        
        # Add labels
        cv2.putText(panel, "Original Image", (10, h+40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(panel, "Defect Localization (Grad-CAM)", (w+110, h+40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        
        # Add prediction info
        pred = explanation['prediction']
        y_offset = h + 100
        
        cv2.putText(panel, f"Classification: {pred['class_full_name']} ({pred['class_code']})",
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        
        cv2.putText(panel, f"Confidence: {pred['confidence']*100:.1f}%",
                   (10, y_offset+40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        
        cv2.putText(panel, f"Severity: {pred['severity']}",
                   (10, y_offset+80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        
        # Add location description
        if explanation['location_description']:
            cv2.putText(panel, explanation['location_description'],
                       (10, y_offset+120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 100), 2)
        
        # Draw probability bars
        bar_x = w + 110
        bar_y = h + 100
        bar_width = 400
        bar_height = 30
        
        for i, prob_info in enumerate(explanation['probabilities']):
            y = bar_y + i * (bar_height + 10)
            
            # Background
            cv2.rectangle(panel, (bar_x, y), (bar_x + bar_width, y + bar_height),
                         (200, 200, 200), -1)
            
            # Filled portion
            filled_width = int(bar_width * prob_info['probability'])
            color = prob_info['color']
            cv2.rectangle(panel, (bar_x, y), (bar_x + filled_width, y + bar_height),
                         color, -1)
            
            # Label
            label = f"{prob_info['class_code']}: {prob_info['probability']*100:.1f}%"
            cv2.putText(panel, label, (bar_x + bar_width + 10, y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # Save if requested
        if output_path:
            cv2.imwrite(str(output_path), panel)
            logger.info(f"Visualization panel saved to: {output_path}")
        
        return panel
    
    def _generate_description(
        self,
        pred_result: Dict,
        regions: List,
        location_desc: str
    ) -> Tuple[str, str]:
        """Generate natural language description and recommendation."""
        class_id = pred_result['predicted_class']
        class_name = self.CLASS_INFO[class_id]['name']
        confidence = pred_result['confidence'] * 100
        
        # Description
        if pred_result['is_defect']:
            if regions:
                description = (
                    f"The model detected {class_name} with {confidence:.1f}% confidence. "
                    f"{location_desc}. "
                    f"The highlighted regions indicate where the defect characteristics are most prominent."
                )
            else:
                description = (
                    f"The model classified this as {class_name} with {confidence:.1f}% confidence. "
                    f"The defect characteristics are distributed across the weld area."
                )
        else:
            description = (
                f"The model classified this weld as acceptable (No Defect) with {confidence:.1f}% confidence. "
                f"No significant defect indications were detected."
            )
        
        # Recommendation
        severity = self.CLASS_INFO[class_id]['severity']
        
        if severity == 'CRITICAL':
            recommendation = (
                "⚠️ CRITICAL: This weld requires immediate attention. "
                "Recommend rejection and repair according to welding procedure specifications."
            )
        elif severity == 'MEDIUM':
            recommendation = (
                "⚡ MEDIUM: Assess defect density and size against acceptance criteria. "
                "May require further evaluation or repair depending on standards."
            )
        else:
            recommendation = (
                "✅ ACCEPTABLE: Weld meets quality standards. "
                "Proceed with production or final inspection."
            )
        
        return description, recommendation
    
    def _heatmap_to_base64(self, heatmap: np.ndarray) -> str:
        """Convert heatmap to base64 PNG."""
        # Normalize to [0, 255]
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        # Encode to PNG
        success, buffer = cv2.imencode('.png', heatmap_colored)
        if not success:
            raise ValueError("Failed to encode heatmap")
        
        # Base64 encode
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        return base64_str
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert BGR image to base64 PNG."""
        success, buffer = cv2.imencode('.png', image)
        if not success:
            raise ValueError("Failed to encode image")
        
        base64_str = base64.b64encode(buffer).decode('utf-8')
        return base64_str
    
    def _base64_to_image(self, base64_str: str) -> np.ndarray:
        """Convert base64 PNG to BGR image."""
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image


def test_explainer():
    """Test the explainer."""
    from core.models.yolo_classifier import YOLOClassifier
    
    # Load classifier
    classifier = YOLOClassifier()
    
    # Create explainer
    explainer = ClassificationExplainer(classifier)
    
    # Test on sample images
    test_images = [
        "DATA/testing/Difetto1/00006.jpg",  # LP
        "DATA/testing/Difetto2/00017.jpg",  # PO
        "DATA/testing/Difetto4/00001.jpg",  # CR
        "DATA/testing/NoDifetto/00002.jpg", # ND
    ]
    
    for img_path in test_images:
        img_path = Path(img_path)
        if not img_path.exists():
            print(f"Skipping {img_path} (not found)")
            continue
        
        print(f"\n{'='*60}")
        print(f"Testing: {img_path.name}")
        print('='*60)
        
        # Get explanation
        result = explainer.explain_prediction(str(img_path))
        
        # Print results
        pred = result['prediction']
        print(f"Prediction: {pred['class_full_name']} ({pred['class_code']})")
        print(f"Confidence: {pred['confidence']*100:.1f}%")
        print(f"Severity: {pred['severity']}")
        print(f"\nLocation: {result['location_description']}")
        print(f"\nDescription: {result['description']}")
        print(f"\nRecommendation: {result['recommendation']}")
        print(f"\nDetected {len(result['regions'])} regions")
        
        # Save visualization panel
        output_path = f"test_explanation_{img_path.stem}.png"
        explainer.create_visualization_panel(str(img_path), output_path)
        print(f"\nVisualization saved to: {output_path}")


if __name__ == "__main__":
    test_explainer()
