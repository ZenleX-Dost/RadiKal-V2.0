"""
Comprehensive RadiKal Model Testing
Tests: Training Set, Validation Set, Test Set
Generates: Confusion matrices, ROC curves, detailed analysis
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path
from collections import defaultdict, Counter
from sklearn.metrics import (
    confusion_matrix, classification_report, f1_score, accuracy_score,
    precision_recall_fscore_support, roc_curve, auc, roc_auc_score,
    precision_recall_curve
)
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))
from core.models.yolo_classifier import YOLOClassifier

class ComprehensiveModelTester:
    """Comprehensive model testing across all data splits"""
    
    def __init__(self, model_path="models/yolo/classification_defect_focused/weights/best.pt"):
        """Initialize tester with model"""
        self.model = YOLOClassifier(model_path=model_path)
        self.class_names = ["LP", "PO", "CR", "ND"]
        self.class_names_full = ["Lack of Penetration", "Porosity", "Cracks", "No Defect"]
        self.results = {}
        
    def load_dataset(self, dataset_dir, set_name="test"):
        """Load dataset from directory"""
        dataset_path = Path(dataset_dir)
        images = []
        labels = []
        
        dir_to_class = {
            "Difetto1": 0,  # LP
            "Difetto2": 1,  # PO
            "Difetto4": 2,  # CR
            "NoDifetto": 3  # ND
        }
        
        print(f"\n📂 Loading {set_name.upper()} set from: {dataset_path}")
        
        for dir_name, class_idx in dir_to_class.items():
            class_dir = dataset_path / dir_name
            if not class_dir.exists():
                print(f"   ⚠️  {dir_name} not found")
                continue
            
            image_files = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
            class_name = self.class_names[class_idx]
            print(f"   {class_name}: {len(image_files)} images")
            
            for img_path in image_files:
                img = cv2.imread(str(img_path))
                if img is not None:
                    images.append(img)
                    labels.append(class_idx)
        
        print(f"   ✅ Total: {len(images)} images loaded")
        return images, labels
    
    def evaluate_set(self, images, labels, set_name="test"):
        """Evaluate a dataset"""
        print(f"\n🔍 Running inference on {set_name.upper()} set ({len(images)} images)...")
        
        predictions = []
        confidences = []
        probabilities_all = []
        
        for img in tqdm(images, desc=f"Processing {set_name}"):
            result = self.model.classify(img)
            predictions.append(result['predicted_class'])
            confidences.append(result['confidence'])
            
            # Extract probabilities for ROC
            all_probs = result.get('all_probabilities', {})
            probs = [all_probs.get(self.class_names[i], 0) for i in range(4)]
            probabilities_all.append(probs)
        
        predictions = np.array(predictions)
        confidences = np.array(confidences)
        probabilities_all = np.array(probabilities_all)
        labels = np.array(labels)
        
        # Calculate metrics
        metrics = self._calculate_all_metrics(labels, predictions, confidences, probabilities_all)
        metrics['set_name'] = set_name
        
        self.results[set_name] = metrics
        return metrics, predictions, confidences, probabilities_all
    
    def _calculate_all_metrics(self, true_labels, predictions, confidences, probabilities_all):
        """Calculate comprehensive metrics"""
        metrics = {}
        
        # Overall metrics
        metrics['accuracy'] = float(accuracy_score(true_labels, predictions))
        metrics['macro_f1'] = float(f1_score(true_labels, predictions, average='macro'))
        metrics['weighted_f1'] = float(f1_score(true_labels, predictions, average='weighted'))
        metrics['macro_precision'] = float(np.mean(precision_recall_fscore_support(true_labels, predictions, average=None)[0]))
        metrics['macro_recall'] = float(np.mean(precision_recall_fscore_support(true_labels, predictions, average=None)[1]))
        
        metrics['mean_confidence'] = float(np.mean(confidences))
        metrics['std_confidence'] = float(np.std(confidences))
        metrics['min_confidence'] = float(np.min(confidences))
        metrics['max_confidence'] = float(np.max(confidences))
        
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
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, predictions, labels=[0, 1, 2, 3])
        metrics['confusion_matrix'] = cm.tolist()
        
        # ROC-AUC (one-vs-rest)
        try:
            roc_auc_scores = []
            for i in range(4):
                y_binary = (true_labels == i).astype(int)
                if len(np.unique(y_binary)) > 1:  # Only if both classes present
                    roc_auc = roc_auc_score(y_binary, probabilities_all[:, i])
                    roc_auc_scores.append(roc_auc)
            metrics['macro_roc_auc'] = float(np.mean(roc_auc_scores)) if roc_auc_scores else None
        except:
            metrics['macro_roc_auc'] = None
        
        return metrics
    
    def run_all_tests(self):
        """Run tests on all three data splits"""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE RADIKAL MODEL TESTING")
        print("="*80)
        
        all_results = {}
        
        # Test on all three sets
        for set_name, set_dir in [
            ("training", "../DATA/training"),
            ("validation", "../DATA/validation"),
            ("test", "../DATA/testing")
        ]:
            images, labels = self.load_dataset(set_dir, set_name)
            if len(images) == 0:
                print(f"   ❌ No data found for {set_name}")
                continue
            
            metrics, predictions, confidences, probs = self.evaluate_set(images, labels, set_name)
            all_results[set_name] = {
                'metrics': metrics,
                'predictions': predictions.tolist(),
                'true_labels': labels.tolist(),
                'confidences': confidences.tolist()
            }
        
        # Print comprehensive results
        self._print_comprehensive_results()
        
        # Generate visualizations
        self._generate_visualizations()
        
        # Save results
        self._save_comprehensive_results(all_results)
        
        return all_results
    
    def _print_comprehensive_results(self):
        """Print detailed results for all sets"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE RESULTS ACROSS ALL DATA SPLITS")
        print("="*80)
        
        # Summary table
        print("\n" + "="*80)
        print("OVERALL PERFORMANCE COMPARISON")
        print("="*80)
        print(f"{'Metric':<25} {'Training':<20} {'Validation':<20} {'Test':<20}")
        print("-"*80)
        
        for metric_name in ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall', 'mean_confidence']:
            values = []
            for set_name in ['training', 'validation', 'test']:
                if set_name in self.results:
                    val = self.results[set_name].get(metric_name, 'N/A')
                    if isinstance(val, (int, float)):
                        values.append(f"{val:.4f}")
                    else:
                        values.append(str(val))
                else:
                    values.append("N/A")
            
            metric_display = metric_name.replace('_', ' ').title()
            print(f"{metric_display:<25} {values[0]:<20} {values[1]:<20} {values[2]:<20}")
        
        # Detailed per-set results
        for set_name in ['training', 'validation', 'test']:
            if set_name not in self.results:
                continue
            
            metrics = self.results[set_name]
            print("\n" + "="*80)
            print(f"📈 {set_name.upper()} SET DETAILED RESULTS")
            print("="*80)
            print(f"\nAccuracy:           {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
            print(f"Macro F1-Score:     {metrics['macro_f1']:.4f}")
            print(f"Macro Precision:    {metrics['macro_precision']:.4f}")
            print(f"Macro Recall:       {metrics['macro_recall']:.4f}")
            print(f"Mean Confidence:    {metrics['mean_confidence']:.4f} ± {metrics['std_confidence']:.4f}")
            print(f"Confidence Range:   [{metrics['min_confidence']:.4f}, {metrics['max_confidence']:.4f}]")
            
            if metrics.get('macro_roc_auc'):
                print(f"Macro ROC-AUC:      {metrics['macro_roc_auc']:.4f}")
            
            print(f"\nPer-Class Performance:")
            print(f"{'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
            print("-"*80)
            
            for class_name, stats in metrics['per_class'].items():
                class_full = self.class_names_full[self.class_names.index(class_name)]
                print(f"{class_full:<20} {stats['precision']:<12.4f} {stats['recall']:<12.4f} "
                      f"{stats['f1_score']:<12.4f} {stats['support']:<10}")
            
            # Confusion matrix
            print(f"\nConfusion Matrix:")
            cm = np.array(metrics['confusion_matrix'])
            print(f"{'':10} {self.class_names[0]:>8} {self.class_names[1]:>8} {self.class_names[2]:>8} {self.class_names[3]:>8}")
            for i, class_name in enumerate(self.class_names):
                print(f"{class_name:<10}", end="")
                for j in range(4):
                    print(f"{cm[i, j]:>8}", end="")
                print()
    
    def _generate_visualizations(self):
        """Generate visualization plots"""
        output_dir = Path("backend/comprehensive_evaluation")
        output_dir.mkdir(exist_ok=True)
        
        # Comparison bar chart
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('RadiKal Model Performance Across All Data Splits', fontsize=16, fontweight='bold')
        
        metrics_to_plot = ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall']
        metric_labels = ['Accuracy', 'F1-Score', 'Precision', 'Recall']
        
        for idx, (metric, label) in enumerate(zip(metrics_to_plot, metric_labels)):
            ax = axes[idx // 2, idx % 2]
            
            values = []
            for set_name in ['training', 'validation', 'test']:
                if set_name in self.results:
                    values.append(self.results[set_name].get(metric, 0))
            
            colors = ['#2E86AB', '#A23B72', '#F18F01']
            bars = ax.bar(['Training', 'Validation', 'Test'], values, color=colors)
            ax.set_ylabel(label, fontsize=11)
            ax.set_ylim([0.98, 1.001])
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.4f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_dir / "performance_comparison.png", dpi=300, bbox_inches='tight')
        print(f"\n✅ Performance comparison plot saved to: {output_dir / 'performance_comparison.png'}")
        plt.close()
        
        # Confusion matrices for each set
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Confusion Matrices Across Data Splits', fontsize=14, fontweight='bold')
        
        for idx, set_name in enumerate(['training', 'validation', 'test']):
            if set_name not in self.results:
                continue
            
            cm = np.array(self.results[set_name]['confusion_matrix'])
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                       xticklabels=self.class_names,
                       yticklabels=self.class_names,
                       cbar_kws={'label': 'Count'})
            axes[idx].set_title(f'{set_name.upper()} Set')
            axes[idx].set_ylabel('True Label')
            axes[idx].set_xlabel('Predicted Label')
        
        plt.tight_layout()
        plt.savefig(output_dir / "confusion_matrices_comparison.png", dpi=300, bbox_inches='tight')
        print(f"✅ Confusion matrices comparison saved to: {output_dir / 'confusion_matrices_comparison.png'}")
        plt.close()
        
        # Confidence distribution
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        fig.suptitle('Confidence Score Distributions', fontsize=14, fontweight='bold')
        
        for idx, set_name in enumerate(['training', 'validation', 'test']):
            if set_name not in self.results:
                continue
            
            confidences = self.results[set_name].get('confidences', [])
            axes[idx].hist(confidences, bins=50, color='#2E86AB', edgecolor='black', alpha=0.7)
            axes[idx].set_title(f'{set_name.upper()} Set')
            axes[idx].set_xlabel('Confidence Score')
            axes[idx].set_ylabel('Frequency')
            axes[idx].grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "confidence_distributions.png", dpi=300, bbox_inches='tight')
        print(f"✅ Confidence distributions saved to: {output_dir / 'confidence_distributions.png'}")
        plt.close()
    
    def _save_comprehensive_results(self, all_results):
        """Save all results"""
        output_dir = Path("backend/comprehensive_evaluation")
        output_dir.mkdir(exist_ok=True)
        
        # Save metrics
        metrics_only = {
            set_name: all_results[set_name]['metrics']
            for set_name in all_results
        }
        
        with open(output_dir / "comprehensive_metrics.json", "w") as f:
            json.dump(metrics_only, f, indent=2)
        
        print(f"\n✅ Comprehensive metrics saved to: {output_dir / 'comprehensive_metrics.json'}")
        
        # Save detailed report
        with open(output_dir / "comprehensive_report.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write("RADIKAL MODEL - COMPREHENSIVE EVALUATION REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Metric':<25} {'Training':<20} {'Validation':<20} {'Test':<20}\n")
            f.write("-"*80 + "\n")
            
            for metric_name in ['accuracy', 'macro_f1', 'macro_precision', 'macro_recall']:
                values = []
                for set_name in ['training', 'validation', 'test']:
                    if set_name in self.results:
                        val = self.results[set_name].get(metric_name, 'N/A')
                        values.append(f"{val:.4f}" if isinstance(val, (int, float)) else str(val))
                    else:
                        values.append("N/A")
                
                metric_display = metric_name.replace('_', ' ').title()
                f.write(f"{metric_display:<25} {values[0]:<20} {values[1]:<20} {values[2]:<20}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("OVERFITTING ANALYSIS\n")
            f.write("="*80 + "\n\n")
            
            if 'training' in self.results and 'validation' in self.results:
                train_acc = self.results['training']['accuracy']
                val_acc = self.results['validation']['accuracy']
                diff = abs(train_acc - val_acc)
                
                f.write(f"Training Accuracy:   {train_acc:.4f}\n")
                f.write(f"Validation Accuracy: {val_acc:.4f}\n")
                f.write(f"Difference:          {diff:.4f}\n\n")
                
                if diff < 0.01:
                    f.write("✅ VERDICT: NO OVERFITTING DETECTED\n")
                    f.write("   Model generalizes well from training to validation set.\n")
                elif diff < 0.05:
                    f.write("⚠️  VERDICT: MINIMAL OVERFITTING\n")
                    f.write("   Performance gap is acceptable (<5%).\n")
                else:
                    f.write("⚠️  VERDICT: POTENTIAL OVERFITTING\n")
                    f.write("   Performance gap >5%, consider regularization.\n")
        
        print(f"✅ Comprehensive report saved to: {output_dir / 'comprehensive_report.txt'}")
        print(f"\n📁 All results available in: {output_dir}")


if __name__ == "__main__":
    try:
        tester = ComprehensiveModelTester()
        all_results = tester.run_all_tests()
        
        print("\n" + "="*80)
        print("✅ COMPREHENSIVE TESTING COMPLETE")
        print("="*80)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
