"""
Comprehensive model evaluation script for RadiKal
Generates accuracy, precision, recall, F1-score, confusion matrix, and detailed per-class metrics
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import confusion_matrix, classification_report, f1_score, accuracy_score
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.models.yolo_classifier import YOLOClassifier

class ModelEvaluator:
    """Comprehensive model evaluation with all metrics and confusion matrix"""
    
    def __init__(self, model_path="models/yolo/classification_defect_focused/weights/best.pt"):
        """Initialize evaluator with model"""
        self.model = YOLOClassifier(model_path=model_path)
        self.class_names = ["LP", "PO", "CR", "ND"]
        self.class_names_full = ["Lack of Penetration", "Porosity", "Cracks", "No Defect"]
        
    def load_test_images(self, test_dir="../DATA/testing"):
        """Load all test images and their labels from directory structure"""
        test_path = Path(test_dir)
        images = []
        labels = []
        
        # Map directory names to class indices
        dir_to_class = {
            "Difetto1": 0,  # LP
            "Difetto2": 1,  # PO
            "Difetto4": 2,  # CR
            "NoDifetto": 3  # ND
        }
        
        print(f"\n📂 Loading test images from: {test_path}")
        print(f"   Expected structure: {test_path}/<class_dir>/*.jpg")
        
        for dir_name, class_idx in dir_to_class.items():
            class_dir = test_path / dir_name
            if not class_dir.exists():
                print(f"   ⚠️  Class directory not found: {class_dir}")
                continue
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            class_name = self.class_names[class_idx]
            print(f"   Found {len(image_files)} images for class '{class_name}' ({dir_name}, index {class_idx})")
            
            for img_path in image_files:
                img = cv2.imread(str(img_path))
                if img is not None:
                    images.append(img)
                    labels.append(class_idx)
                else:
                    print(f"   ⚠️  Failed to load: {img_path}")
        
        print(f"\n✅ Total images loaded: {len(images)}")
        return images, labels
    
    def evaluate(self, test_dir="../DATA/testing"):
        """Run comprehensive evaluation"""
        print("\n" + "="*70)
        print("🚀 RADIKAL MODEL EVALUATION")
        print("="*70)
        
        # Load test data
        images, true_labels = self.load_test_images(test_dir)
        
        if len(images) == 0:
            print("❌ No test images found!")
            return None
        
        # Run inference
        print(f"\n🔍 Running inference on {len(images)} test images...")
        predictions = []
        confidences = []
        
        for i, img in enumerate(tqdm(images, desc="Processing")):
            result = self.model.classify(img)
            predictions.append(result['predicted_class'])
            confidences.append(result['confidence'])
        
        predictions = np.array(predictions)
        true_labels = np.array(true_labels)
        confidences = np.array(confidences)
        
        # Calculate metrics
        metrics = self._calculate_metrics(true_labels, predictions, confidences)
        
        # Generate confusion matrix
        cm = confusion_matrix(true_labels, predictions, labels=[0, 1, 2, 3])
        metrics['confusion_matrix'] = cm
        
        # Print results
        self._print_results(metrics, true_labels, predictions)
        
        # Save results
        self._save_results(metrics, cm, true_labels, predictions, confidences)
        
        return metrics
    
    def _calculate_metrics(self, true_labels, predictions, confidences):
        """Calculate comprehensive metrics"""
        metrics = {}
        
        # Overall metrics
        metrics['overall_accuracy'] = accuracy_score(true_labels, predictions)
        metrics['macro_f1'] = f1_score(true_labels, predictions, average='macro')
        metrics['weighted_f1'] = f1_score(true_labels, predictions, average='weighted')
        metrics['mean_confidence'] = float(np.mean(confidences))
        metrics['std_confidence'] = float(np.std(confidences))
        
        # Per-class metrics
        report = classification_report(true_labels, predictions, 
                                      target_names=self.class_names, 
                                      output_dict=True)
        
        metrics['per_class'] = {}
        for class_idx, class_name in enumerate(self.class_names):
            metrics['per_class'][class_name] = {
                'precision': float(report[class_name]['precision']),
                'recall': float(report[class_name]['recall']),
                'f1_score': float(report[class_name]['f1-score']),
                'support': int(report[class_name]['support'])
            }
        
        metrics['macro_precision'] = float(report['macro avg']['precision'])
        metrics['macro_recall'] = float(report['macro avg']['recall'])
        metrics['weighted_precision'] = float(report['weighted avg']['precision'])
        metrics['weighted_recall'] = float(report['weighted avg']['recall'])
        
        return metrics
    
    def _print_results(self, metrics, true_labels, predictions):
        """Print formatted results"""
        print("\n" + "="*70)
        print("📊 OVERALL METRICS")
        print("="*70)
        print(f"✓ Overall Accuracy:     {metrics['overall_accuracy']:.4f} ({metrics['overall_accuracy']*100:.2f}%)")
        print(f"✓ Macro F1-Score:       {metrics['macro_f1']:.4f}")
        print(f"✓ Weighted F1-Score:    {metrics['weighted_f1']:.4f}")
        print(f"✓ Mean Confidence:      {metrics['mean_confidence']:.4f} ± {metrics['std_confidence']:.4f}")
        
        print("\n" + "="*70)
        print("📈 PER-CLASS METRICS")
        print("="*70)
        print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
        print("-"*70)
        
        for class_name, stats in metrics['per_class'].items():
            class_full = self.class_names_full[self.class_names.index(class_name)]
            print(f"{class_full:<20} {stats['precision']:<12.4f} {stats['recall']:<12.4f} "
                  f"{stats['f1_score']:<12.4f} {stats['support']:<10}")
        
        print("\n" + "="*70)
        print("🔢 CONFUSION MATRIX")
        print("="*70)
        cm = metrics['confusion_matrix']
        print("\nPredictions →")
        print("Ground Truth ↓")
        print(f"{'':10} {self.class_names[0]:>8} {self.class_names[1]:>8} {self.class_names[2]:>8} {self.class_names[3]:>8}")
        for i, class_name in enumerate(self.class_names):
            print(f"{class_name:<10}", end="")
            for j in range(4):
                print(f"{cm[i, j]:>8}", end="")
            print()
        
        print("\n" + "="*70)
        print("📋 CLASSIFICATION REPORT")
        print("="*70)
        print(classification_report(true_labels, predictions, target_names=self.class_names))
    
    def _save_results(self, metrics, cm, true_labels, predictions, confidences):
        """Save results to files"""
        output_dir = Path("backend/evaluation_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save metrics as JSON
        metrics_json = {k: v for k, v in metrics.items() if k != 'confusion_matrix'}
        metrics_json['confusion_matrix'] = cm.tolist()
        
        with open(output_dir / "metrics.json", "w") as f:
            json.dump(metrics_json, f, indent=2)
        
        print(f"\n✅ Metrics saved to: {output_dir / 'metrics.json'}")
        
        # Generate confusion matrix plot
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=self.class_names,
                   yticklabels=self.class_names,
                   cbar_kws={'label': 'Count'})
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.title('Confusion Matrix - RadiKal Model Evaluation')
        plt.tight_layout()
        plt.savefig(output_dir / "confusion_matrix.png", dpi=300, bbox_inches='tight')
        print(f"✅ Confusion matrix plot saved to: {output_dir / 'confusion_matrix.png'}")
        plt.close()
        
        # Generate per-class metrics plot
        classes = list(metrics['per_class'].keys())
        precision_vals = [metrics['per_class'][c]['precision'] for c in classes]
        recall_vals = [metrics['per_class'][c]['recall'] for c in classes]
        f1_vals = [metrics['per_class'][c]['f1_score'] for c in classes]
        
        x = np.arange(len(classes))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width, precision_vals, width, label='Precision', color='#2E86AB')
        bars2 = ax.bar(x, recall_vals, width, label='Recall', color='#A23B72')
        bars3 = ax.bar(x + width, f1_vals, width, label='F1-Score', color='#F18F01')
        
        ax.set_xlabel('Class')
        ax.set_ylabel('Score')
        ax.set_title('Per-Class Performance Metrics')
        ax.set_xticks(x)
        ax.set_xticklabels(classes)
        ax.legend()
        ax.set_ylim([0, 1.1])
        
        # Add value labels on bars
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(output_dir / "per_class_metrics.png", dpi=300, bbox_inches='tight')
        print(f"✅ Per-class metrics plot saved to: {output_dir / 'per_class_metrics.png'}")
        plt.close()
        
        # Save detailed results
        with open(output_dir / "detailed_results.txt", "w") as f:
            f.write("="*70 + "\n")
            f.write("RADIKAL MODEL EVALUATION RESULTS\n")
            f.write("="*70 + "\n\n")
            
            f.write("OVERALL METRICS\n")
            f.write("-"*70 + "\n")
            f.write(f"Overall Accuracy:     {metrics['overall_accuracy']:.4f} ({metrics['overall_accuracy']*100:.2f}%)\n")
            f.write(f"Macro F1-Score:       {metrics['macro_f1']:.4f}\n")
            f.write(f"Weighted F1-Score:    {metrics['weighted_f1']:.4f}\n")
            f.write(f"Mean Confidence:      {metrics['mean_confidence']:.4f} ± {metrics['std_confidence']:.4f}\n\n")
            
            f.write("PER-CLASS METRICS\n")
            f.write("-"*70 + "\n")
            for class_name, stats in metrics['per_class'].items():
                f.write(f"\n{class_name}:\n")
                f.write(f"  Precision: {stats['precision']:.4f}\n")
                f.write(f"  Recall:    {stats['recall']:.4f}\n")
                f.write(f"  F1-Score:  {stats['f1_score']:.4f}\n")
                f.write(f"  Support:   {stats['support']}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("CONFUSION MATRIX\n")
            f.write("="*70 + "\n\n")
            f.write(f"{'':10} {self.class_names[0]:>8} {self.class_names[1]:>8} {self.class_names[2]:>8} {self.class_names[3]:>8}\n")
            cm = metrics['confusion_matrix']
            for i, class_name in enumerate(self.class_names):
                f.write(f"{class_name:<10}")
                for j in range(4):
                    f.write(f"{cm[i, j]:>8}")
                f.write("\n")
        
        print(f"✅ Detailed results saved to: {output_dir / 'detailed_results.txt'}")
        print(f"\n📁 All results available in: {output_dir}")


if __name__ == "__main__":
    try:
        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate()
        
        if metrics:
            print("\n" + "="*70)
            print("✅ EVALUATION COMPLETE")
            print("="*70)
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
