# Cahier des Charges - RadiKal
## Système XAI de Contrôle Qualité Visuel pour la Détection de Défauts de Soudure
## Partie 1/2 : Présentation et Architecture

**Version:** 1.0  
**Date:** 21 Octobre 2025  
**Projet:** RadiKal - Explainable AI Visual Quality Control System  
**Propriétaire:** ZenleX-Dost  
**Type:** Cahier des Charges Technique

---

## 📋 Table des Matières - Partie 1

1. [Contexte et Objectifs](#1-contexte-et-objectifs)
2. [Périmètre du Projet](#2-périmètre-du-projet)
3. [Exigences Fonctionnelles](#3-exigences-fonctionnelles)
4. [Architecture Technique](#4-architecture-technique)
5. [Spécifications Backend](#5-spécifications-backend)

---

## 1. Contexte et Objectifs

### 1.1 Contexte
Le projet RadiKal vise à développer un système de contrôle qualité automatisé utilisant l'intelligence artificielle expliquable (XAI) pour la détection de défauts dans les images radiographiques de soudures industrielles.

### 1.2 Objectifs Principaux
- ✅ Détecter automatiquement les défauts de soudure avec une précision ≥ 95%
- ✅ Fournir des explications visuelles compréhensibles des décisions du modèle
- ✅ Atteindre un mAP@0.5 ≥ 99% sur le dataset RIAWELC
- ✅ Traiter les images en temps réel (< 200ms par image)
- ✅ Garantir la traçabilité complète des analyses

### 1.3 Bénéfices Attendus
- **Qualité**: Réduction des défauts non détectés de 80%
- **Productivité**: Gain de temps d'inspection de 60%
- **Confiance**: Transparence totale via les explications XAI
- **Traçabilité**: Historique complet des analyses et décisions

---

## 2. Périmètre du Projet

### 2.1 Inclus dans le Projet

#### 2.1.1 Dataset
- **Source**: RIAWELC (Radiographic Images for Automatic Weld Defects Classification)
- **Volume**: 24,407 images radiographiques
- **Format**: PNG 224×224 pixels, 8-bit grayscale
- **Classes**: 4 types de défauts
  - LP (Lack of Penetration) - Manque de pénétration
  - PO (Porosity) - Porosité
  - CR (Cracks) - Fissures
  - ND (No Defect) - Aucun défaut

#### 2.1.2 Modèle de Détection
- **Architecture**: YOLOv8s (Small) pré-entraîné
- **Performance cible**: mAP@0.5 ≥ 99.88%
- **Optimisation**: NVIDIA RTX 4050 (6GB VRAM)
- **Framework**: PyTorch 2.5.1 + CUDA 12.1

#### 2.1.3 Méthodes XAI (4 méthodes obligatoires)
1. **Grad-CAM** - Gradient-weighted Class Activation Mapping
2. **SHAP** - SHapley Additive exPlanations
3. **LIME** - Local Interpretable Model-agnostic Explanations
4. **Integrated Gradients** - Attribution-based explanations

#### 2.1.4 Backend API
- **Framework**: FastAPI 0.104.1+
- **Endpoints**: 6 endpoints REST obligatoires
  - `/api/xai-qc/health` - Vérification de santé
  - `/api/xai-qc/detect` - Détection de défauts
  - `/api/xai-qc/explain` - Génération d'explications XAI
  - `/api/xai-qc/metrics` - Métriques de performance
  - `/api/xai-qc/calibration` - Calibration du modèle
  - `/api/xai-qc/history` - Historique des analyses

#### 2.1.5 Frontend Web
- **Framework**: Next.js 14 + React 18
- **Pages**: 5 pages principales
  - Dashboard (analyse d'images)
  - Metrics (métriques de performance)
  - History (historique des analyses)
  - Settings (paramètres utilisateur)
  - Home (page d'accueil)
- **UI**: Tailwind CSS + Lucide Icons
- **État**: Zustand pour la gestion d'état

#### 2.1.6 MLOps & Monitoring
- **Tracking**: MLflow pour suivi des expériences
- **Versioning**: DVC pour données et modèles
- **Database**: SQLite pour persistance locale
- **Logs**: Système de logging structuré

### 2.2 Hors Périmètre
- ❌ Déploiement cloud (AWS/Azure/GCP)
- ❌ Application mobile (iOS/Android)
- ❌ Traitement vidéo en temps réel
- ❌ Authentification multi-utilisateurs avancée
- ❌ Intégration ERP/MES d'entreprise
- ❌ Support multi-langues (UI en anglais uniquement)

---

## 3. Exigences Fonctionnelles

### 3.1 Détection de Défauts (REQ-DET)

#### REQ-DET-001: Upload d'Images
**Priorité**: CRITIQUE  
**Description**: Le système doit permettre l'upload d'images radiographiques.
- **Formats supportés**: PNG, JPG, JPEG
- **Taille max**: 10 MB par image
- **Validation**: Vérification format + dimensions
- **Pré-traitement**: Redimensionnement automatique à 224×224

#### REQ-DET-002: Détection Automatique
**Priorité**: CRITIQUE  
**Description**: Détection automatique des défauts de soudure.
- **Modèle**: YOLOv8s optimisé
- **Classes**: LP, PO, CR, ND
- **Output**: Bounding boxes + confiance + classe
- **Temps de réponse**: < 200ms par image

#### REQ-DET-003: Calcul de Sévérité
**Priorité**: HAUTE  
**Description**: Attribution automatique d'un niveau de sévérité.
- **Critical**: confidence ≥ 90%
- **High**: confidence ≥ 70%
- **Medium**: confidence ≥ 50%
- **Low**: confidence < 50%

#### REQ-DET-004: Segmentation de Défauts
**Priorité**: MOYENNE  
**Description**: Génération de masques de segmentation pour chaque défaut.
- **Format**: Masques binaires
- **Encoding**: Base64 pour transmission API

### 3.2 Explications XAI (REQ-XAI)

#### REQ-XAI-001: Grad-CAM
**Priorité**: CRITIQUE  
**Description**: Génération de heatmaps Grad-CAM.
- **Target layers**: Dernière couche convolutionnelle
- **Colormap**: Jet (rouge = haute importance)
- **Overlay**: Superposition sur image originale

#### REQ-XAI-002: SHAP
**Priorité**: CRITIQUE  
**Description**: Calcul des valeurs SHAP pour chaque pixel.
- **Méthode**: DeepExplainer ou GradientExplainer
- **Nombre de samples**: 50-100 pour précision
- **Visualisation**: Heatmap de contribution

#### REQ-XAI-003: LIME
**Priorité**: HAUTE  
**Description**: Explication locale via LIME.
- **Segmentation**: Superpixels (quickshift)
- **Nombre de features**: 100-200 segments
- **Perturbations**: 1000 échantillons

#### REQ-XAI-004: Integrated Gradients
**Priorité**: HAUTE  
**Description**: Attribution basée sur les gradients intégrés.
- **Baseline**: Image noire (zéros)
- **Steps**: 50 étapes d'intégration
- **Précision**: Convergence garantie

#### REQ-XAI-005: Consensus XAI
**Priorité**: HAUTE  
**Description**: Agrégation des 4 méthodes XAI.
- **Méthode**: Moyenne pondérée des heatmaps
- **Score de consensus**: Corrélation entre méthodes
- **Seuil de confiance**: consensus ≥ 0.7 = fiable

### 3.3 Métriques et Monitoring (REQ-MET)

#### REQ-MET-001: Métriques Business
**Priorité**: CRITIQUE  
**Description**: Calcul des métriques métier.
- **True Positives (TP)**: Défauts correctement détectés
- **True Negatives (TN)**: Absences correctement détectées
- **False Positives (FP)**: Fausses alarmes
- **False Negatives (FN)**: Défauts manqués
- **Defect Rate**: Taux de défauts global
- **False Alarm Rate**: Taux de fausses alertes

#### REQ-MET-002: Métriques de Détection
**Priorité**: CRITIQUE  
**Description**: Métriques de performance du modèle.
- **mAP@0.5**: Mean Average Precision à IoU 50%
- **mAP@0.75**: Mean Average Precision à IoU 75%
- **mAP (average)**: mAP moyen sur IoU 0.5:0.95
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1-Score**: Moyenne harmonique Precision/Recall
- **AUROC**: Area Under ROC Curve

#### REQ-MET-003: Temps de Traitement
**Priorité**: HAUTE  
**Description**: Monitoring des performances temporelles.
- **Inference time**: Temps de détection
- **XAI computation time**: Temps de génération XAI
- **End-to-end latency**: Temps total < 500ms

### 3.4 Historique et Traçabilité (REQ-HIST)

#### REQ-HIST-001: Sauvegarde des Analyses
**Priorité**: CRITIQUE  
**Description**: Persistance de toutes les analyses.
- **Base de données**: SQLite locale
- **Champs**: image_id, timestamp, détections, métriques
- **Rétention**: Illimitée (configurable)

#### REQ-HIST-002: Export des Résultats
**Priorité**: HAUTE  
**Description**: Export des résultats d'analyse.
- **Formats**: PDF, Excel (XLSX), JSON
- **Contenu**: Image annotée + détections + explications
- **Génération**: À la demande

#### REQ-HIST-003: Recherche et Filtrage
**Priorité**: MOYENNE  
**Description**: Recherche dans l'historique.
- **Filtres**: Date, type de défaut, sévérité, nom de fichier
- **Tri**: Par date, confiance, nombre de défauts
- **Pagination**: 10-50 résultats par page

### 3.5 Paramètres Utilisateur (REQ-SETT)

#### REQ-SETT-001: Configuration de Confiance
**Priorité**: HAUTE  
**Description**: Ajustement du seuil de confiance.
- **Plage**: 0.1 à 0.9
- **Défaut**: 0.5
- **Impact**: Filtrage des détections faibles

#### REQ-SETT-002: Sauvegarde Automatique
**Priorité**: MOYENNE  
**Description**: Option de sauvegarde auto des analyses.
- **Valeurs**: On/Off
- **Défaut**: On
- **Effet**: Sauvegarde en DB automatique

#### REQ-SETT-003: Notifications
**Priorité**: BASSE  
**Description**: Alertes pour défauts critiques.
- **Types**: Critique uniquement / Critique + High / Tous
- **Méthode**: Toast notification dans l'UI

---

## 4. Architecture Technique

### 4.1 Architecture Globale

```
┌─────────────────────────────────────────────┐
│         Frontend (Next.js 14)               │
│  ┌───────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Dashboard │  │ Metrics  │  │ History │  │
│  └───────────┘  └──────────┘  └─────────┘  │
│         ↕ HTTP/REST (Port 3000)             │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│       Backend API (FastAPI)                 │
│  ┌──────────────────────────────────────┐   │
│  │     6 REST Endpoints                 │   │
│  │  /detect, /explain, /metrics, etc.   │   │
│  └──────────────┬───────────────────────┘   │
│                 ↕                            │
│  ┌──────────────▼───────────────────────┐   │
│  │      Core ML Layer                   │   │
│  │  ┌──────────┐  ┌─────────────────┐  │   │
│  │  │ YOLOv8s  │  │  4 XAI Methods  │  │   │
│  │  │ Detector │  │  (Grad-CAM,etc) │  │   │
│  │  └──────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────┘   │
│         ↕ Port 8000                         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Data & MLOps Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ SQLite   │  │ MLflow   │  │   DVC    │  │
│  │ Database │  │ Tracking │  │ Version  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

### 4.2 Technologies et Versions

#### 4.2.1 Backend
| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| Framework API | FastAPI | 0.104.1+ | Performance, async, auto-docs |
| Serveur ASGI | Uvicorn | 0.24.0+ | Serveur ASGI haute performance |
| ML Framework | PyTorch | 2.5.1+cu121 | Écosystème riche, GPU support |
| Détection | YOLOv8s | ultralytics 8.0+ | SOTA, rapide, pré-entraîné |
| XAI - Grad-CAM | Captum | 0.7.0+ | Bibliothèque Facebook officielle |
| XAI - SHAP | SHAP | 0.43.0+ | Standard industrie |
| XAI - LIME | LIME | 0.2.0.1+ | Méthode model-agnostic |
| MLOps | MLflow | 2.8.1+ | Tracking + Registry |
| Versioning | DVC | 3.30.1+ | Data + Model versioning |
| Database | SQLAlchemy | 2.0+ | ORM Python standard |
| Validation | Pydantic | 2.5.0+ | Validation de données |

#### 4.2.2 Frontend
| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| Framework | Next.js | 14.0.3+ | React SSR, performance |
| UI Library | React | 18.2.0+ | Composants réactifs |
| Styling | Tailwind CSS | 3.3.6+ | Utility-first CSS |
| State | Zustand | 4.5.7+ | État global léger |
| HTTP Client | Axios | 1.6.2+ | Requêtes HTTP robustes |
| Charts | Recharts | 2.15.4+ | Graphiques React natifs |
| Icons | Lucide React | 0.294.0+ | Icons modernes |
| Export | jsPDF | 3.0.3+ | Génération PDF |
| Tables | xlsx | 0.18.5+ | Export Excel |

#### 4.2.3 Infrastructure
| Composant | Technologie | Version | Justification |
|-----------|-------------|---------|---------------|
| GPU | NVIDIA RTX 4050 | - | 6GB VRAM, CUDA 12.1 |
| Python | Python | 3.10.11 | Compatibilité PyTorch |
| Node.js | Node.js | 18+ | Runtime Next.js |
| Database | SQLite | 3+ | Léger, sans serveur |
| Container | Docker | 24+ | Déploiement isolé |

### 4.3 Structure des Dossiers

```
RadiKal/
├── backend/                      # Backend Python
│   ├── api/                      # Couche API REST
│   │   ├── routes.py            # Définition des endpoints
│   │   ├── schemas.py           # Modèles Pydantic
│   │   └── middleware.py        # Middleware auth/CORS
│   │
│   ├── core/                     # Logique métier
│   │   ├── models/              # Modèles ML
│   │   │   ├── yolo_detector.py # YOLOv8 wrapper
│   │   │   └── detector.py      # Interface base
│   │   │
│   │   ├── xai/                 # Explications XAI
│   │   │   ├── gradcam.py       # Grad-CAM
│   │   │   ├── shap_explainer.py # SHAP
│   │   │   ├── lime_explainer.py # LIME
│   │   │   ├── integrated_gradients.py # IG
│   │   │   └── aggregator.py    # Consensus XAI
│   │   │
│   │   ├── metrics/             # Calcul de métriques
│   │   │   ├── business_metrics.py
│   │   │   ├── detection_metrics.py
│   │   │   └── segmentation_metrics.py
│   │   │
│   │   ├── uncertainty/         # Quantification incertitude
│   │   │   ├── mc_dropout.py    # Monte-Carlo Dropout
│   │   │   └── calibration.py   # ECE, temperature scaling
│   │   │
│   │   └── preprocessing/       # Traitement d'images
│   │       └── image_processor.py
│   │
│   ├── db/                       # Base de données
│   │   ├── database.py          # Configuration SQLAlchemy
│   │   └── models.py            # Modèles de données
│   │
│   ├── scripts/                  # Scripts utilitaires
│   │   ├── train_yolo.py        # Entraînement YOLOv8
│   │   ├── evaluate.py          # Évaluation modèle
│   │   └── test_yolo_integration.py
│   │
│   ├── tests/                    # Tests unitaires
│   │   ├── test_api_integration.py
│   │   ├── test_models.py
│   │   ├── test_xai.py
│   │   └── conftest.py
│   │
│   ├── configs/                  # Fichiers de configuration
│   │   ├── train_config.json    # Config entraînement
│   │   └── model_config.yaml    # Config modèle
│   │
│   ├── models/                   # Modèles entraînés
│   │   └── best.pt              # YOLOv8s entraîné
│   │
│   ├── main.py                   # Point d'entrée API
│   ├── requirements.txt          # Dépendances Python
│   ├── Dockerfile               # Image Docker backend
│   └── README.md                # Documentation backend
│
├── frontend/                     # Frontend Next.js
│   ├── app/                      # Pages Next.js 14
│   │   ├── page.tsx             # Page d'accueil
│   │   ├── layout.tsx           # Layout principal
│   │   ├── dashboard/           # Dashboard analyse
│   │   ├── metrics/             # Page métriques
│   │   ├── history/             # Historique
│   │   └── settings/            # Paramètres
│   │
│   ├── components/               # Composants réutilisables
│   │   ├── ui/                  # Composants UI de base
│   │   │   ├── Card.tsx
│   │   │   ├── Button.tsx
│   │   │   └── Spinner.tsx
│   │   ├── DetectionResults.tsx # Résultats détection
│   │   ├── XAIExplanations.tsx  # Affichage XAI
│   │   ├── ImageUpload.tsx      # Upload d'images
│   │   ├── Navbar.tsx           # Barre de navigation
│   │   └── Sidebar.tsx          # Menu latéral
│   │
│   ├── lib/                      # Utilitaires
│   │   └── api.ts               # Client API
│   │
│   ├── types/                    # Types TypeScript
│   │   └── index.ts             # Définitions de types
│   │
│   ├── store/                    # État global (Zustand)
│   │   ├── analysisStore.ts     # État des analyses
│   │   ├── settingsStore.ts     # Paramètres utilisateur
│   │   └── authStore.ts         # Authentification
│   │
│   ├── public/                   # Assets statiques
│   │   └── images/
│   │
│   ├── package.json             # Dépendances Node.js
│   ├── tsconfig.json            # Config TypeScript
│   ├── tailwind.config.js       # Config Tailwind
│   └── README.md                # Documentation frontend
│
├── docs/                         # Documentation
│   ├── RIAWELC_DATASET_INFO.md  # Info dataset
│   ├── guides/
│   │   ├── API_TESTING_GUIDE.md
│   │   └── DEPLOYMENT_CHECKLIST.md
│   └── archive/
│
├── DATA/                         # Données d'entraînement
│   ├── images/                  # Images RIAWELC
│   ├── labels/                  # Annotations YOLO
│   └── data.yaml                # Config dataset YOLO
│
├── docker-compose.yml           # Orchestration containers
├── README.md                    # Documentation projet
├── CHANGELOG.md                 # Historique des versions
├── START_RADIKAL.bat           # Lanceur Windows
└── STOP_ALL.ps1                # Arrêt des services
```

---

## 5. Spécifications Backend

### 5.1 API REST - Spécifications Détaillées

#### 5.1.1 Endpoint: Health Check
```
GET /api/xai-qc/health
```

**Objectif**: Vérifier l'état du système.

**Paramètres**: Aucun

**Réponse Success (200)**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "xai_methods_available": ["gradcam", "shap", "lime", "ig"],
  "gpu_available": true,
  "timestamp": "2025-10-21T14:30:00Z"
}
```

**Codes d'Erreur**:
- `503`: Service temporairement indisponible

---

#### 5.1.2 Endpoint: Detect Defects
```
POST /api/xai-qc/detect
```

**Objectif**: Détecter les défauts dans une image.

**Content-Type**: `multipart/form-data`

**Paramètres**:
- `file` (required): Fichier image (PNG/JPG/JPEG)
- `confidence_threshold` (optional): Seuil de confiance (0.1-0.9, défaut: 0.5)

**Réponse Success (200)**:
```json
{
  "image_id": "img_1729521234.567",
  "detections": [
    {
      "x1": 100.5,
      "y1": 150.3,
      "x2": 200.8,
      "y2": 250.9,
      "confidence": 0.956,
      "label": 0,
      "severity": "critical"
    }
  ],
  "segmentation_masks": ["base64_encoded_mask_1", "..."],
  "inference_time_ms": 145.3,
  "timestamp": "2025-10-21T14:30:00Z",
  "model_version": "YOLOv8s-1.0"
}
```

**Codes d'Erreur**:
- `400`: Format d'image invalide
- `413`: Fichier trop volumineux (> 10MB)
- `500`: Erreur lors de l'inférence

---

#### 5.1.3 Endpoint: Generate Explanations
```
POST /api/xai-qc/explain
```

**Objectif**: Générer les explications XAI pour une image analysée.

**Content-Type**: `application/json`

**Body**:
```json
{
  "image_id": "img_1729521234.567",
  "methods": ["gradcam", "shap", "lime", "ig"],
  "target_class": 0
}
```

**Paramètres**:
- `image_id` (required): ID de l'image à expliquer
- `methods` (optional): Liste des méthodes XAI (défaut: toutes)
- `target_class` (optional): Classe cible à expliquer (défaut: classe prédite)

**Réponse Success (200)**:
```json
{
  "image_id": "img_1729521234.567",
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
      "confidence_score": 0.89
    },
    {
      "method": "shap",
      "heatmap_base64": "data:image/png;base64,iVBORw0KGgo...",
      "confidence_score": 0.92
    }
  ],
  "aggregated_heatmap": "data:image/png;base64,iVBORw0KGgo...",
  "consensus_score": 0.87,
  "computation_time_ms": 1234.5,
  "timestamp": "2025-10-21T14:30:05Z"
}
```

**Codes d'Erreur**:
- `404`: Image ID non trouvé
- `400`: Méthode XAI invalide
- `500`: Erreur lors de la génération XAI

---

#### 5.1.4 Endpoint: Get Metrics
```
GET /api/xai-qc/metrics
```

**Objectif**: Récupérer les métriques de performance du système.

**Paramètres Query**:
- `start_date` (optional): Date de début (ISO 8601)
- `end_date` (optional): Date de fin (ISO 8601)

**Réponse Success (200)**:
```json
{
  "business_metrics": {
    "true_positives": 185,
    "true_negatives": 795,
    "false_positives": 8,
    "false_negatives": 12,
    "precision": 0.958,
    "recall": 0.939,
    "f1_score": 0.948,
    "defect_rate_percent": 2.0,
    "false_alarm_rate_percent": 0.8,
    "miss_rate_percent": 1.2
  },
  "detection_metrics": {
    "mAP@0.5": 0.9988,
    "mAP@0.75": 0.9856,
    "mAP": 0.9974,
    "precision": 0.958,
    "recall": 0.939,
    "f1_score": 0.948,
    "auroc": 0.945
  },
  "segmentation_metrics": {
    "mean_iou": 0.783,
    "mean_dice": 0.856,
    "pixel_accuracy": 0.912
  },
  "total_inspections": 1000,
  "date_range": {
    "start_date": "2025-10-01T00:00:00Z",
    "end_date": "2025-10-21T23:59:59Z"
  },
  "timestamp": "2025-10-21T14:30:00Z"
}
```

---

#### 5.1.5 Endpoint: Get Calibration
```
GET /api/xai-qc/calibration
```

**Objectif**: Obtenir les informations de calibration du modèle.

**Réponse Success (200)**:
```json
{
  "ece_score": 0.045,
  "temperature": 1.2,
  "calibrated": true,
  "confidence_bins": [
    {"bin_range": "0.0-0.1", "accuracy": 0.12, "confidence": 0.05, "count": 23},
    {"bin_range": "0.9-1.0", "accuracy": 0.98, "confidence": 0.95, "count": 456}
  ],
  "timestamp": "2025-10-21T14:30:00Z"
}
```

---

#### 5.1.6 Endpoint: Get History
```
GET /api/xai-qc/history
```

**Objectif**: Récupérer l'historique des analyses.

**Paramètres Query**:
- `page` (optional): Numéro de page (défaut: 1)
- `page_size` (optional): Taille de page (défaut: 10, max: 100)
- `defect_type` (optional): Filtrer par type (LP, PO, CR, ND)
- `severity` (optional): Filtrer par sévérité (critical, high, medium, low)
- `start_date` (optional): Date de début
- `end_date` (optional): Date de fin

**Réponse Success (200)**:
```json
{
  "total": 1543,
  "page": 1,
  "page_size": 10,
  "total_pages": 155,
  "analyses": [
    {
      "image_id": "img_1729521234.567",
      "filename": "weld_sample_001.png",
      "timestamp": "2025-10-21T14:30:00Z",
      "num_detections": 2,
      "has_defects": true,
      "highest_severity": "critical",
      "mean_confidence": 0.923,
      "defect_types": ["LP", "CR"]
    }
  ]
}
```

---

### 5.2 Modèle YOLOv8s - Spécifications

#### 5.2.1 Architecture
- **Backbone**: CSPDarknet53 modifié
- **Neck**: PANet (Path Aggregation Network)
- **Head**: Decoupled head (classification + localisation)
- **Paramètres**: ~11M paramètres
- **FLOPs**: ~28.4 GFLOPs

#### 5.2.2 Configuration d'Entraînement
```yaml
# data.yaml
path: DATA/
train: images/train
val: images/val
test: images/test

nc: 4  # nombre de classes
names: ['LP', 'PO', 'CR', 'ND']
```

```json
// train_config.json
{
  "model": "yolov8s.pt",
  "data": "DATA/data.yaml",
  "epochs": 50,
  "batch": 16,
  "imgsz": 224,
  "device": 0,
  "optimizer": "AdamW",
  "lr0": 0.001,
  "weight_decay": 0.0005,
  "mosaic": 1.0,
  "mixup": 0.1,
  "augment": true,
  "patience": 10,
  "save_period": 5
}
```

#### 5.2.3 Optimisations GPU
- **Mixed Precision**: Activé (FP16)
- **Gradient Accumulation**: 2 steps
- **Multi-scale Training**: [192, 224, 256]
- **TensorRT**: Support pour déploiement

---

**[Suite dans CdC_Part2.md]**

