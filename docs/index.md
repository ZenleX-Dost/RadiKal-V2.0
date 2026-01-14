# RadiKal V2.0 Documentation

**Explainable AI for Automated Weld Defect Detection in Radiographic Images**

Version: 2.0.0  
Status: Production Ready  
Last Updated: January 14, 2026

---

## Welcome

RadiKal V2.0 is a production-ready Explainable AI (XAI) system for automated visual quality control of radiographic images, specializing in weld defect detection. The system combines state-of-the-art deep learning with interpretable AI techniques to provide transparent, trustworthy defect detection.

## Key Features

### Dual Detection System
- **YOLOv8 Classification**: Fast defect classification for 4 defect types (LP, PO, CR, ND)
- **SAM2 Segmentation**: Zero-shot pixel-level segmentation with no training required
- **Hybrid Analysis**: Combined classification and segmentation for comprehensive results

### Explainable AI Methods
- **Grad-CAM**: Gradient-weighted Class Activation Mapping
- **SHAP**: SHapley Additive exPlanations
- **LIME**: Local Interpretable Model-agnostic Explanations
- **Integrated Gradients**: Attribution-based explanations
- **Consensus Scoring**: Combined XAI method evaluation

### Modern Technology Stack
- **Backend**: FastAPI with Python 3.10+, PyTorch 2.5.1, CUDA 12.1
- **Frontend**: Next.js 15 with Makerkit B2B SaaS starter
- **Database**: Supabase for authentication and data storage
- **UI**: TypeScript, TailwindCSS v4, Shadcn UI components
- **ML Tools**: MLflow for experiment tracking, DVC for data versioning

### Production-Ready Features
- Real-time notifications with Server-Sent Events (SSE)
- Batch processing with concurrent image analysis
- Comprehensive REST API (7 endpoints)
- Advanced export (PDF/Excel) with customization
- GPU optimization for NVIDIA RTX 4050
- Docker deployment configuration
- Comprehensive testing suite (>90% coverage)

## Quick Links

### Getting Started
- [Installation Guide](installation.md) - Complete setup instructions
- [Getting Started](getting-started.md) - Quick start guide
- [User Guide](user-guide.md) - Comprehensive usage documentation

### Technical Documentation
- [Architecture](architecture.md) - System design and architecture
- [API Reference](api-reference.md) - Complete API documentation
- [SAM2 Integration](sam2-guide.md) - Segmentation capabilities
- [XAI Methods](xai-methods.md) - Explainability techniques

### Operations
- [Deployment Guide](deployment.md) - Production deployment
- [Testing Guide](testing.md) - Testing and quality assurance
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Dataset: RIAWELC

This project uses the **RIAWELC** dataset - a publicly available academic dataset for weld defect classification.

- **Full Name**: Radiographic Images for Automatic Weld Defects Classification
- **Total Images**: 24,407 radiographic images (224x224, 8-bit grayscale PNG)
- **Classes**: 4 weld defect types
  - No Defect (ND)
  - Lack of Penetration (LP)
  - Porosity (PO)
  - Cracks (CR)
- **Citation**: Totino et al., ICMECE 2022

For complete dataset information, see [RIAWELC Dataset Documentation](RIAWELC_DATASET_INFO.md).

## System Status

| Component | Status | Progress |
|-----------|--------|----------|
| Backend API | Complete | 100% |
| Makerkit Frontend | Complete | 100% |
| SAM2 Segmentation | Complete | 100% |
| YOLOv8 Classification | Complete | 100% |
| XAI Methods | Complete | 100% |
| Dataset | Ready | 100% |
| GPU Setup | Complete | 100% |
| Real-time Features | Complete | 100% |
| Testing | Complete | >90% |
| Deployment | Ready | 100% |

## Performance Expectations

Based on RIAWELC dataset characteristics:

| Metric | Expected Value | Notes |
|--------|---------------|-------|
| Overall mAP | 0.75 - 0.90 | Mean Average Precision |
| No Defect (ND) | 0.90 - 0.95 | Easiest class |
| Lack of Penetration (LP) | 0.75 - 0.85 | Good detectability |
| Porosity (PO) | 0.70 - 0.80 | Moderate difficulty |
| Cracks (CR) | 0.65 - 0.75 | Most challenging |
| Inference Time | < 200ms | Per image on RTX 4050 |
| Hybrid Analysis Time | ~2.25s | YOLOv8 + SAM2 combined |

## Recent Updates

### January 2026 - Makerkit Integration
- Complete B2B SaaS frontend with Next.js 15 + Supabase
- Turborepo monorepo structure for frontend packages
- Full TypeScript migration with type safety
- Shadcn UI component library integration

### December 2025 - SAM2 Segmentation
- Zero-shot segmentation without training needed
- Hybrid YOLOv8 + SAM2 analysis pipeline
- New `/api/xai-qc/analyze-hybrid` endpoint
- Frontend components for mask visualization
- 99.62% coverage, 2.25s processing time

### November 2025 - Phase 1 Completion
- Real-time notifications with SSE
- Advanced settings and user preferences
- Enhanced export functionality
- Batch processing capabilities
- Production middleware and security hardening

## License

MIT License - see LICENSE file for details.

## Academic Citation

If you use the RIAWELC dataset, please cite:

```bibtex
@inproceedings{totino2022riawelc,
  title={RIAWELC: A Novel Dataset of Radiographic Images for Automatic Weld Defects Classification},
  author={Totino, Benito and Spagnolo, Fanny and Perri, Stefania},
  booktitle={International Conference on Mechanical, Electric and Control Engineering (ICMECE)},
  year={2022},
  organization={IEEE}
}
```

## Acknowledgments

- **RIAWELC Dataset**: University of Calabria (Totino et al., 2022)
- **SAM2**: Facebook Research - Segment Anything Model 2
- **Makerkit**: Next.js Supabase SaaS Starter Kit
- **YOLOv8**: Ultralytics - State-of-the-art object detection
- **ML Frameworks**: PyTorch, FastAPI, MLflow, Supabase
