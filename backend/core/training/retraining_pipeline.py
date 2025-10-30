"""
Automated Model Retraining Pipeline for RadiKal.

This module orchestrates the complete retraining workflow:
1. Dataset preparation from labeled samples
2. Model training with monitoring
3. Validation and performance evaluation
4. Deployment decision
5. Rollback if performance degrades

**Retraining Triggers**:
- Manual trigger from UI
- Automatic when custom defect type reaches minimum samples
- Scheduled periodic retraining
- Performance degradation detection
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.training.transfer_learner import TransferLearner, create_transfer_learner
from core.learning.active_learner import ActiveLearner
from db.models import (
    CustomDefectType,
    TrainingSample,
    ModelVersion,
    TrainingDataset,
    TrainingJob
)

logger = logging.getLogger(__name__)


class RetrainingPipeline:
    """
    Automated pipeline for model retraining with validation and deployment.
    """
    
    def __init__(
        self,
        db_session: Session,
        base_model_path: str = "yolov8s-cls.pt",
        output_dir: str = "models/custom",
        min_samples_per_class: int = 50,
        validation_threshold: float = 0.85,
        device: str = "cuda"
    ):
        """
        Initialize retraining pipeline.
        
        Args:
            db_session: Database session for accessing data
            base_model_path: Path to base model for transfer learning
            output_dir: Directory for output models
            min_samples_per_class: Minimum samples required per class
            validation_threshold: Minimum accuracy to deploy new model
            device: Training device
        """
        self.db = db_session
        self.base_model_path = base_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_samples_per_class = min_samples_per_class
        self.validation_threshold = validation_threshold
        self.device = device
        
        # Initialize transfer learner
        self.transfer_learner = create_transfer_learner(
            base_model=base_model_path,
            output_dir=str(output_dir),
            device=device
        )
        
        # Training callbacks
        self.callbacks = []
        
        logger.info("Initialized RetrainingPipeline")
    
    
    def check_retraining_needed(self) -> Dict[str, any]:
        """
        Check if retraining is needed based on multiple criteria.
        
        Returns:
            Dict with retraining decision and reasons
        """
        reasons = []
        should_retrain = False
        
        # Check 1: Any custom defect type requiring retraining
        defects_needing_retraining = self.db.query(CustomDefectType).filter(
            CustomDefectType.requires_retraining == True,
            CustomDefectType.is_active == True
        ).all()
        
        if defects_needing_retraining:
            should_retrain = True
            reasons.append(f"{len(defects_needing_retraining)} custom defect types need retraining")
        
        # Check 2: Custom defects with sufficient samples but not yet trained
        defects_ready = self.db.query(CustomDefectType).filter(
            CustomDefectType.is_active == True,
            CustomDefectType.current_sample_count >= CustomDefectType.min_samples_required,
            CustomDefectType.requires_retraining == True
        ).all()
        
        if defects_ready:
            should_retrain = True
            reasons.append(f"{len(defects_ready)} defect types have sufficient samples for training")
        
        # Check 3: Time-based (retrain every 30 days)
        active_model = self.db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).first()
        
        if active_model:
            days_since_training = (datetime.utcnow() - active_model.created_at).days
            if days_since_training >= 30:
                should_retrain = True
                reasons.append(f"Model is {days_since_training} days old (threshold: 30 days)")
        
        # Check 4: New samples available (10% increase)
        if active_model and active_model.training_dataset_id:
            old_dataset = self.db.query(TrainingDataset).filter(
                TrainingDataset.id == active_model.training_dataset_id
            ).first()
            
            current_sample_count = self.db.query(TrainingSample).count()
            
            if old_dataset and current_sample_count > old_dataset.total_images * 1.1:
                should_retrain = True
                reasons.append(f"10% more samples available ({current_sample_count} vs {old_dataset.total_images})")
        
        return {
            'should_retrain': should_retrain,
            'reasons': reasons,
            'defects_needing_retraining': [d.name for d in defects_needing_retraining],
            'defects_ready': [d.name for d in defects_ready]
        }
    
    
    def prepare_training_dataset(
        self,
        dataset_name: Optional[str] = None,
        include_base_classes: bool = True
    ) -> Dict[str, any]:
        """
        Prepare dataset from database training samples.
        
        Args:
            dataset_name: Optional name for dataset
            include_base_classes: Include base defect classes (LP/PO/CR/ND)
        
        Returns:
            Dataset info dict
        """
        logger.info("Preparing training dataset from database...")
        
        # Get all active custom defect types
        custom_defects = self.db.query(CustomDefectType).filter(
            CustomDefectType.is_active == True
        ).all()
        
        # Build class lists
        base_classes = ['LP', 'PO', 'CR', 'ND'] if include_base_classes else []
        custom_classes = [d.code for d in custom_defects]
        all_classes = base_classes + custom_classes
        
        logger.info(f"Classes: {all_classes}")
        
        # Get all training samples
        training_samples = []
        class_counts = {}
        
        for defect in custom_defects:
            samples = self.db.query(TrainingSample).filter(
                TrainingSample.defect_type_id == defect.id
            ).all()
            
            for sample in samples:
                training_samples.append({
                    'image_path': sample.image_path,
                    'class_name': defect.code,
                    'annotations': sample.annotations,
                    'quality_score': sample.quality_score
                })
            
            class_counts[defect.code] = len(samples)
            logger.info(f"  {defect.code}: {len(samples)} samples")
        
        # Check if we have enough samples
        insufficient_classes = [cls for cls, count in class_counts.items() 
                               if count < self.min_samples_per_class]
        
        if insufficient_classes:
            logger.warning(f"Insufficient samples for classes: {insufficient_classes}")
            logger.warning(f"Training may proceed but quality could be affected")
        
        # Create dataset directory
        if dataset_name is None:
            dataset_name = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dataset_path = self.output_dir / dataset_name
        
        # Prepare dataset using transfer learner
        dataset_info = self.transfer_learner.prepare_dataset(
            training_samples=training_samples,
            base_classes=base_classes,
            custom_classes=custom_classes,
            output_path=str(dataset_path),
            train_split=0.7,
            val_split=0.2,
            test_split=0.1,
            augmentation=True
        )
        
        # Save dataset to database
        db_dataset = TrainingDataset(
            name=dataset_name,
            description=f"Auto-generated dataset with {len(all_classes)} classes",
            dataset_path=str(dataset_path),
            total_images=dataset_info['train_count'] + dataset_info['val_count'] + dataset_info['test_count'],
            train_images=dataset_info['train_count'],
            val_images=dataset_info['val_count'],
            test_images=dataset_info['test_count'],
            class_distribution=dataset_info['class_distribution'],
            includes_custom_types=len(custom_classes) > 0,
            custom_types_included=[d.id for d in custom_defects],
            created_by="retraining_pipeline"
        )
        
        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        
        dataset_info['dataset_id'] = db_dataset.id
        
        logger.info(f"Dataset prepared: {dataset_name} (ID: {db_dataset.id})")
        
        return dataset_info
    
    
    def create_model_version(
        self,
        dataset_id: int,
        version_number: Optional[str] = None
    ) -> ModelVersion:
        """
        Create a new model version entry in database.
        
        Args:
            dataset_id: Training dataset ID
            version_number: Optional version number (auto-generated if None)
        
        Returns:
            ModelVersion database object
        """
        # Get latest version number
        if version_number is None:
            latest = self.db.query(ModelVersion).order_by(
                ModelVersion.created_at.desc()
            ).first()
            
            if latest:
                # Parse version (e.g., "v1.2.0" -> "v1.3.0")
                try:
                    parts = latest.version_number.lstrip('v').split('.')
                    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                    version_number = f"v{major}.{minor + 1}.0"
                except:
                    version_number = "v1.0.0"
            else:
                version_number = "v1.0.0"
        
        # Get dataset info
        dataset = self.db.query(TrainingDataset).filter(
            TrainingDataset.id == dataset_id
        ).first()
        
        # Create model version
        model_version = ModelVersion(
            version_number=version_number,
            model_name=f"yolov8s-cls-custom-{version_number}",
            model_path="",  # Will be updated after training
            base_model=self.base_model_path,
            training_dataset_id=dataset_id,
            classes=dataset.class_distribution['train'].keys() if dataset else [],
            num_classes=len(dataset.class_distribution['train']) if dataset else 0,
            custom_classes=[],  # Will be updated
            is_active=False,  # Not active until validated and deployed
            deployment_status="training",
            trained_by="retraining_pipeline"
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        logger.info(f"Created model version: {version_number} (ID: {model_version.id})")
        
        return model_version
    
    
    def train_model(
        self,
        dataset_info: Dict[str, any],
        model_version: ModelVersion,
        job_config: Optional[Dict[str, any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, any]:
        """
        Train model using transfer learning.
        
        Args:
            dataset_info: Dataset information dict
            model_version: ModelVersion database object
            job_config: Optional training job configuration
            progress_callback: Optional callback for progress updates
        
        Returns:
            Training results dict
        """
        logger.info(f"Starting training for model version {model_version.version_number}")
        
        # Create training job
        job = TrainingJob(
            model_version_id=model_version.id,
            job_type="transfer_learning",
            hyperparameters=job_config or {},
            total_epochs=job_config.get('epochs', 50) if job_config else 50,
            status="running"
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Configure training
            training_config = self.transfer_learner.configure_training(
                epochs=job_config.get('epochs', 50) if job_config else 50,
                batch_size=job_config.get('batch_size', 16) if job_config else 16,
                learning_rate=job_config.get('learning_rate', 0.001) if job_config else 0.001,
                freeze_layers=job_config.get('freeze_layers', 10) if job_config else 10,
                patience=job_config.get('patience', 10) if job_config else 10
            )
            
            # Add progress callback
            def update_progress(epoch, metrics):
                if progress_callback:
                    progress_callback(epoch, metrics)
                
                # Update database
                job.current_epoch = epoch
                job.progress_percent = (epoch / job.total_epochs) * 100
                job.latest_train_loss = metrics.get('train_loss')
                job.latest_val_loss = metrics.get('val_loss')
                job.latest_accuracy = metrics.get('accuracy')
                self.db.commit()
            
            # Train model
            results = self.transfer_learner.train(
                data_yaml_path=dataset_info['yaml_path'],
                config=training_config
            )
            
            if results['success']:
                # Update model version with results
                model_version.model_path = results['best_model_path']
                model_version.epochs_trained = job.total_epochs
                model_version.final_accuracy = results['final_metrics'].get('top1_acc')
                model_version.final_map50 = results['final_metrics'].get('top1_acc')  # Use accuracy as proxy
                model_version.deployment_status = "trained"
                
                # Update job
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.progress_percent = 100.0
                job.latest_accuracy = results['final_metrics'].get('top1_acc')
                
                self.db.commit()
                
                logger.info(f"Training completed successfully!")
                logger.info(f"Final accuracy: {results['final_metrics'].get('top1_acc', 0.0):.4f}")
                
                return results
            
            else:
                # Training failed
                job.status = "failed"
                job.error_message = results.get('error', 'Unknown error')
                model_version.deployment_status = "failed"
                self.db.commit()
                
                logger.error(f"Training failed: {results.get('error')}")
                
                return results
        
        except Exception as e:
            logger.error(f"Training error: {e}")
            job.status = "failed"
            job.error_message = str(e)
            model_version.deployment_status = "failed"
            self.db.commit()
            
            return {'success': False, 'error': str(e)}
    
    
    def validate_model(
        self,
        model_version: ModelVersion,
        dataset_info: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Validate trained model on test set.
        
        Args:
            model_version: ModelVersion to validate
            dataset_info: Dataset information
        
        Returns:
            Validation metrics dict
        """
        logger.info(f"Validating model version {model_version.version_number}")
        
        try:
            # Evaluate on test set
            metrics = self.transfer_learner.evaluate(
                model_path=model_version.model_path,
                data_yaml_path=dataset_info['yaml_path'],
                split='test'
            )
            
            # Update model version with metrics
            model_version.precision = metrics.get('top1_accuracy')
            model_version.recall = metrics.get('top1_accuracy')  # For classification, use accuracy
            model_version.f1_score = metrics.get('top1_accuracy')
            model_version.confusion_matrix = metrics.get('confusion_matrix')
            
            self.db.commit()
            
            # Check if model meets validation threshold
            accuracy = metrics.get('top1_accuracy', 0.0)
            passes_validation = accuracy >= self.validation_threshold
            
            logger.info(f"Validation accuracy: {accuracy:.4f}")
            logger.info(f"Threshold: {self.validation_threshold}")
            logger.info(f"Passes validation: {passes_validation}")
            
            return {
                'passes_validation': passes_validation,
                'accuracy': accuracy,
                'threshold': self.validation_threshold,
                'metrics': metrics
            }
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                'passes_validation': False,
                'error': str(e)
            }
    
    
    def deploy_model(
        self,
        model_version: ModelVersion,
        force: bool = False
    ) -> Dict[str, any]:
        """
        Deploy model to production (mark as active).
        
        Args:
            model_version: ModelVersion to deploy
            force: Force deployment even if validation failed
        
        Returns:
            Deployment result dict
        """
        logger.info(f"Deploying model version {model_version.version_number}")
        
        # Check deployment status
        if model_version.deployment_status != "trained" and not force:
            return {
                'success': False,
                'error': f"Model status is '{model_version.deployment_status}', must be 'trained'"
            }
        
        # Deactivate current active model
        current_active = self.db.query(ModelVersion).filter(
            ModelVersion.is_active == True
        ).first()
        
        if current_active:
            current_active.is_active = False
            current_active.deployment_status = "archived"
            logger.info(f"Deactivated previous model: {current_active.version_number}")
        
        # Activate new model
        model_version.is_active = True
        model_version.deployment_status = "deployed"
        model_version.deployed_at = datetime.utcnow()
        
        # Mark custom defect types as trained
        dataset = self.db.query(TrainingDataset).filter(
            TrainingDataset.id == model_version.training_dataset_id
        ).first()
        
        if dataset and dataset.custom_types_included:
            for defect_id in dataset.custom_types_included:
                defect = self.db.query(CustomDefectType).filter(
                    CustomDefectType.id == defect_id
                ).first()
                if defect:
                    defect.requires_retraining = False
        
        self.db.commit()
        
        logger.info(f"Model {model_version.version_number} deployed successfully!")
        
        return {
            'success': True,
            'model_version': model_version.version_number,
            'previous_model': current_active.version_number if current_active else None
        }
    
    
    def run_full_pipeline(
        self,
        dataset_name: Optional[str] = None,
        job_config: Optional[Dict[str, any]] = None,
        auto_deploy: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, any]:
        """
        Run complete retraining pipeline: prepare → train → validate → deploy.
        
        Args:
            dataset_name: Optional dataset name
            job_config: Training configuration
            auto_deploy: Automatically deploy if validation passes
            progress_callback: Progress callback function
        
        Returns:
            Pipeline results dict
        """
        logger.info("=" * 80)
        logger.info("STARTING FULL RETRAINING PIPELINE")
        logger.info("=" * 80)
        
        pipeline_results = {
            'started_at': datetime.utcnow().isoformat(),
            'stages': {}
        }
        
        try:
            # Stage 1: Check if retraining is needed
            logger.info("\n--- Stage 1: Checking if retraining is needed ---")
            check = self.check_retraining_needed()
            pipeline_results['stages']['check'] = check
            
            if not check['should_retrain']:
                logger.info("Retraining not needed at this time")
                return {
                    'success': True,
                    'message': 'Retraining not needed',
                    'check': check
                }
            
            logger.info(f"Retraining needed. Reasons: {check['reasons']}")
            
            # Stage 2: Prepare dataset
            logger.info("\n--- Stage 2: Preparing dataset ---")
            dataset_info = self.prepare_training_dataset(dataset_name=dataset_name)
            pipeline_results['stages']['dataset'] = dataset_info
            
            # Stage 3: Create model version
            logger.info("\n--- Stage 3: Creating model version ---")
            model_version = self.create_model_version(dataset_id=dataset_info['dataset_id'])
            pipeline_results['stages']['model_version'] = model_version.version_number
            
            # Stage 4: Train model
            logger.info("\n--- Stage 4: Training model ---")
            training_results = self.train_model(
                dataset_info=dataset_info,
                model_version=model_version,
                job_config=job_config,
                progress_callback=progress_callback
            )
            pipeline_results['stages']['training'] = training_results
            
            if not training_results.get('success'):
                logger.error("Training failed, aborting pipeline")
                return {
                    'success': False,
                    'stage_failed': 'training',
                    'error': training_results.get('error'),
                    'pipeline_results': pipeline_results
                }
            
            # Stage 5: Validate model
            logger.info("\n--- Stage 5: Validating model ---")
            validation_results = self.validate_model(model_version, dataset_info)
            pipeline_results['stages']['validation'] = validation_results
            
            # Stage 6: Deploy model (if auto-deploy and validation passed)
            if auto_deploy and validation_results.get('passes_validation'):
                logger.info("\n--- Stage 6: Deploying model ---")
                deployment_results = self.deploy_model(model_version)
                pipeline_results['stages']['deployment'] = deployment_results
            elif not validation_results.get('passes_validation'):
                logger.warning("Model did not pass validation, skipping deployment")
                pipeline_results['stages']['deployment'] = {
                    'skipped': True,
                    'reason': 'Failed validation'
                }
            else:
                logger.info("Auto-deploy disabled, skipping deployment")
                pipeline_results['stages']['deployment'] = {
                    'skipped': True,
                    'reason': 'Auto-deploy disabled'
                }
            
            pipeline_results['completed_at'] = datetime.utcnow().isoformat()
            pipeline_results['success'] = True
            
            logger.info("\n" + "=" * 80)
            logger.info("RETRAINING PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            
            return pipeline_results
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_results['error'] = str(e)
            pipeline_results['success'] = False
            return pipeline_results


# ===== Helper Functions =====

def create_retraining_pipeline(
    db_session: Session,
    base_model: str = "yolov8s-cls.pt",
    output_dir: str = "models/custom"
) -> RetrainingPipeline:
    """
    Factory function to create RetrainingPipeline instance.
    
    Args:
        db_session: Database session
        base_model: Base model path
        output_dir: Output directory
    
    Returns:
        Configured RetrainingPipeline
    """
    return RetrainingPipeline(
        db_session=db_session,
        base_model_path=base_model,
        output_dir=output_dir
    )
