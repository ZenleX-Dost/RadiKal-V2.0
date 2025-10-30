"""
Transfer Learning Module for Custom Defect Types.

This module handles fine-tuning YOLOv8 classification models on custom defect types
using transfer learning from pre-trained base models.

**Transfer Learning Strategy**:
1. Start with pre-trained YOLOv8 weights (trained on ImageNet or existing defects)
2. Freeze early layers (feature extraction layers)
3. Fine-tune later layers (classification head) on custom defects
4. Gradually unfreeze layers for full fine-tuning
5. Use data augmentation to prevent overfitting

**Workflow**:
1. Load base model (yolov8s-cls.pt or existing custom model)
2. Prepare dataset with custom defect classes
3. Configure hyperparameters (epochs, learning rate, freeze layers)
4. Train with validation monitoring
5. Save new model version
6. Evaluate performance metrics
"""

import os
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import logging
import json

import torch
from ultralytics import YOLO
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class TransferLearner:
    """
    Transfer learning system for fine-tuning YOLOv8 on custom defect types.
    """
    
    def __init__(
        self,
        base_model_path: str = "yolov8s-cls.pt",
        output_dir: str = "models/custom",
        device: str = "cuda"
    ):
        """
        Initialize transfer learner.
        
        Args:
            base_model_path: Path to base YOLOv8 model (.pt file)
            output_dir: Directory to save trained models
            device: Device for training ('cuda' or 'cpu')
        """
        self.base_model_path = base_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = device if torch.cuda.is_available() else "cpu"
        
        # Training state
        self.model = None
        self.current_epoch = 0
        self.training_metrics = []
        
        # Callbacks for progress monitoring
        self.callbacks = {
            "on_epoch_end": [],
            "on_train_end": [],
            "on_validation_end": []
        }
        
        logger.info(f"Initialized TransferLearner with base model: {base_model_path}")
        logger.info(f"Device: {self.device}")
    
    
    def prepare_dataset(
        self,
        training_samples: List[Dict],
        base_classes: List[str],
        custom_classes: List[str],
        output_path: str,
        train_split: float = 0.7,
        val_split: float = 0.2,
        test_split: float = 0.1,
        augmentation: bool = True
    ) -> Dict[str, any]:
        """
        Prepare dataset in YOLOv8 classification format.
        
        YOLOv8 Classification Format:
        dataset/
            train/
                class1/
                    img1.jpg
                    img2.jpg
                class2/
                    img3.jpg
            val/
                class1/
                class2/
            test/
                class1/
                class2/
        
        Args:
            training_samples: List of training sample dicts
            base_classes: Base defect classes (LP, PO, CR, ND)
            custom_classes: Custom defect classes
            output_path: Path to create dataset directory
            train_split: Training set ratio
            val_split: Validation set ratio
            test_split: Test set ratio
            augmentation: Whether to apply data augmentation
        
        Returns:
            Dataset info dict with paths and statistics
        """
        dataset_path = Path(output_path)
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Combine all classes
        all_classes = base_classes + custom_classes
        
        # Create directory structure
        for split in ['train', 'val', 'test']:
            split_path = dataset_path / split
            split_path.mkdir(exist_ok=True)
            for cls in all_classes:
                (split_path / cls).mkdir(exist_ok=True)
        
        # Split samples into train/val/test
        np.random.shuffle(training_samples)
        n_total = len(training_samples)
        n_train = int(n_total * train_split)
        n_val = int(n_total * val_split)
        
        train_samples = training_samples[:n_train]
        val_samples = training_samples[n_train:n_train + n_val]
        test_samples = training_samples[n_train + n_val:]
        
        # Copy images to appropriate directories
        class_counts = {split: {} for split in ['train', 'val', 'test']}
        
        for split, samples in [('train', train_samples), ('val', val_samples), ('test', test_samples)]:
            for sample in samples:
                # Get class name from annotations
                class_name = sample.get('class_name') or sample['annotations'].get('class')
                
                if class_name not in all_classes:
                    logger.warning(f"Unknown class {class_name}, skipping sample")
                    continue
                
                # Copy image
                src_path = sample['image_path']
                if not os.path.exists(src_path):
                    logger.warning(f"Image not found: {src_path}, skipping")
                    continue
                
                dst_dir = dataset_path / split / class_name
                dst_path = dst_dir / Path(src_path).name
                
                shutil.copy2(src_path, dst_path)
                
                # Track counts
                class_counts[split][class_name] = class_counts[split].get(class_name, 0) + 1
        
        # Create data.yaml for YOLOv8
        data_yaml = {
            'path': str(dataset_path.absolute()),
            'train': 'train',
            'val': 'val',
            'test': 'test',
            'nc': len(all_classes),
            'names': all_classes
        }
        
        yaml_path = dataset_path / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f)
        
        logger.info(f"Dataset prepared at {dataset_path}")
        logger.info(f"Classes: {all_classes}")
        logger.info(f"Train samples: {sum(class_counts['train'].values())}")
        logger.info(f"Val samples: {sum(class_counts['val'].values())}")
        logger.info(f"Test samples: {sum(class_counts['test'].values())}")
        
        return {
            'dataset_path': str(dataset_path),
            'yaml_path': str(yaml_path),
            'classes': all_classes,
            'n_classes': len(all_classes),
            'train_count': sum(class_counts['train'].values()),
            'val_count': sum(class_counts['val'].values()),
            'test_count': sum(class_counts['test'].values()),
            'class_distribution': class_counts
        }
    
    
    def configure_training(
        self,
        epochs: int = 50,
        batch_size: int = 16,
        learning_rate: float = 0.001,
        freeze_layers: int = 10,
        image_size: int = 224,
        patience: int = 10,
        augmentation: bool = True
    ) -> Dict[str, any]:
        """
        Configure training hyperparameters.
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Initial learning rate
            freeze_layers: Number of layers to freeze (transfer learning)
            image_size: Input image size
            patience: Early stopping patience (epochs without improvement)
            augmentation: Enable data augmentation
        
        Returns:
            Configuration dict
        """
        config = {
            'epochs': epochs,
            'batch': batch_size,
            'lr0': learning_rate,
            'lrf': 0.01,  # Final learning rate (lr0 * lrf)
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'warmup_momentum': 0.8,
            'warmup_bias_lr': 0.1,
            'freeze': freeze_layers,
            'imgsz': image_size,
            'patience': patience,
            'save': True,
            'save_period': 5,  # Save checkpoint every N epochs
            'cache': False,  # Don't cache images (memory intensive)
            'device': self.device,
            'workers': 4,
            'project': str(self.output_dir),
            'name': f'train_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'exist_ok': True,
            'pretrained': True,
            'optimizer': 'AdamW',
            'verbose': True,
            'seed': 42,
            'deterministic': True
        }
        
        # Data augmentation settings
        if augmentation:
            config.update({
                'hsv_h': 0.015,  # HSV-Hue augmentation
                'hsv_s': 0.7,    # HSV-Saturation augmentation
                'hsv_v': 0.4,    # HSV-Value augmentation
                'degrees': 10.0,  # Rotation degrees
                'translate': 0.1, # Translation
                'scale': 0.5,     # Scaling
                'shear': 0.0,     # Shear
                'perspective': 0.0, # Perspective
                'flipud': 0.5,    # Vertical flip probability
                'fliplr': 0.5,    # Horizontal flip probability
                'mosaic': 0.0,    # Mosaic augmentation (disable for classification)
                'mixup': 0.0      # Mixup augmentation
            })
        
        return config
    
    
    def train(
        self,
        data_yaml_path: str,
        config: Dict[str, any],
        callbacks: Optional[Dict[str, List[Callable]]] = None
    ) -> Dict[str, any]:
        """
        Train YOLOv8 classification model with transfer learning.
        
        Args:
            data_yaml_path: Path to data.yaml file
            config: Training configuration dict
            callbacks: Optional callbacks for monitoring
        
        Returns:
            Training results dict
        """
        logger.info("Starting transfer learning training...")
        logger.info(f"Base model: {self.base_model_path}")
        logger.info(f"Dataset: {data_yaml_path}")
        logger.info(f"Config: {json.dumps(config, indent=2)}")
        
        # Load base model
        try:
            self.model = YOLO(self.base_model_path)
            logger.info(f"Loaded base model: {self.base_model_path}")
        except Exception as e:
            logger.error(f"Failed to load base model: {e}")
            raise
        
        # Register callbacks
        if callbacks:
            for event, callback_list in callbacks.items():
                for callback in callback_list:
                    self.callbacks[event].append(callback)
        
        # Start training
        try:
            results = self.model.train(
                data=data_yaml_path,
                **config
            )
            
            logger.info("Training completed successfully!")
            
            # Extract metrics
            training_results = {
                'success': True,
                'final_metrics': {
                    'top1_acc': float(results.results_dict.get('metrics/accuracy_top1', 0.0)),
                    'top5_acc': float(results.results_dict.get('metrics/accuracy_top5', 0.0)),
                    'train_loss': float(results.results_dict.get('train/loss', 0.0)),
                    'val_loss': float(results.results_dict.get('val/loss', 0.0))
                },
                'model_path': str(self.model.ckpt_path),
                'best_model_path': str(Path(config['project']) / config['name'] / 'weights' / 'best.pt'),
                'training_time_hours': results.t / 3600 if hasattr(results, 't') else None
            }
            
            # Save training history
            history_path = Path(config['project']) / config['name'] / 'training_history.json'
            with open(history_path, 'w') as f:
                json.dump(training_results, f, indent=2)
            
            return training_results
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    def evaluate(
        self,
        model_path: str,
        data_yaml_path: str,
        split: str = 'test'
    ) -> Dict[str, any]:
        """
        Evaluate trained model on test set.
        
        Args:
            model_path: Path to trained model (.pt file)
            data_yaml_path: Path to data.yaml
            split: Dataset split to evaluate ('val' or 'test')
        
        Returns:
            Evaluation metrics dict
        """
        logger.info(f"Evaluating model: {model_path}")
        
        try:
            model = YOLO(model_path)
            
            # Run validation
            results = model.val(
                data=data_yaml_path,
                split=split,
                batch=16,
                device=self.device
            )
            
            metrics = {
                'top1_accuracy': float(results.results_dict.get('metrics/accuracy_top1', 0.0)),
                'top5_accuracy': float(results.results_dict.get('metrics/accuracy_top5', 0.0)),
                'val_loss': float(results.results_dict.get('val/loss', 0.0)),
                'confusion_matrix': results.confusion_matrix.matrix.tolist() if hasattr(results, 'confusion_matrix') else None
            }
            
            logger.info(f"Evaluation complete. Top-1 Accuracy: {metrics['top1_accuracy']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {'error': str(e)}
    
    
    def export_model(
        self,
        model_path: str,
        export_format: str = 'onnx',
        output_path: Optional[str] = None
    ) -> str:
        """
        Export trained model to different formats.
        
        Args:
            model_path: Path to trained model
            export_format: Export format (onnx, torchscript, tflite, etc.)
            output_path: Optional output path
        
        Returns:
            Path to exported model
        """
        logger.info(f"Exporting model to {export_format} format...")
        
        try:
            model = YOLO(model_path)
            exported_path = model.export(format=export_format)
            
            if output_path:
                shutil.move(exported_path, output_path)
                exported_path = output_path
            
            logger.info(f"Model exported to: {exported_path}")
            return str(exported_path)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise
    
    
    def fine_tune_progressive(
        self,
        data_yaml_path: str,
        initial_config: Dict[str, any],
        stages: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Progressive fine-tuning: gradually unfreeze layers.
        
        **Strategy**:
        1. Stage 1: Train classification head only (freeze all backbone)
        2. Stage 2: Unfreeze last few layers
        3. Stage 3: Full fine-tuning (all layers trainable)
        
        Args:
            data_yaml_path: Path to data.yaml
            initial_config: Initial training config
            stages: List of stage configs with {'freeze': N, 'epochs': M, 'lr': X}
        
        Returns:
            List of results for each stage
        """
        logger.info("Starting progressive fine-tuning...")
        
        all_results = []
        current_model_path = self.base_model_path
        
        for i, stage_config in enumerate(stages):
            logger.info(f"=== Stage {i+1}/{len(stages)} ===")
            logger.info(f"Freeze: {stage_config.get('freeze', 0)} layers")
            logger.info(f"Epochs: {stage_config['epochs']}")
            logger.info(f"Learning Rate: {stage_config.get('lr', initial_config['lr0'])}")
            
            # Update config for this stage
            stage_training_config = initial_config.copy()
            stage_training_config.update(stage_config)
            stage_training_config['name'] = f"stage_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Use previous stage's best model as starting point
            self.base_model_path = current_model_path
            
            # Train this stage
            results = self.train(data_yaml_path, stage_training_config)
            
            if results['success']:
                current_model_path = results['best_model_path']
                logger.info(f"Stage {i+1} completed. Best model: {current_model_path}")
            else:
                logger.error(f"Stage {i+1} failed: {results.get('error')}")
                break
            
            all_results.append(results)
        
        logger.info("Progressive fine-tuning completed!")
        return all_results
    
    
    def predict(
        self,
        model_path: str,
        image_path: str,
        return_features: bool = False
    ) -> Dict[str, any]:
        """
        Make prediction on a single image.
        
        Args:
            model_path: Path to trained model
            image_path: Path to input image
            return_features: Whether to return feature embeddings
        
        Returns:
            Prediction dict with class probabilities
        """
        try:
            model = YOLO(model_path)
            results = model(image_path)
            
            # Extract prediction
            result = results[0]
            probs = result.probs.data.cpu().numpy()
            top1_idx = int(result.probs.top1)
            
            prediction = {
                'predicted_class': top1_idx,
                'class_name': result.names[top1_idx],
                'confidence': float(probs[top1_idx]),
                'probabilities': probs.tolist(),
                'top5_indices': result.probs.top5,
                'top5_confidences': [float(probs[i]) for i in result.probs.top5]
            }
            
            # Extract features if requested (for active learning)
            if return_features:
                # Get feature embeddings from penultimate layer
                # This requires model modification - placeholder for now
                prediction['features'] = None  # TODO: Extract features
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {'error': str(e)}


# ===== Helper Functions =====

def create_transfer_learner(
    base_model: str = "yolov8s-cls.pt",
    output_dir: str = "models/custom",
    device: str = "cuda"
) -> TransferLearner:
    """
    Factory function to create a TransferLearner instance.
    
    Args:
        base_model: Base model path
        output_dir: Output directory for trained models
        device: Training device
    
    Returns:
        Configured TransferLearner instance
    """
    return TransferLearner(
        base_model_path=base_model,
        output_dir=output_dir,
        device=device
    )


def calculate_class_weights(class_counts: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate class weights for imbalanced datasets.
    
    Args:
        class_counts: Dict mapping class names to sample counts
    
    Returns:
        Dict mapping class names to weights
    """
    total_samples = sum(class_counts.values())
    n_classes = len(class_counts)
    
    weights = {}
    for cls, count in class_counts.items():
        # Inverse frequency weighting
        weights[cls] = total_samples / (n_classes * count)
    
    return weights
