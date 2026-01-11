"""
SAM2 (Segment Anything Model 2) Wrapper for Weld Defect Segmentation

This module provides integration with SAM2 for pixel-level defect segmentation
in radiographic weld images, working alongside YOLOv8 classification.

Architecture:
    1. YOLOv8 Classifier: Determines defect type (LP, PO, CR, ND)
    2. SAM2 Segmenter: Generates precise pixel mask of defect location
    
Author: RadiKal Team
Date: 2026-01-09
"""

import numpy as np
import torch
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# SAM2 imports
try:
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    SAM2_AVAILABLE = True
except ImportError:
    SAM2_AVAILABLE = False
    logger.warning("[WARN] SAM2 not installed. Install with: pip install segment-anything-2")


class SAM2Segmenter:
    """
    SAM2 wrapper for defect segmentation in radiographic images.
    
    Works in two modes:
    1. Auto-segmentation: Generates all possible masks (for ND images)
    2. Point-prompted: Uses detected defect regions as prompts (for defect images)
    """
    
    # Supported SAM2 model sizes (SAM 2.1)
    MODEL_SIZES = {
        "tiny": "sam2.1_hiera_t.pt",
        "small": "sam2.1_hiera_s.pt", 
        "base": "sam2.1_hiera_base_plus.pt",  # SAM2 v1.1 compatible
        "large": "sam2.1_hiera_l.pt"
    }
    
    # Config files for SAM 2.1
    CONFIG_FILES = {
        "tiny": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "small": "configs/sam2.1/sam2.1_hiera_s.yaml",
        "base": "configs/sam2.1/sam2.1_hiera_b+.yaml",
        "large": "configs/sam2.1/sam2.1_hiera_l.yaml"
    }
    
    def __init__(
        self,
        model_size: str = "small",
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        conf_threshold: float = 0.1,  # Very low to catch all potential defects
        mask_threshold: float = 0.3   # Lower for more permissive mask generation
    ):
        """
        Initialize SAM2 segmenter.
        
        Args:
            model_size: SAM2 model size ('tiny', 'small', 'base', 'large')
            model_path: Custom model checkpoint path (optional)
            device: Device for inference ('cuda', 'cpu', or None for auto)
            conf_threshold: Minimum confidence for keeping masks
            mask_threshold: Threshold for binarizing masks
        """
        if not SAM2_AVAILABLE:
            raise ImportError(
                "SAM2 not installed. Install with:\n"
                "  pip install segment-anything-2\n"
                "Or from GitHub:\n"
                "  pip install git+https://github.com/facebookresearch/segment-anything-2.git"
            )
        
        # Set device - SAM2 uses 'cuda' not '0' or 'cuda:0'
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        elif device in ('0', 'cuda:0', '1', 'cuda:1'):
            # Normalize GPU device strings to 'cuda'
            self.device = 'cuda'
        else:
            self.device = device
        
        self.model_size = model_size
        self.conf_threshold = conf_threshold
        self.mask_threshold = mask_threshold
        
        # Model checkpoint
        if model_path is None:
            # Try multiple possible locations for SAM2 models
            possible_dirs = [
                Path("models/sam2"),  # When running from backend/
                Path("backend/models/sam2"),  # When running from project root
                Path(__file__).parent.parent.parent / "models" / "sam2",  # Relative to this file
            ]
            
            checkpoint_name = self.MODEL_SIZES.get(model_size, "sam2_hiera_small.pt")
            self.model_path = None
            
            for models_dir in possible_dirs:
                potential_path = models_dir / checkpoint_name
                if potential_path.exists():
                    self.model_path = potential_path
                    break
            
            if self.model_path is None:
                # Use first option as default for error message
                self.model_path = possible_dirs[0] / checkpoint_name
                logger.warning(
                    f"SAM2 checkpoint not found at {self.model_path}\n"
                    f"Download from: https://github.com/facebookresearch/segment-anything-2/tree/main/checkpoints"
                )
        else:
            self.model_path = Path(model_path)
        
        # Load model
        logger.info(f"Loading SAM2 ({model_size}) from: {self.model_path}")
        try:
            # Get config file
            config_file = self.CONFIG_FILES.get(model_size, "configs/sam2.1/sam2.1_hiera_s.yaml")
            
            # Build SAM2 model
            self.sam2_model = build_sam2(
                config_file=config_file,
                ckpt_path=str(self.model_path),
                device=self.device
            )
            
            # Create predictor
            self.predictor = SAM2ImagePredictor(self.sam2_model)
            
            logger.info(f"[OK] SAM2 loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load SAM2: {e}")
            raise
    
    def set_image(self, image: Union[np.ndarray, Image.Image, str]) -> None:
        """
        Preprocess and set image for segmentation.
        
        Args:
            image: Input image (numpy array, PIL Image, or path)
        """
        # Convert to numpy array
        if isinstance(image, str):
            image = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            image = np.array(image.convert('RGB'))
        
        # Ensure RGB format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        
        # Log image properties for debugging
        logger.info(f"SAM2 input image: shape={image.shape}, dtype={image.dtype}, range=[{image.min()}, {image.max()}]")
        
        # Apply CLAHE contrast enhancement for radiographic images
        # This helps SAM2 detect subtle defects in low-contrast radiographs
        if self._is_low_contrast(image):
            logger.info("Detected low contrast image, applying CLAHE enhancement")
            image = self._enhance_contrast(image)
            logger.info(f"Enhanced image range: [{image.min()}, {image.max()}]")
        
        self.current_image = image
        self.predictor.set_image(image)
    
    def _is_low_contrast(self, image: np.ndarray, threshold: float = 50.0) -> bool:
        """Check if image has low contrast (typical for radiographic images)."""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        contrast = gray.std()
        logger.debug(f"Image contrast (std): {contrast:.2f}")
        return contrast < threshold
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE contrast enhancement."""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to RGB
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return enhanced
    
    def segment_auto(
        self,
        points_per_side: int = 32,  # Balance between coverage and speed
        pred_iou_thresh: float = 0.3,  # Very low to catch subtle defects
        stability_score_thresh: float = 0.5,  # Lower for radiographic images
        crop_n_layers: int = 1,  # Single layer for speed
        crop_n_points_downscale_factor: int = 2,  # Downscale for speed
        min_mask_region_area: int = 20  # Very small to catch tiny defects
    ) -> List[Dict[str, Any]]:
        """
        Automatic mask generation (no prompts).
        
        Use this for exploratory segmentation or when defect location is unknown.
        Optimized for radiographic weld defect detection.
        
        Args:
            points_per_side: Number of points per side for grid sampling
            pred_iou_thresh: Minimum IoU threshold for mask filtering
            stability_score_thresh: Minimum stability score
            crop_n_layers: Number of crop layers for multi-scale
            crop_n_points_downscale_factor: Downscale factor for crop points
            min_mask_region_area: Minimum mask area in pixels
        
        Returns:
            List of mask dictionaries containing:
                - segmentation: Binary mask (H, W)
                - area: Mask area in pixels
                - bbox: Bounding box [x, y, w, h]
                - predicted_iou: Predicted IoU score
                - stability_score: Stability score
                - point_coords: Generated point coordinates
        """
        # Use automatic mask generator
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
        
        mask_generator = SAM2AutomaticMaskGenerator(
            model=self.sam2_model,
            points_per_side=points_per_side,
            pred_iou_thresh=pred_iou_thresh,
            stability_score_thresh=stability_score_thresh,
            crop_n_layers=crop_n_layers,
            crop_n_points_downscale_factor=crop_n_points_downscale_factor,
            min_mask_region_area=min_mask_region_area
        )
        
        logger.info(f"Running SAM2 auto-segmentation with: points_per_side={points_per_side}, "
                   f"pred_iou_thresh={pred_iou_thresh}, stability_score_thresh={stability_score_thresh}")
        
        masks = mask_generator.generate(self.current_image)
        
        logger.info(f"SAM2 raw output: {len(masks)} masks")
        if masks:
            # Log top 5 mask scores
            for i, m in enumerate(masks[:5]):
                logger.debug(f"  Mask {i}: area={m['area']}, iou={m['predicted_iou']:.3f}, stability={m['stability_score']:.3f}")
        
        # Filter masks by area (remove very large masks that cover most of the image)
        image_area = self.current_image.shape[0] * self.current_image.shape[1]
        max_area_ratio = 0.5  # Defects shouldn't cover more than 50% of image
        masks = [m for m in masks if m['area'] < image_area * max_area_ratio]
        
        logger.info(f"Auto-segmentation: {len(masks)} masks after area filtering")
        
        # FALLBACK: If no masks found, try intensity-based prompting
        if len(masks) == 0:
            logger.warning("No masks from auto-segmentation, trying intensity-based defect detection...")
            fallback_masks = self._intensity_based_segmentation()
            if fallback_masks:
                logger.info(f"Fallback found {len(fallback_masks)} potential defect regions")
                return fallback_masks
        
        return masks
    
    def _intensity_based_segmentation(self) -> List[Dict[str, Any]]:
        """
        Fallback method: Find potential defects using intensity anomalies.
        Radiographic defects often appear as dark spots (porosity, inclusions) 
        or bright spots (lack of fusion, cracks) in the image.
        """
        if self.current_image is None:
            return []
        
        gray = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape
        
        # Apply bilateral filter to reduce noise while preserving edges
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive thresholding to find dark and bright anomalies
        # Dark spots (porosity, inclusions)
        dark_thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 21, 10
        )
        
        # Bright spots (lack of fusion)
        bright_thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dark_clean = cv2.morphologyEx(dark_thresh, cv2.MORPH_OPEN, kernel)
        bright_clean = cv2.morphologyEx(bright_thresh, cv2.MORPH_OPEN, kernel)
        
        # Find contours in both
        all_masks = []
        
        for thresh_img, defect_type in [(dark_clean, 'dark'), (bright_clean, 'bright')]:
            contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter by area (defects typically 20-10000 pixels)
                if 20 < area < (h * w * 0.3):
                    # Get centroid as prompt point
                    M = cv2.moments(contour)
                    if M['m00'] > 0:
                        cx = int(M['m10'] / M['m00'])
                        cy = int(M['m01'] / M['m00'])
                        
                        # Use point to get SAM2 mask
                        try:
                            masks, scores, _ = self.predictor.predict(
                                point_coords=np.array([[cx, cy]]),
                                point_labels=np.array([1]),
                                multimask_output=True
                            )
                            
                            # Take the best mask
                            if len(masks) > 0:
                                best_idx = np.argmax(scores)
                                mask = masks[best_idx]
                                bbox = self._get_bbox(mask)
                                
                                all_masks.append({
                                    'segmentation': mask.astype(bool),
                                    'area': int(np.sum(mask)),
                                    'bbox': bbox,
                                    'predicted_iou': float(scores[best_idx]),
                                    'stability_score': float(scores[best_idx]),
                                    'point_coords': [[cx, cy]],
                                    'defect_type_hint': defect_type
                                })
                        except Exception as e:
                            logger.debug(f"Point prompt failed for {defect_type} region at ({cx}, {cy}): {e}")
        
        # Remove duplicates (overlapping masks)
        all_masks = self._remove_duplicate_masks(all_masks)
        
        return all_masks
    
    def _remove_duplicate_masks(self, masks: List[Dict[str, Any]], iou_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Remove overlapping masks, keeping higher scoring ones."""
        if len(masks) <= 1:
            return masks
        
        # Sort by score descending
        masks = sorted(masks, key=lambda x: x['predicted_iou'], reverse=True)
        
        keep = []
        for mask in masks:
            is_duplicate = False
            for kept in keep:
                # Calculate IoU
                mask_arr = np.array(mask['segmentation'])
                kept_arr = np.array(kept['segmentation'])
                intersection = np.logical_and(mask_arr, kept_arr).sum()
                union = np.logical_or(mask_arr, kept_arr).sum()
                iou = intersection / union if union > 0 else 0
                
                if iou > iou_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                keep.append(mask)
        
        return keep
    
    def segment_with_points(
        self,
        point_coords: np.ndarray,
        point_labels: np.ndarray,
        multimask_output: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Segment with point prompts.
        
        Use this when you have rough defect locations (e.g., from YOLOv8 detection).
        
        Args:
            point_coords: Point coordinates [[x1, y1], [x2, y2], ...] (N, 2)
            point_labels: Point labels [1, 1, ...] (1=foreground, 0=background) (N,)
            multimask_output: Whether to output multiple masks
        
        Returns:
            Tuple of:
                - masks: Predicted masks (M, H, W) where M is number of masks
                - scores: IoU prediction scores (M,)
                - logits: Low-resolution mask logits (M, 256, 256)
        """
        masks, scores, logits = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=multimask_output
        )
        
        return masks, scores, logits
    
    def segment_with_box(
        self,
        box: np.ndarray,
        multimask_output: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Segment with bounding box prompt.
        
        Args:
            box: Bounding box [x1, y1, x2, y2] in xyxy format
            multimask_output: Whether to output multiple masks
        
        Returns:
            Tuple of (masks, scores, logits)
        """
        masks, scores, logits = self.predictor.predict(
            box=box,
            multimask_output=multimask_output
        )
        
        return masks, scores, logits
    
    def segment_defect(
        self,
        image: Union[np.ndarray, Image.Image, str],
        prompt_points: Optional[np.ndarray] = None,
        prompt_boxes: Optional[np.ndarray] = None,
        auto_segment: bool = False
    ) -> Dict[str, Any]:
        """
        High-level defect segmentation API.
        
        Args:
            image: Input radiographic image
            prompt_points: Optional point prompts [[x, y], ...]
            prompt_boxes: Optional box prompts [[x1, y1, x2, y2], ...]
            auto_segment: If True and no prompts given, do automatic segmentation
        
        Returns:
            Dictionary containing:
                - masks: List of binary masks
                - scores: Confidence scores for each mask
                - num_segments: Number of detected segments
                - primary_mask: Best mask (highest score)
                - combined_mask: Union of all masks
                - bbox: Bounding box of primary mask
                - area: Area of primary mask (pixels)
                - centroid: Centroid (x, y) of primary mask
        """
        # Set image
        self.set_image(image)
        
        image_area = self.current_image.shape[0] * self.current_image.shape[1]
        
        # Determine segmentation mode
        if prompt_points is not None:
            # Point-prompted segmentation
            point_labels = np.ones(len(prompt_points), dtype=np.int32)
            masks, scores, _ = self.segment_with_points(
                point_coords=prompt_points,
                point_labels=point_labels,
                multimask_output=True
            )
            
            # For point prompting, prefer smaller masks (defects are typically small)
            # SAM2 returns 3 masks: small, medium, large - we want the smallest reasonable one
            if len(masks) > 0:
                mask_areas = [np.sum(m) for m in masks]
                logger.info(f"Point-prompted masks: areas={mask_areas}, scores={scores.tolist()}")
                
                # Filter out masks that cover too much of the image (>30% is likely the whole object)
                valid_masks = []
                valid_scores = []
                for i, (mask, score) in enumerate(zip(masks, scores)):
                    area = np.sum(mask)
                    coverage = area / image_area
                    if coverage < 0.3:  # Defects shouldn't cover more than 30% of image
                        valid_masks.append(mask)
                        valid_scores.append(score)
                        logger.info(f"  Mask {i}: area={area}, coverage={coverage:.1%}, score={score:.3f} - KEPT")
                    else:
                        logger.info(f"  Mask {i}: area={area}, coverage={coverage:.1%}, score={score:.3f} - FILTERED (too large)")
                
                if valid_masks:
                    masks = np.array(valid_masks)
                    scores = np.array(valid_scores)
                else:
                    # If all masks are too large, use the smallest one anyway
                    smallest_idx = np.argmin(mask_areas)
                    masks = masks[smallest_idx:smallest_idx+1]
                    scores = scores[smallest_idx:smallest_idx+1]
                    logger.warning(f"All masks too large, using smallest: area={mask_areas[smallest_idx]}")
            
        elif prompt_boxes is not None:
            # Box-prompted segmentation (single box for now)
            masks, scores, _ = self.segment_with_box(
                box=prompt_boxes[0],
                multimask_output=True
            )
            
        elif auto_segment:
            # Automatic segmentation
            auto_masks = self.segment_auto()
            
            if not auto_masks:
                return {
                    'masks': [],
                    'scores': [],
                    'num_segments': 0,
                    'primary_mask': None,
                    'combined_mask': None
                }
            
            # Convert to standard format
            masks = np.array([m['segmentation'] for m in auto_masks])
            scores = np.array([m['predicted_iou'] for m in auto_masks])
            
        else:
            raise ValueError("Must provide prompt_points, prompt_boxes, or set auto_segment=True")
        
        # Filter by confidence
        logger.info(f"SAM2 raw masks: {len(masks)}, scores: {scores.tolist() if len(scores) > 0 else []}")
        logger.info(f"Filtering with conf_threshold={self.conf_threshold}")
        
        valid_idx = scores >= self.conf_threshold
        masks = masks[valid_idx]
        scores = scores[valid_idx]
        
        logger.info(f"After filtering: {len(masks)} masks remaining")
        
        if len(masks) == 0:
            logger.warning(f"No masks passed confidence threshold ({self.conf_threshold}). Consider lowering threshold.")
            return {
                'masks': [],
                'scores': [],
                'num_segments': 0,
                'primary_mask': None,
                'combined_mask': None
            }
        
        # Get primary mask (highest score)
        primary_idx = np.argmax(scores)
        primary_mask = masks[primary_idx]
        
        # Combined mask (union of all)
        combined_mask = np.any(masks, axis=0).astype(np.uint8)
        
        # Calculate properties
        bbox = self._get_bbox(primary_mask)
        area = int(np.sum(primary_mask))
        centroid = self._get_centroid(primary_mask)
        
        return {
            'masks': masks.tolist(),
            'scores': scores.tolist(),
            'num_segments': len(masks),
            'primary_mask': primary_mask.astype(np.uint8).tolist(),
            'combined_mask': combined_mask.tolist(),
            'bbox': bbox,
            'area': area,
            'centroid': centroid
        }
    
    def _get_bbox(self, mask: np.ndarray) -> List[int]:
        """Get bounding box [x, y, w, h] from binary mask."""
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        
        if not rows.any() or not cols.any():
            return [0, 0, 0, 0]
        
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        
        return [int(cmin), int(rmin), int(cmax - cmin), int(rmax - rmin)]
    
    def _get_centroid(self, mask: np.ndarray) -> List[float]:
        """Get centroid (x, y) from binary mask."""
        moments = cv2.moments(mask.astype(np.uint8))
        
        if moments['m00'] == 0:
            return [0.0, 0.0]
        
        cx = moments['m10'] / moments['m00']
        cy = moments['m01'] / moments['m00']
        
        return [float(cx), float(cy)]
    
    def visualize_masks(
        self,
        masks: np.ndarray,
        scores: Optional[np.ndarray] = None,
        alpha: float = 0.5,
        show_borders: bool = True
    ) -> np.ndarray:
        """
        Create visualization overlay of masks on original image.
        
        Args:
            masks: Binary masks (M, H, W)
            scores: Optional confidence scores (M,)
            alpha: Transparency of masks
            show_borders: Whether to draw mask borders
        
        Returns:
            RGB image with mask overlays
        """
        overlay = self.current_image.copy()
        
        # Generate distinct colors
        colors = self._generate_colors(len(masks))
        
        for i, mask in enumerate(masks):
            # Apply color overlay
            color = colors[i]
            mask_3ch = np.stack([mask] * 3, axis=-1)
            colored_mask = mask_3ch * color
            
            # Blend with original
            overlay = np.where(
                mask_3ch,
                overlay * (1 - alpha) + colored_mask * alpha,
                overlay
            ).astype(np.uint8)
            
            # Draw borders
            if show_borders:
                contours, _ = cv2.findContours(
                    mask.astype(np.uint8),
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(overlay, contours, -1, color.tolist(), 2)
            
            # Add score text if available
            if scores is not None:
                centroid = self._get_centroid(mask)
                cv2.putText(
                    overlay,
                    f"{scores[i]:.2f}",
                    (int(centroid[0]), int(centroid[1])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )
        
        return overlay
    
    def _generate_colors(self, n: int) -> List[np.ndarray]:
        """Generate N distinct colors."""
        colors = []
        for i in range(n):
            hue = i * (360 / n)
            # HSV to RGB
            h = hue / 60
            x = 255 * (1 - abs((h % 2) - 1))
            
            if h < 1:
                rgb = [255, x, 0]
            elif h < 2:
                rgb = [x, 255, 0]
            elif h < 3:
                rgb = [0, 255, x]
            elif h < 4:
                rgb = [0, x, 255]
            elif h < 5:
                rgb = [x, 0, 255]
            else:
                rgb = [255, 0, x]
            
            colors.append(np.array(rgb, dtype=np.uint8))
        
        return colors
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_type': 'SAM2',
            'model_size': self.model_size,
            'device': self.device,
            'conf_threshold': self.conf_threshold,
            'mask_threshold': self.mask_threshold,
            'model_path': str(self.model_path)
        }
