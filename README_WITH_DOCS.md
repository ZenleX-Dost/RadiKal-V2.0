[![Documentation Status](https://readthedocs.org/projects/radikal-v2/badge/?version=latest)](https://radikal-v2.readthedocs.io/en/latest/?badge=latest)

# RadiKal V2.0 - XAI Visual Quality Control System

**Phase 1: Production Readiness - COMPLETE (100%)**  
**SAM2 Integration - COMPLETE**  
**Makerkit Frontend - COMPLETE**  
**Documentation - LIVE ON READ THE DOCS**

**Explainable AI for Automated Weld Defect Detection in Radiographic Images**

[![Version](https://img.shields.io/badge/version-2.0--production-blue.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](PHASE_1_COMPLETE_100_PERCENT.md)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/pytorch-2.5.1+cu121-red.svg)](https://pytorch.org/)
[![Next.js](https://img.shields.io/badge/nextjs-15-black.svg)](https://nextjs.org/)
[![Makerkit](https://img.shields.io/badge/Makerkit-Integrated-orange.svg)](https://makerkit.dev)
[![SAM2](https://img.shields.io/badge/SAM2-Segmentation-blueviolet.svg)](https://github.com/facebookresearch/segment-anything-2)
[![Phase 1](https://img.shields.io/badge/Phase%201-100%25%20Complete-brightgreen.svg)](PHASE1_QUICK_START.md)

---

## Documentation

**Full Documentation:** https://radikal-v2.readthedocs.io

Quick Links:
- [Getting Started](https://radikal-v2.readthedocs.io/en/latest/getting-started/)
- [Installation Guide](https://radikal-v2.readthedocs.io/en/latest/installation/)
- [API Reference](https://radikal-v2.readthedocs.io/en/latest/api-reference/)
- [User Guide](https://radikal-v2.readthedocs.io/en/latest/user-guide/)
- [Deployment Guide](https://radikal-v2.readthedocs.io/en/latest/deployment/)

---

## Quick Start

### Launch All Features
```batch
# Windows - Start Everything (Backend + Makerkit Frontend)
START_RADIKAL.bat

# Or manually:
# Terminal 1 - Backend API
cd backend
python run_server.py

# Terminal 2 - Makerkit Frontend
cd frontend-makerkit/apps/web
pnpm run dev
```

**Access Application**: http://localhost:3000 (Makerkit Frontend)  
**API Documentation**: http://localhost:8000/docs  
**Health Check**: http://localhost:8000/health/detailed

---

## What Makes RadiKal V2.0 Special?

### Production-Ready from Day One
- Complete backend API with 7 endpoints
- Modern B2B SaaS frontend (Makerkit)
- Comprehensive testing suite (>90% coverage)
- Security hardened with audit reports
- Deployment ready with Docker configs
- **Professional documentation on Read the Docs**

### Advanced AI Capabilities
- **Dual Detection**: YOLOv8 classification + SAM2 segmentation
- **Zero-Shot Learning**: SAM2 works without training on new defect types
- **4 XAI Methods**: Multiple explainability techniques for transparency
- **Hybrid Analysis**: Best of both classification and segmentation

### Modern Development Stack
- **Next.js 15**: Latest React framework with App Router
- **Makerkit**: Production-grade B2B SaaS architecture
- **Supabase**: Real-time database and authentication
- **TypeScript**: Type-safe frontend and backend
- **TailwindCSS v4**: Utility-first styling with Shadcn UI

---

## Free Deployment Options

### Documentation (Already Available!)
**Service**: Read the Docs  
**URL**: https://radikal-v2.readthedocs.io  
**Cost**: FREE forever

### Application Deployment

For deploying the full application for free, see:
- [FREE_DEPLOYMENT_GUIDE.md](FREE_DEPLOYMENT_GUIDE.md) - Complete free deployment options
- [DEPLOY_DOCS_NOW.md](DEPLOY_DOCS_NOW.md) - Documentation deployment guide

**Recommended Free Stack:**
- Frontend: Vercel (Free)
- Backend: Render (Free, CPU-only) or Local with Cloudflare Tunnel
- Database: Supabase (Free tier)
- Documentation: Read the Docs (Free)

---

## Project Structure

```
RadiKal-V2.0/
├── README.md                    # This file
├── .readthedocs.yaml           # Read the Docs config
├── mkdocs.yml                   # Documentation config
├── docs/                        # Full documentation
│   ├── index.md                # Documentation home
│   ├── getting-started.md      # Quick start
│   ├── installation.md         # Install guide
│   ├── user-guide.md           # User manual
│   ├── api-reference.md        # API docs
│   ├── architecture.md         # System design
│   ├── deployment.md           # Deployment
│   ├── testing.md              # Testing
│   ├── troubleshooting.md      # Help
│   ├── sam2-guide.md           # SAM2 guide
│   └── xai-methods.md          # XAI methods
├── backend/                     # FastAPI Backend
├── frontend-makerkit/           # Makerkit Frontend
├── DATA/                        # RIAWELC dataset
├── models/                      # ML model checkpoints
└── FREE_DEPLOYMENT_GUIDE.md    # Free deployment options
```

---

## Dataset: RIAWELC

This project uses the **RIAWELC** dataset - a publicly available academic dataset for weld defect classification.

- **Total Images**: 24,407 radiographic images (224x224, 8-bit grayscale PNG)
- **Classes**: LP, PO, CR, ND
- **Citation**: Totino et al., ICMECE 2022

For complete dataset information, see the [documentation](https://radikal-v2.readthedocs.io/en/latest/RIAWELC_DATASET_INFO/).

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

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

---

## Acknowledgments

- **RIAWELC Dataset**: University of Calabria (Totino et al., 2022)
- **SAM2**: Facebook Research - Segment Anything Model 2
- **Makerkit**: Next.js Supabase SaaS Starter Kit
- **YOLOv8**: Ultralytics - State-of-the-art object detection
- **ML Frameworks**: PyTorch, FastAPI, MLflow, Supabase
- **Documentation**: Read the Docs, MkDocs, Material theme

---

**Current Status**: PRODUCTION READY - All Core Features Complete  
**Documentation**: https://radikal-v2.readthedocs.io  
**Last Updated**: January 14, 2026  
**Version**: 2.0.0
