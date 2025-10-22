"""Training script with MLflow tracking and RTX 4050 GPU optimization.

This script trains the defect detection model with full experiment tracking,
optimized for NVIDIA RTX 4050 GPU.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import mlflow
import mlflow.pytorch
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from core.models.detector import DefectDetector
from core.preprocessing.image_processor import ImageProcessor
from core.metrics.business_metrics import calculate_confusion_matrix_metrics
from core.metrics.detection_metrics import calculate_map


def collate_fn(batch):
    """Custom collate function for DataLoader.
    
    This is defined at module level to avoid pickling issues on Windows.
    """
    return tuple(zip(*batch))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_gpu(gpu_id: int = 0) -> torch.device:
    """Setup GPU for training on RTX 4050.
    
    Args:
        gpu_id: GPU device ID (default: 0).
        
    Returns:
        Torch device object.
    """
    if not torch.cuda.is_available():
        logger.warning("CUDA not available! Training will run on CPU.")
        return torch.device('cpu')
    
    device = torch.device(f'cuda:{gpu_id}')
    
    logger.info(f"GPU: {torch.cuda.get_device_name(device)}")
    logger.info(f"CUDA Version: {torch.version.cuda}")
    logger.info(f"Available GPU Memory: {torch.cuda.get_device_properties(device).total_memory / 1e9:.2f} GB")
    
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    
    logger.info("RTX 4050 GPU setup complete with optimized settings")
    
    return device


def optimize_for_rtx4050():
    """Apply RTX 4050-specific optimizations."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
        torch.set_float32_matmul_precision('high')
        
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
        
        logger.info("Applied RTX 4050 optimizations")


class DefectDataset(Dataset):
    """Dataset class for defect detection."""
    
    def __init__(
        self,
        image_dir: str,
        annotation_file: str,
        processor: ImageProcessor,
        augment: bool = False
    ):
        """Initialize dataset.
        
        Args:
            image_dir: Directory containing images.
            annotation_file: Path to annotation file.
            processor: Image processor instance.
            augment: Whether to apply data augmentation.
        """
        self.image_dir = Path(image_dir)
        self.processor = processor
        self.augment = augment
        
        self.samples = self._load_annotations(annotation_file)
    
    def _load_annotations(self, annotation_file: str) -> list:
        """Load annotations from COCO format file.
        
        Args:
            annotation_file: Path to COCO annotation file.
            
        Returns:
            List of processed sample dictionaries.
        """
        import json
        from collections import defaultdict
        
        with open(annotation_file, 'r') as f:
            coco_data = json.load(f)
        
        # Create image_id to filename mapping
        images_dict = {img['id']: img['file_name'] for img in coco_data['images']}
        
        # Group annotations by image_id
        annotations_by_image = defaultdict(list)
        for ann in coco_data['annotations']:
            annotations_by_image[ann['image_id']].append(ann)
        
        # Create samples list
        samples = []
        for img_id, anns in annotations_by_image.items():
            boxes = []
            labels = []
            
            for ann in anns:
                # COCO bbox format: [x, y, width, height]
                x, y, w, h = ann['bbox']
                # Convert to [x1, y1, x2, y2]
                boxes.append([x, y, x + w, y + h])
                labels.append(ann['category_id'])
            
            samples.append({
                'image_file': images_dict[img_id],
                'boxes': boxes,
                'labels': labels
            })
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> tuple:
        """Get dataset item.
        
        Args:
            idx: Sample index.
            
        Returns:
            Tuple of (image, target).
        """
        sample = self.samples[idx]
        
        image_path = self.image_dir / sample['image_file']
        image = self.processor.load_image(str(image_path))
        image = self.processor.preprocess(image)
        image_tensor = torch.from_numpy(self.processor.to_tensor(image)).float()
        
        boxes = torch.as_tensor(sample['boxes'], dtype=torch.float32)
        labels = torch.as_tensor(sample['labels'], dtype=torch.int64)
        
        target = {
            'boxes': boxes,
            'labels': labels
        }
        
        return image_tensor, target


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int
) -> Dict[str, float]:
    """Train for one epoch.
    
    Args:
        model: Model to train.
        dataloader: Training dataloader.
        optimizer: Optimizer.
        device: Device to train on.
        epoch: Current epoch number.
        
    Returns:
        Dictionary of training metrics.
    """
    model.train()
    
    total_loss = 0.0
    num_batches = 0
    
    pbar = tqdm(dataloader, desc=f"Epoch {epoch}")
    
    for images, targets in pbar:
        images = [img.to(device) for img in images]
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
        
        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())
        
        optimizer.zero_grad()
        losses.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
        total_loss += losses.item()
        num_batches += 1
        
        pbar.set_postfix({'loss': losses.item()})
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    avg_loss = total_loss / num_batches
    
    return {
        'train_loss': avg_loss
    }


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """Validate model.
    
    Args:
        model: Model to validate.
        dataloader: Validation dataloader.
        device: Device to validate on.
        
    Returns:
        Dictionary of validation metrics.
    """
    model.eval()
    
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for images, targets in tqdm(dataloader, desc="Validating"):
            images = [img.to(device) for img in images]
            
            predictions = model(images)
            
            all_predictions.extend(predictions)
            all_targets.extend(targets)
    
    map_score = calculate_map(all_predictions, all_targets, iou_threshold=0.5)
    
    return {
        'val_mAP@0.5': map_score
    }


def train_model(
    config: Dict[str, Any],
    device: torch.device
) -> None:
    """Main training function with MLflow tracking.
    
    Args:
        config: Training configuration dictionary.
        device: Device to train on.
    """
    mlflow.set_tracking_uri(config['mlflow_tracking_uri'])
    mlflow.set_experiment(config['experiment_name'])
    
    with mlflow.start_run(run_name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_params({
            'num_epochs': config['num_epochs'],
            'batch_size': config['batch_size'],
            'learning_rate': config['learning_rate'],
            'num_classes': config['num_classes'],
            'image_size': config['image_size'],
            'device': str(device),
            'gpu_name': torch.cuda.get_device_name(device) if torch.cuda.is_available() else 'CPU'
        })
        
        logger.info("Initializing model...")
        detector = DefectDetector(
            num_classes=config['num_classes'],
            device=str(device)
        )
        model = detector.model  # Get the actual PyTorch model
        model.to(device)
        
        logger.info("Loading datasets...")
        processor = ImageProcessor(target_size=config['image_size'])
        
        train_dataset = DefectDataset(
            config['train_image_dir'],
            config['train_annotations'],
            processor,
            augment=True
        )
        
        val_dataset = DefectDataset(
            config['val_image_dir'],
            config['val_annotations'],
            processor,
            augment=False
        )
        
        # Use num_workers=0 on Windows to avoid multiprocessing issues
        num_workers = 0 if sys.platform == 'win32' else config.get('num_workers', 4)
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=config['batch_size'],
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True if torch.cuda.is_available() else False,
            collate_fn=collate_fn
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=config['batch_size'],
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True if torch.cuda.is_available() else False,
            collate_fn=collate_fn
        )
        
        logger.info("Setting up optimizer and scheduler...")
        optimizer = optim.AdamW(
            model.parameters(),
            lr=config['learning_rate'],
            weight_decay=config['weight_decay']
        )
        
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='max',
            factor=0.5,
            patience=3
        )
        
        best_map = 0.0
        
        logger.info("Starting training...")
        for epoch in range(1, config['num_epochs'] + 1):
            logger.info(f"Epoch {epoch}/{config['num_epochs']}")
            
            train_metrics = train_epoch(model, train_loader, optimizer, device, epoch)
            
            mlflow.log_metrics(train_metrics, step=epoch)
            logger.info(f"Train Loss: {train_metrics['train_loss']:.4f}")
            
            val_metrics = validate(model, val_loader, device)
            
            mlflow.log_metrics(val_metrics, step=epoch)
            logger.info(f"Validation mAP@0.5: {val_metrics['val_mAP@0.5']:.4f}")
            
            scheduler.step(val_metrics['val_mAP@0.5'])
            
            if val_metrics['val_mAP@0.5'] > best_map:
                best_map = val_metrics['val_mAP@0.5']
                
                checkpoint_path = Path(config['checkpoint_dir']) / 'best_model.pth'
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'best_map': best_map,
                    'config': config
                }, checkpoint_path)
                
                mlflow.log_artifact(str(checkpoint_path))
                logger.info(f"Saved best model with mAP@0.5: {best_map:.4f}")
        
        mlflow.log_metric('best_val_mAP@0.5', best_map)
        
        mlflow.pytorch.log_model(model.model, "model")
        
        logger.info("Training completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train defect detection model on RTX 4050")
    parser.add_argument('--config', type=str, default='configs/train_config.json', help='Path to config file')
    parser.add_argument('--gpu', type=int, default=0, help='GPU device ID')
    args = parser.parse_args()
    
    import json
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    optimize_for_rtx4050()
    
    device = setup_gpu(args.gpu)
    
    train_model(config, device)


if __name__ == "__main__":
    main()
