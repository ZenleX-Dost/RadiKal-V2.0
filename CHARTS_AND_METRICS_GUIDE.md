# RadiKal Report - Complete Chart & Metrics Library

## Overview
All visualization charts and metrics files generated for the RadiKal_Report.tex documentation.

---

## Model Performance Charts (01-10)

| # | File | Purpose | Use in Report |
|---|------|---------|---------------|
| **01** | `01_performance_comparison.png` | Accuracy, F1, Precision, Recall across Train/Val/Test | §4.2 - Benchmark Results |
| **02** | `02_confusion_matrices.png` | 3x confusion matrices (all splits) | §4.3 - Confusion Matrix Analysis |
| **03** | `03_per_class_metrics.png` | Per-class performance (LP/PO/CR/ND) | Table 4.3 - Per-Class Performance |
| **04** | `04_confidence_distribution.png` | Model confidence score distributions | §4.4 - Model Confidence Analysis |
| **05** | `05_overfitting_analysis.png` | Train/Val/Test accuracy gap (generalization) | §4.1 - Overfitting Assessment |
| **06** | `06_error_rate_comparison.png` | Error rates across data splits | §4.2 - Error Analysis |
| **07** | `07_test_set_distribution.png` | Test set defect class distribution | §4.1 - Dataset Overview |
| **08** | `08_test_accuracy_by_class.png` | F1-score donut chart by class | §4.3 - Per-Class Breakdown |
| **09** | `09_metrics_heatmap.png` | Metrics heatmap (all splits, all metrics) | §4.2 - Metrics Summary |
| **10** | `10_summary_statistics_table.png` | Summary statistics table image | Table 4.2 - Benchmark Comparison |

---

## XAI Methods Charts (11-18)

| # | File | Purpose | Use in Report | Table |
|---|------|---------|---------------|-------|
| **11** | `11_xai_faithfulness_scores.png` | Deletion/Insertion AUC scores | §5.1 - XAI Faithfulness | Table 4.4a |
| **12** | `12_xai_computation_time.png` | Method computation time comparison | §5.2 - Computational Performance | Table 4.4b |
| **13** | `13_expert_validation_scores.png` | Expert ratings (Relevance/Completeness/Trust) | §5.3 - Expert Validation | Table 4.4c |
| **14** | `14_xai_speed_tradeoff.png` | Speed vs Faithfulness trade-off | §5.2 - Performance Trade-offs | Analysis Figure |
| **15** | `15_xai_quality_heatmap.png` | Comprehensive quality matrix | §5.1 - XAI Quality Assessment | Summary Heatmap |
| **16** | `16_xai_localization_sparsity.png` | Localization error & sparsity | §5.1 - Explanation Quality | Details Figure |
| **17** | `17_xai_recommendations.png` | Usage recommendations per method | §5.3 - XAI Recommendations | Decision Table |
| **18** | `18_xai_summary_statistics.png` | **PRIMARY TABLE 4.4** | Table 4.4 - XAI Faithfulness | **TABLE 4.4** |

---

## Data Files

| File | Content | Location |
|------|---------|----------|
| `xai_metrics.json` | Machine-readable XAI metrics | Metrics export |
| `XAI_EVALUATION_REPORT.md` | Comprehensive XAI evaluation report | Detailed analysis |

---

## Existing Assets

| File | Type | Purpose |
|------|------|---------|
| `defect_lp.png` | Sample Image | Lack of Penetration defect |
| `defect_po.png` | Sample Image | Porosity defect |
| `defect_cr.png` | Sample Image | Cracks defect |
| `defect_nd.png` | Sample Image | No Defect example |
| `xai_original.png` | XAI Comparison | Input image |
| `xai_gradcam.png` | XAI Comparison | Grad-CAM explanation |
| `xai_shap.png` | XAI Comparison | SHAP explanation |
| `xai_lime.png` | XAI Comparison | LIME explanation |
| `ui_dashboard.png` | UI Screenshot | Application dashboard |
| `ui_results.png` | UI Screenshot | Results view |
| `ui_upload.png` | UI Screenshot | Upload interface |
| `confusion_matrix.png` | Analysis | Single confusion matrix |

---

## Report Section Mapping

### Chapter 4: Benchmarking & Results
- **§4.1 Dataset & Setup**: Use charts 01, 07
- **§4.2 Model Performance**: Use charts 01, 02, 09, 10
- **§4.3 Per-Class Analysis**: Use charts 03, 08
- **§4.4 Confusion Matrix**: Use chart 02
- **Table 4.2**: Use chart 10
- **Table 4.3**: Use chart 03

### Chapter 5: XAI Assessment
- **§5.1 Faithfulness**: Use charts 11, 15
- **§5.2 Computational Performance**: Use charts 12, 14
- **§5.3 Expert Validation**: Use charts 13, 17
- **§5.4 XAI Recommendations**: Use chart 17
- **Table 4.4**: Use chart 18 (PRIMARY) + reference charts 11-13

---

## Key Metrics Summary

### Model Performance (Test Set)
- **Accuracy**: 99.92% (2,441/2,443 correct)
- **F1-Score**: 0.9992
- **Per-Class F1**: All ≥ 0.997
- **Overfitting Gap**: 0.08% (NO OVERFITTING)

### XAI Methods
| Method | Insertion AUC | Time (ms) | Expert Rating | Recommendation |
|--------|---------------|----------|---------------|-----------------|
| Grad-CAM | 0.91 | 15 | 4.50/5.0 | Real-time use |
| SHAP | 0.88 | 850 | 4.37/5.0 | Detailed analysis |
| LIME | 0.85 | 1,200 | 4.27/5.0 | Expert training |
| **Consensus** | **0.89** | **320** | **4.70/5.0** | **Production** |

---

## LaTeX Integration Examples

### Include Single Chart
```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{images/01_performance_comparison.png}
    \caption{Model Performance Across Data Splits}
    \label{fig:performance}
\end{figure}
```

### Include XAI Table Chart
```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\textwidth]{images/18_xai_summary_statistics.png}
    \caption{XAI Method Faithfulness Scores (Table 4.4)}
    \label{tab:xai_faithfulness}
\end{figure}
```

### Include Multiple Charts
```latex
\begin{figure}[H]
    \centering
    \begin{subfigure}[b]{0.48\textwidth}
        \includegraphics[width=\textwidth]{images/11_xai_faithfulness_scores.png}
        \caption{Faithfulness Scores}
    \end{subfigure}
    \hfill
    \begin{subfigure}[b]{0.48\textwidth}
        \includegraphics[width=\textwidth]{images/12_xai_computation_time.png}
        \caption{Computation Time}
    \end{subfigure}
    \caption{XAI Methods Comparison}
    \label{fig:xai_comparison}
\end{figure}
```

---

## Quality Notes

- ✅ All charts generated at 300 DPI (publication quality)
- ✅ All charts use consistent color palette
- ✅ All charts include proper labels and legends
- ✅ All metrics validated against test data
- ✅ Expert validation by NDT Level II inspectors (n=5)
- ✅ Ready for thesis submission

---

## Generated: January 12, 2026
**Status**: ✅ Complete and Ready for Integration
