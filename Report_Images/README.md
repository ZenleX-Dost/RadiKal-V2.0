# RadiKal Report Images

Place the following images in this folder for the LaTeX report to compile correctly.

## Required Images

### Logos and Institutional
| Filename | Description | Suggested Size |
|----------|-------------|----------------|
| `ensam_logo.png` | ENSAM Meknes official logo | 400x400 px |
| `radikal_logo.png` | RadiKal application logo | 300x300 px |
| `ensam_campus.jpg` | ENSAM Meknes campus photo | 1200x800 px |

### Defect Examples (from RIAWELC dataset)
| Filename | Description | Size |
|----------|-------------|------|
| `defect_lp.png` | Lack of Penetration sample | 224x224 px |
| `defect_po.png` | Porosity sample | 224x224 px |
| `defect_cr.png` | Crack sample | 224x224 px |
| `defect_nd.png` | No Defect sample | 224x224 px |

### XAI Outputs
| Filename | Description |
|----------|-------------|
| `xai_original.png` | Original input image |
| `xai_gradcam.png` | Grad-CAM heatmap overlay |
| `xai_shap.png` | SHAP explanation visualization |
| `xai_lime.png` | LIME superpixel explanation |

### Charts and Diagrams
| Filename | Description |
|----------|-------------|
| `confusion_matrix.png` | 4×4 confusion matrix heatmap |
| `performance_chart.png` | Bar chart comparing RadiKal vs literature |
| `database_schema.png` | Entity-relationship diagram |

### Application Screenshots
| Filename | Description |
|----------|-------------|
| `ui_dashboard.png` | Main dashboard view |
| `ui_upload.png` | Image upload interface |
| `ui_results.png` | Analysis results display |
| `ui_xai_panel.png` | XAI comparison panel |
| `ui_batch.png` | Batch processing interface |
| `ui_review.png` | Review queue interface |
| `ui_metrics.png` | Metrics dashboard |
| `ui_export.png` | Export dialog |
| `ui_settings.png` | Settings page |

### Use Case Screenshots
| Filename | Description |
|----------|-------------|
| `usecase1_upload.png` | Pipeline weld batch upload |
| `usecase1_crack.png` | Crack detection result |
| `usecase2_hybrid.png` | Aerospace hybrid analysis |
| `usecase2_report.png` | Compliance report preview |
| `usecase3_training.png` | Training feedback interface |

### Annex Images
| Filename | Description |
|----------|-------------|
| `annex_gradcam_lp.png` | Grad-CAM on Lack of Penetration |
| `annex_gradcam_po.png` | Grad-CAM on Porosity |
| `annex_gradcam_cr.png` | Grad-CAM on Cracks |
| `annex_gradcam_nd.png` | Grad-CAM on No Defect |

## How to Use

1. Add all images to this folder
2. In the LaTeX file, uncomment the `\includegraphics` lines
3. Comment out or remove the `\fbox{\parbox{...}}` placeholder lines
4. Compile with `pdflatex -shell-escape RadiKal_Report.tex`

## Tips for Screenshots

- Use browser at 100% zoom for consistent quality
- Capture at 1920x1080 minimum resolution
- Save as PNG for screenshots, JPG for photos
- Consider adding subtle drop shadows for polish
