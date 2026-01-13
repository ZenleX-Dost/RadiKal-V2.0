"""
Fast Comprehensive RadiKal Model Testing with Sampling
Tests representative samples from Training, Validation, Test sets
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path
from collections import Counter
from sklearn.metrics import (
    confusion_matrix, classification_report, f1_score, accuracy_score,
    precision_recall_fscore_support
)
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
import random

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))
from core.models.yolo_classifier import YOLOClassifier

class FastComprehensiveTester:
    """Fast comprehensive testing with sampling"""
    
    def __init__(self, model_path="models/yolo/classification_defect_focused/weights/best.pt", sample_size=500):
        """Initialize tester"""
        self.model = YOLOClassifier(model_path=model_path)
        self.class_names = ["LP", "PO", "CR", "ND"]
        self.class_names_full = ["Lack of Penetration", "Porosity", "Cracks", "No Defect"]
        self.sample_size = sample_size
        self.results = {}
        
    def load_dataset_sampled(self, dataset_dir, set_name="test", sample_size=None):
        """Load random sample from dataset"""
        if sample_size is None:
            sample_size = self.sample_size
        
        dataset_path = Path(dataset_dir)
        images = []
        labels = []
        
        dir_to_class = {
            "Difetto1": 0,
            "Difetto2": 1,
            "Difetto4": 2,
            "NoDifetto": 3
        }
        
        print(f"\n📂 Loading {set_name.upper()} set from: {dataset_path}")
        print(f"   (sampling ~{sample_size} images per class)")
        
        for dir_name, class_idx in dir_to_class.items():
            class_dir = dataset_path / dir_name
            if not class_dir.exists():
                print(f"   ⚠️  {dir_name} not found")
                continue
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            
            # Sample images
            if len(image_files) > sample_size:
                sampled_files = random.sample(image_files, sample_size)
                print(f"   {self.class_names[class_idx]}: {len(sampled_files)}/{len(image_files)} sampled")
            else:
                sampled_files = image_files
                print(f"   {self.class_names[class_idx]}: {len(sampled_files)} images (all)")
            
            for img_path in sampled_files:
                img = cv2.imread(str(img_path))
                if img is not None:
                    images.append(img)
                    labels.append(class_idx)
        
        print(f"   ✅ Total sampled: {len(images)} images")
        return images, labels
    
    def evaluate_set(self, images, labels, set_name="test"):
        """Evaluate dataset"""
        print(f"\n🔍 Running inference on {set_name.upper()} set ({len(images)} images)...")
        
        predictions = []
        confidences = []
        
        for img in tqdm(images, desc=f"Processing {set_name}"):
            result = self.model.classify(img)
            predictions.append(result['predicted_class'])
            confidences.append(result['confidence'])
        
        predictions = np.array(predictions)
        confidences = np.array(confidences)
        labels = np.array(labels)
        
        # Calculate metrics
        metrics = self._calculate_metrics(labels, predictions, confidences)
        self.results[set_name] = metrics
        
        return metrics, predictions, labels, confidences
    
    def _calculate_metrics(self, true_labels, predictions, confidences):
        """Calculate metrics"""
        metrics = {}
        
        metrics['accuracy'] = float(accuracy_score(true_labels, predictions))
        metrics['macro_f1'] = float(f1_score(true_labels, predictions, average='macro'))
        metrics['weighted_f1'] = float(f1_score(true_labels, predictions, average='weighted'))
        
        prec, rec, f1, _ = precision_recall_fscore_support(true_labels, predictions, average=None)
        metrics['macro_precision'] = float(np.mean(prec))
        metrics['macro_recall'] = float(np.mean(rec))
        
        metrics['mean_confidence'] = float(np.mean(confidences))
        metrics['std_confidence'] = float(np.std(confidences))
        
        # Per-class
        report = classification_report(true_labels, predictions,
                                      target_names=self.class_names,
                                      output_dict=True)
        
        metrics['per_class'] = {}
        for class_name in self.class_names:
            metrics['per_class'][class_name] = {
                'precision': float(report[class_name]['precision']),
                'recall': float(report[class_name]['recall']),
                'f1_score': float(report[class_name]['f1-score']),
                'support': int(report[class_name]['support'])
            }
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, predictions, labels=[0, 1, 2, 3])
        metrics['confusion_matrix'] = cm.tolist()
        
        return metrics
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE RADIKAL MODEL TESTING (SAMPLED)")
        print("="*80)
        
        all_results = {}
        
        # Test all three sets (with sampling for speed)
        for set_name, set_dir, sample_size in [
            ("training", "../DATA/training", 500),
            ("validation", "../DATA/validation", 500),
            ("test", "../DATA/testing", 2443)  # Full test set
        ]:
            images, labels = self.load_dataset_sampled(set_dir, set_name, sample_size)
            if len(images) == 0:
                continue
            
            metrics, predictions, true_labels, confidences = self.evaluate_set(images, labels, set_name)
            all_results[set_name] = {
                'metrics': metrics,
                'predictions': predictions.tolist(),
                'true_labels': true_labels.tolist()
            }
        
        # Print results
        self._print_results()
        
        # Generate plots
        self._generate_plots()
        
        # Save results
        self._save_results(all_results)
        
        return all_results
    
    def _print_results(self):
        """Print detailed results"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE RESULTS")
        print("="*80)
        
        # Summary table
        print("\n" + "="*80)
        print("PERFORMANCE COMPARISON")
        print("="*80)
        print(f"{'Metric':<25} {'Training':<20} {'Validation':<20} {'Test':<20}")
        print("-"*80)
        
        for metric in ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall']:
            row = f"{metric.replace('_', ' ').title():<25}"
            for set_name in ['training', 'validation', 'test']:
                if set_name in self.results:
                    val = self.results[set_name].get(metric, 0)
                    row += f" {val:.4f}{'':<14}"
                else:
                    row += f" {'N/A':<20}"
            print(row)
        
        # Detailed per-set
        for set_name in ['training', 'validation', 'test']:
            if set_name not in self.results:
                continue
            
            metrics = self.results[set_name]
            
            print("\n" + "="*80)
            print(f"📈 {set_name.upper()} SET")
            print("="*80)
            print(f"Accuracy:        {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
            print(f"Macro F1-Score:  {metrics['macro_f1']:.4f}")
            print(f"Mean Confidence: {metrics['mean_confidence']:.4f} ± {metrics['std_confidence']:.4f}")
            
            print(f"\nPer-Class Metrics:")
            print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1':<12}")
            print("-"*60)
            
            for class_name, stats in metrics['per_class'].items():
                print(f"{class_name:<20} {stats['precision']:<12.4f} {stats['recall']:<12.4f} {stats['f1_score']:<12.4f}")
        
        # Overfitting analysis
        print("\n" + "="*80)
        print("🔍 OVERFITTING ANALYSIS")
        print("="*80)
        
        if 'training' in self.results and 'validation' in self.results:
            train_acc = self.results['training']['accuracy']
            val_acc = self.results['validation']['accuracy']
            diff = abs(train_acc - val_acc)
            
            print(f"\nTraining Accuracy:   {train_acc:.4f}")
            print(f"Validation Accuracy: {val_acc:.4f}")
            print(f"Difference:          {diff:.4f}")
            
            if diff < 0.01:
                print(f"\n✅ VERDICT: NO OVERFITTING")
                print(f"   Model generalizes perfectly!")
            elif diff < 0.05:
                print(f"\n✅ VERDICT: MINIMAL OVERFITTING")
                print(f"   Performance gap is acceptable.")
            else:
                print(f"\n⚠️  VERDICT: POTENTIAL OVERFITTING")
                print(f"   Consider adding regularization.")
        
        if 'validation' in self.results and 'test' in self.results:
            val_acc = self.results['validation']['accuracy']
            test_acc = self.results['test']['accuracy']
            diff = abs(val_acc - test_acc)
            
            print(f"\nValidation Accuracy: {val_acc:.4f}")
            print(f"Test Accuracy:       {test_acc:.4f}")
            print(f"Difference:          {diff:.4f}")
            
            if diff < 0.01:
                print(f"\n✅ Validation set is representative of test set!")
    
    def _generate_plots(self):
        """Generate comparison plots"""
        output_dir = Path("backend/comprehensive_evaluation")
        output_dir.mkdir(exist_ok=True)
        
        # Performance comparison
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('RadiKal Performance Across Data Splits', fontsize=16, fontweight='bold')
        
        metrics = ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall']
        labels = ['Accuracy', 'F1-Score', 'Precision', 'Recall']
        
        for idx, (metric, label) in enumerate(zip(metrics, labels)):
            ax = axes[idx // 2, idx % 2]
            
            values = []
            for set_name in ['training', 'validation', 'test']:
                if set_name in self.results:
                    values.append(self.results[set_name].get(metric, 0))
            
            colors = ['#2E86AB', '#A23B72', '#F18F01']
            bars = ax.bar(['Training', 'Validation', 'Test'], values, color=colors)
            ax.set_ylabel(label)
            ax.set_ylim([0.97, 1.01])
            ax.grid(axis='y', alpha=0.3)
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.4f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_dir / "01_performance_comparison.png", dpi=300, bbox_inches='tight')
        print(f"\n✅ Performance comparison saved")
        plt.close()
        
        # Confusion matrices
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Confusion Matrices by Data Split', fontsize=14, fontweight='bold')
        
        for idx, set_name in enumerate(['training', 'validation', 'test']):
            if set_name not in self.results:
                continue
            
            cm = np.array(self.results[set_name]['confusion_matrix'])
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                       xticklabels=self.class_names,
                       yticklabels=self.class_names)
            axes[idx].set_title(f'{set_name.upper()}')
            axes[idx].set_ylabel('True')
            axes[idx].set_xlabel('Predicted')
        
        plt.tight_layout()
        plt.savefig(output_dir / "02_confusion_matrices.png", dpi=300, bbox_inches='tight')
        print(f"✅ Confusion matrices saved")
        plt.close()
    
    def _save_results(self, all_results):
        """Save results"""
        output_dir = Path("backend/comprehensive_evaluation")
        output_dir.mkdir(exist_ok=True)
        
        # Save metrics
        metrics_only = {
            set_name: all_results[set_name]['metrics']
            for set_name in all_results
        }
        
        with open(output_dir / "comprehensive_metrics.json", "w") as f:
            json.dump(metrics_only, f, indent=2)
        
        # Save report
        with open(output_dir / "comprehensive_report.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write("RADIKAL MODEL - COMPREHENSIVE EVALUATION\n")
            f.write("="*80 + "\n\n")
            
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Metric':<25} {'Training':<20} {'Validation':<20} {'Test':<20}\n")
            f.write("-"*80 + "\n")
            
            for metric in ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall']:
                row = f"{metric.replace('_', ' ').title():<25}"
                for set_name in ['training', 'validation', 'test']:
                    if set_name in self.results:
                        val = self.results[set_name].get(metric, 0)
                        row += f" {val:.4f}{'':<14}"
                f.write(row + "\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("OVERFITTING ASSESSMENT\n")
            f.write("="*80 + "\n\n")
            
            if 'training' in self.results and 'validation' in self.results:
                train_acc = self.results['training']['accuracy']
                val_acc = self.results['validation']['accuracy']
                diff = abs(train_acc - val_acc)
                
                f.write(f"Training Accuracy:   {train_acc:.4f}\n")
                f.write(f"Validation Accuracy: {val_acc:.4f}\n")
                f.write(f"Difference:          {diff:.4f}\n\n")
                
                if diff < 0.01:
                    f.write("✅ NO OVERFITTING - Model generalizes excellently\n")
                elif diff < 0.05:
                    f.write("✅ MINIMAL OVERFITTING - Acceptable performance gap\n")
                else:
                    f.write("⚠️  POTENTIAL OVERFITTING - Consider regularization\n")
        
        print(f"✅ Metrics saved")
        print(f"✅ Report saved")
        print(f"\n📁 All results in: {output_dir}")


if __name__ == "__main__":
    try:
        random.seed(42)
        tester = FastComprehensiveTester()
        results = tester.run_all_tests()
        
        print("\n" + "="*80)
        print("✅ COMPREHENSIVE TESTING COMPLETE")
        print("="*80)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
