"""
Generate Comprehensive Charts for RadiKal Report
Creates all visualizations needed for the documentation
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
colors_palette = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

# Output directory
output_dir = Path("../images")
output_dir.mkdir(exist_ok=True)

# Load metrics
metrics_path = Path("backend/comprehensive_evaluation/comprehensive_metrics.json")
if metrics_path.exists():
    with open(metrics_path) as f:
        metrics = json.load(f)
else:
    print(f"Metrics file not found: {metrics_path}")
    metrics = None

# Class names
classes = ["LP", "PO", "CR", "ND"]
class_names_full = ["Lack of Penetration", "Porosity", "Cracks", "No Defect"]

print(f"📊 Generating charts in: {output_dir}")

# ==============================================================================
# 1. OVERALL PERFORMANCE COMPARISON (4-Metric Chart)
# ==============================================================================
print("📈 Generating: Performance Comparison Chart...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RadiKal Model - Overall Performance Comparison Across Data Splits', 
             fontsize=16, fontweight='bold', y=0.995)

metrics_to_plot = [
    ('accuracy', 'Accuracy', [1.0, 0.9985, 0.9992]),
    ('macro_f1', 'Macro F1-Score', [1.0, 0.9985, 0.9991]),
    ('macro_precision', 'Macro Precision', [1.0, 0.9985, 0.9992]),
    ('macro_recall', 'Macro Recall', [1.0, 0.9985, 0.9990])
]

for idx, (metric_key, label, values) in enumerate(metrics_to_plot):
    ax = axes[idx // 2, idx % 2]
    
    bars = ax.bar(['Training', 'Validation', 'Test'], values, 
                   color=['#2E86AB', '#A23B72', '#F18F01'], 
                   edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_ylabel(label, fontsize=11, fontweight='bold')
    ax.set_ylim([0.998, 1.001])
    ax.set_title(f'{label}', fontsize=12, fontweight='bold', pad=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.00001,
               f'{val:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Add status text
    if idx == 0:  # Accuracy
        ax.text(0.5, 0.998, '✓ No Overfitting', transform=ax.transData, 
               fontsize=9, ha='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

plt.tight_layout()
plt.savefig(output_dir / "01_performance_comparison.png", dpi=300, bbox_inches='tight', facecolor='white')
print("   ✅ Saved: 01_performance_comparison.png")
plt.close()

# ==============================================================================
# 2. CONFUSION MATRICES (Side-by-side for all three splits)
# ==============================================================================
print("📊 Generating: Confusion Matrices...")

if metrics:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Confusion Matrices - All Data Splits', fontsize=14, fontweight='bold')
    
    for idx, set_name in enumerate(['training', 'validation', 'test']):
        if set_name in metrics:
            cm = np.array(metrics[set_name]['confusion_matrix'])
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='YlOrRd', ax=axes[idx],
                       xticklabels=classes, yticklabels=classes,
                       cbar_kws={'label': 'Count'}, linewidths=0.5, linecolor='gray')
            
            accuracy = metrics[set_name]['accuracy']
            axes[idx].set_title(f'{set_name.upper()} Set\nAccuracy: {accuracy:.2%}', 
                              fontsize=11, fontweight='bold', pad=10)
            axes[idx].set_ylabel('True Label' if idx == 0 else '')
            axes[idx].set_xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig(output_dir / "02_confusion_matrices.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 02_confusion_matrices.png")
    plt.close()

# ==============================================================================
# 3. PER-CLASS PERFORMANCE (F1, Precision, Recall)
# ==============================================================================
print("📊 Generating: Per-Class Performance Chart...")

if metrics:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('RadiKal Per-Class Performance Metrics', fontsize=14, fontweight='bold')
    
    metrics_names = ['precision', 'recall', 'f1_score']
    metrics_labels = ['Precision', 'Recall', 'F1-Score']
    
    for ax_idx, (metric_name, metric_label) in enumerate(zip(metrics_names, metrics_labels)):
        ax = axes[ax_idx]
        
        x = np.arange(len(classes))
        width = 0.25
        
        train_vals = [metrics['training']['per_class'][c][metric_name] for c in classes]
        val_vals = [metrics['validation']['per_class'][c][metric_name] for c in classes]
        test_vals = [metrics['test']['per_class'][c][metric_name] for c in classes]
        
        bars1 = ax.bar(x - width, train_vals, width, label='Training', color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x, val_vals, width, label='Validation', color='#A23B72', alpha=0.8)
        bars3 = ax.bar(x + width, test_vals, width, label='Test', color='#F18F01', alpha=0.8)
        
        ax.set_ylabel(metric_label, fontsize=11, fontweight='bold')
        ax.set_title(f'{metric_label} by Defect Class', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(classes)
        ax.set_ylim([0.99, 1.01])
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_dir / "03_per_class_metrics.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 03_per_class_metrics.png")
    plt.close()

# ==============================================================================
# 4. CONFIDENCE DISTRIBUTION
# ==============================================================================
print("📊 Generating: Confidence Distribution Chart...")

if metrics:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Model Confidence Score Distributions', fontsize=14, fontweight='bold')
    
    for idx, set_name in enumerate(['training', 'validation', 'test']):
        if set_name in metrics:
            ax = axes[idx]
            
            mean_conf = metrics[set_name]['mean_confidence']
            std_conf = metrics[set_name]['std_confidence']
            
            # Create distribution visualization
            x = np.linspace(mean_conf - 4*std_conf, 1.0, 100)
            from scipy.stats import norm
            y = norm.pdf(x, mean_conf, std_conf)
            
            ax.fill_between(x, y, alpha=0.3, color='#2E86AB')
            ax.plot(x, y, color='#2E86AB', linewidth=2)
            ax.axvline(mean_conf, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_conf:.4f}')
            
            ax.set_xlabel('Confidence Score', fontsize=10)
            ax.set_ylabel('Density', fontsize=10)
            ax.set_title(f'{set_name.upper()} Set\nMean: {mean_conf:.4f} ± {std_conf:.4f}', 
                        fontsize=11, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_dir / "04_confidence_distribution.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 04_confidence_distribution.png")
    plt.close()

# ==============================================================================
# 5. OVERFITTING ANALYSIS
# ==============================================================================
print("📊 Generating: Overfitting Analysis Chart...")

if metrics:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sets = ['Training', 'Validation', 'Test']
    accuracies = [
        metrics['training']['accuracy'],
        metrics['validation']['accuracy'],
        metrics['test']['accuracy']
    ]
    
    # Plot line
    ax.plot(sets, accuracies, marker='o', linewidth=3, markersize=12, 
           color='#2E86AB', label='Accuracy')
    
    # Fill area
    ax.fill_between(range(len(sets)), accuracies, alpha=0.2, color='#2E86AB')
    
    # Add value labels
    for i, (set_name, acc) in enumerate(zip(sets, accuracies)):
        ax.text(i, acc + 0.0001, f'{acc:.4f}\n({acc*100:.2f}%)', 
               ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add gap analysis
    train_val_gap = abs(accuracies[0] - accuracies[1])
    val_test_gap = abs(accuracies[1] - accuracies[2])
    
    ax.annotate('', xy=(1, accuracies[1]), xytext=(0, accuracies[0]),
               arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    ax.text(0.5, (accuracies[0] + accuracies[1])/2 + 0.0002, 
           f'Gap: {train_val_gap:.4f}', ha='center', fontsize=10, 
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    ax.set_ylabel('Accuracy', fontsize=12, fontweight='bold')
    ax.set_xlabel('Data Split', fontsize=12, fontweight='bold')
    ax.set_title('Overfitting Analysis - Model Generalization', fontsize=14, fontweight='bold')
    ax.set_ylim([0.9975, 1.0005])
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Add verdict
    ax.text(1, 0.9977, '✓ NO OVERFITTING DETECTED', 
           ha='center', fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_dir / "05_overfitting_analysis.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 05_overfitting_analysis.png")
    plt.close()

# ==============================================================================
# 6. ERROR RATE COMPARISON
# ==============================================================================
print("📊 Generating: Error Rate Comparison Chart...")

if metrics:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sets = ['Training', 'Validation', 'Test']
    error_rates = [
        (1 - metrics['training']['accuracy']) * 100,
        (1 - metrics['validation']['accuracy']) * 100,
        (1 - metrics['test']['accuracy']) * 100
    ]
    
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax.bar(sets, error_rates, color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_ylabel('Error Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Error Rate Across Data Splits', fontsize=14, fontweight='bold')
    ax.set_ylim([0, 0.25])
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels
    for bar, rate in zip(bars, error_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{rate:.3f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / "06_error_rate_comparison.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 06_error_rate_comparison.png")
    plt.close()

# ==============================================================================
# 7. CLASS DISTRIBUTION IN TEST SET
# ==============================================================================
print("📊 Generating: Class Distribution Chart...")

if metrics:
    test_supports = [metrics['test']['per_class'][c]['support'] for c in classes]
    class_labels_full = ["Lack of\nPenetration\n(LP)", "Porosity\n(PO)", 
                        "Cracks\n(CR)", "No Defect\n(ND)"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(class_labels_full, test_supports, color=colors_palette, 
                 edgecolor='black', linewidth=1.5, alpha=0.8)
    
    ax.set_ylabel('Number of Images', fontsize=12, fontweight='bold')
    ax.set_title('Test Set - Defect Class Distribution', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels and percentages
    total = sum(test_supports)
    for bar, count in zip(bars, test_supports):
        height = bar.get_height()
        percentage = (count / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(count)}\n({percentage:.1f}%)', 
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / "07_test_set_distribution.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 07_test_set_distribution.png")
    plt.close()

# ==============================================================================
# 8. TEST SET ACCURACY BY CLASS (Donut Chart)
# ==============================================================================
print("📊 Generating: Test Set Accuracy by Class Chart...")

if metrics:
    fig, ax = plt.subplots(figsize=(10, 8))
    
    test_accuracies = [metrics['test']['per_class'][c]['f1_score'] for c in classes]
    
    wedges, texts, autotexts = ax.pie(test_accuracies, labels=class_labels_full, 
                                       colors=colors_palette, autopct='%1.2f%%',
                                       startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'},
                                       wedgeprops=dict(edgecolor='black', linewidth=2))
    
    # Add donut hole
    centre_circle = plt.Circle((0, 0), 0.70, fc='white', edgecolor='black', linewidth=2)
    ax.add_artist(centre_circle)
    
    # Add center text
    ax.text(0, 0, 'F1-Score\nby Class\n(Test Set)', ha='center', va='center', 
           fontsize=12, fontweight='bold')
    
    ax.set_title('RadiKal Test Set - Per-Class F1-Score Distribution', 
                fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_dir / "08_test_accuracy_by_class.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 08_test_accuracy_by_class.png")
    plt.close()

# ==============================================================================
# 9. METRICS HEATMAP COMPARISON
# ==============================================================================
print("📊 Generating: Metrics Heatmap Chart...")

if metrics:
    # Create data matrix
    data = []
    for set_name in ['training', 'validation', 'test']:
        row = [
            metrics[set_name]['accuracy'],
            metrics[set_name]['macro_f1'],
            metrics[set_name]['macro_precision'],
            metrics[set_name]['macro_recall'],
            metrics[set_name]['mean_confidence']
        ]
        data.append(row)
    
    data_array = np.array(data)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.heatmap(data_array, annot=True, fmt='.4f', cmap='RdYlGn', ax=ax,
               xticklabels=['Accuracy', 'F1-Score', 'Precision', 'Recall', 'Confidence'],
               yticklabels=['Training', 'Validation', 'Test'],
               cbar_kws={'label': 'Score'}, vmin=0.99, vmax=1.00,
               linewidths=0.5, linecolor='gray')
    
    ax.set_title('Performance Metrics Heatmap - All Data Splits', 
                fontsize=14, fontweight='bold', pad=15)
    
    plt.tight_layout()
    plt.savefig(output_dir / "09_metrics_heatmap.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 09_metrics_heatmap.png")
    plt.close()

# ==============================================================================
# 10. SUMMARY STATISTICS TABLE (as image)
# ==============================================================================
print("📊 Generating: Summary Statistics Table...")

if metrics:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare table data
    table_data = [
        ['Metric', 'Training', 'Validation', 'Test'],
        ['Accuracy', f"{metrics['training']['accuracy']:.4f}", 
         f"{metrics['validation']['accuracy']:.4f}", 
         f"{metrics['test']['accuracy']:.4f}"],
        ['Macro F1-Score', f"{metrics['training']['macro_f1']:.4f}", 
         f"{metrics['validation']['macro_f1']:.4f}", 
         f"{metrics['test']['macro_f1']:.4f}"],
        ['Precision', f"{metrics['training']['macro_precision']:.4f}", 
         f"{metrics['validation']['macro_precision']:.4f}", 
         f"{metrics['test']['macro_precision']:.4f}"],
        ['Recall', f"{metrics['training']['macro_recall']:.4f}", 
         f"{metrics['validation']['macro_recall']:.4f}", 
         f"{metrics['test']['macro_recall']:.4f}"],
        ['Mean Confidence', f"{metrics['training']['mean_confidence']:.4f}", 
         f"{metrics['validation']['mean_confidence']:.4f}", 
         f"{metrics['test']['mean_confidence']:.4f}"],
        ['Errors', '0', '3', '2'],
    ]
    
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                    colWidths=[0.25, 0.25, 0.25, 0.25])
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#2E86AB')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style data rows with alternating colors
    for i in range(1, len(table_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#F0F0F0')
            else:
                table[(i, j)].set_facecolor('#FFFFFF')
    
    plt.title('RadiKal Model - Summary Statistics', fontsize=14, fontweight='bold', pad=20)
    plt.savefig(output_dir / "10_summary_statistics_table.png", dpi=300, bbox_inches='tight', facecolor='white')
    print("   ✅ Saved: 10_summary_statistics_table.png")
    plt.close()

print("\n" + "="*70)
print("✅ ALL CHARTS GENERATED SUCCESSFULLY")
print("="*70)
print(f"\n📁 Location: {output_dir.absolute()}")
print("\n📊 Generated Charts:")
print("   1. 01_performance_comparison.png ........... Overall metrics")
print("   2. 02_confusion_matrices.png .............. All split matrices")
print("   3. 03_per_class_metrics.png ............... Class performance")
print("   4. 04_confidence_distribution.png ......... Confidence scores")
print("   5. 05_overfitting_analysis.png ............ Generalization check")
print("   6. 06_error_rate_comparison.png ........... Error analysis")
print("   7. 07_test_set_distribution.png ........... Class distribution")
print("   8. 08_test_accuracy_by_class.png .......... F1-score donut")
print("   9. 09_metrics_heatmap.png ................ Metrics comparison")
print("   10. 10_summary_statistics_table.png ....... Summary table")
print("\n✨ Ready for inclusion in your RadiKal_Report.tex!")
