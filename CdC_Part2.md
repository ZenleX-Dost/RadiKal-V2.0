# Cahier des Charges - RadiKal
## Système XAI de Contrôle Qualité Visuel pour la Détection de Défauts de Soudure
## Partie 2/2 : Spécifications Frontend et Exigences Non-Fonctionnelles

**Version:** 1.0  
**Date:** 21 Octobre 2025  
**Projet:** RadiKal - Explainable AI Visual Quality Control System  
**Propriétaire:** ZenleX-Dost  
**Type:** Cahier des Charges Technique

---

## 📋 Table des Matières - Partie 2

6. [Spécifications Frontend](#6-spécifications-frontend)
7. [Exigences Non-Fonctionnelles](#7-exigences-non-fonctionnelles)
8. [Sécurité et Conformité](#8-sécurité-et-conformité)
9. [Tests et Validation](#9-tests-et-validation)
10. [Déploiement et Maintenance](#10-déploiement-et-maintenance)
11. [Livrables et Jalons](#11-livrables-et-jalons)

---

## 6. Spécifications Frontend

### 6.1 Architecture Frontend

#### 6.1.1 Structure Next.js 14
```
frontend/
├── app/                           # App Router (Next.js 14)
│   ├── page.tsx                  # Home page
│   ├── layout.tsx                # Root layout
│   ├── dashboard/
│   │   └── page.tsx              # Dashboard principal
│   ├── metrics/
│   │   └── page.tsx              # Métriques de performance
│   ├── history/
│   │   └── page.tsx              # Historique des analyses
│   └── settings/
│       └── page.tsx              # Paramètres utilisateur
│
├── components/                    # Composants React
│   ├── ui/                       # Composants UI de base
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── Spinner.tsx
│   │   └── Tooltip.tsx
│   ├── DetectionResults.tsx      # Affichage résultats détection
│   ├── XAIExplanations.tsx       # Visualisation XAI
│   ├── ImageUpload.tsx           # Upload d'images
│   ├── MetricsChart.tsx          # Graphiques de métriques
│   ├── Navbar.tsx                # Barre de navigation
│   └── Sidebar.tsx               # Menu latéral
│
├── lib/                          # Utilitaires et helpers
│   ├── api.ts                    # Client API Axios
│   ├── utils.ts                  # Fonctions utilitaires
│   └── constants.ts              # Constantes globales
│
├── types/                        # Définitions TypeScript
│   └── index.ts                  # Types partagés
│
└── store/                        # État global (Zustand)
    ├── analysisStore.ts          # État des analyses
    ├── settingsStore.ts          # Paramètres utilisateur
    └── authStore.ts              # État authentification
```

---

### 6.2 Pages Détaillées

#### 6.2.1 Page: Home (`/`)
**Objectif**: Présentation du système et navigation rapide.

**Sections**:
1. **Hero Section**
   - Titre: "RadiKal - XAI Visual Quality Control"
   - Description: Système de détection de défauts explicable
   - Call-to-Action: Boutons "Start Analysis" et "View Documentation"

2. **Features Grid**
   - Carte 1: Détection automatique (icône Shield)
   - Carte 2: Explications XAI (icône Brain)
   - Carte 3: Métriques en temps réel (icône BarChart)
   - Carte 4: Historique complet (icône History)

3. **Stats Bar**
   - Nombre total d'analyses: XXX
   - Taux de précision: 95.8%
   - Défauts détectés: XXX

**Interactions**:
- Clic sur "Start Analysis" → Redirige vers `/dashboard`
- Clic sur "View Metrics" → Redirige vers `/metrics`

---

#### 6.2.2 Page: Dashboard (`/dashboard`)
**Objectif**: Interface principale d'analyse d'images.

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  Navbar (RadiKal logo + navigation)             │
├───────────────┬─────────────────────────────────┤
│               │  Upload Section                 │
│               │  ┌───────────────────────────┐  │
│               │  │ Drag & Drop Area          │  │
│   Sidebar     │  │ [Browse Files]            │  │
│   - Dashboard │  └───────────────────────────┘  │
│   - Metrics   │                                 │
│   - History   │  Detection Results              │
│   - Settings  │  ┌───────────────────────────┐  │
│               │  │ Image + Bounding Boxes    │  │
│               │  │ Defect: LP (Critical)     │  │
│               │  │ Confidence: 95.6%         │  │
│               │  └───────────────────────────┘  │
│               │                                 │
│               │  XAI Explanations               │
│               │  [Grad-CAM] [SHAP] [LIME] [IG] │
│               │  Consensus Score: 87%           │
└───────────────┴─────────────────────────────────┘
```

**Fonctionnalités**:

1. **Upload d'Image**
   - Drag & Drop activé
   - Formats: PNG, JPG, JPEG
   - Taille max: 10 MB
   - Preview instantané de l'image
   - Validation client-side (format + taille)

2. **Détection Automatique**
   - Déclenchement: Au clic sur "Analyze"
   - Loading state: Spinner + "Analyzing..."
   - Affichage résultats:
     - Image annotée avec bounding boxes
     - Liste des défauts détectés
     - Pour chaque défaut: Type (abbrev + full name), confiance, sévérité

3. **XAI Explanations**
   - 4 onglets: Grad-CAM, SHAP, LIME, Integrated Gradients
   - Heatmaps superposées sur l'image originale
   - Score de consensus affiché
   - Toggle "Show All Methods" pour comparaison côte-à-côte

4. **Actions**
   - Bouton "Save Analysis" → Sauvegarde en DB
   - Bouton "Export PDF" → Génère rapport PDF
   - Bouton "Clear" → Réinitialise l'interface

**États**:
- `idle`: Aucune analyse en cours
- `uploading`: Upload en cours
- `analyzing`: Détection en cours
- `explaining`: Génération XAI en cours
- `complete`: Analyse terminée
- `error`: Erreur survenue

---

#### 6.2.3 Page: Metrics (`/metrics`)
**Objectif**: Visualisation des métriques de performance.

**Sections**:

1. **Header avec Filtres**
   - Date Range Picker (start_date, end_date)
   - Bouton "Refresh Metrics"
   - Bouton "Export Excel"

2. **Business Metrics Cards**
   - Carte 1: True Positives (TP) + icône CheckCircle
   - Carte 2: True Negatives (TN) + icône XCircle
   - Carte 3: False Positives (FP) + icône AlertCircle
   - Carte 4: False Negatives (FN) + icône AlertTriangle
   - Carte 5: Precision (95.8%) + tooltip explicatif
   - Carte 6: Recall (93.9%) + tooltip explicatif
   - Carte 7: F1-Score (94.8%) + tooltip explicatif
   - Carte 8: AUROC (94.5%) + tooltip explicatif

3. **Detection Metrics Cards**
   - Carte 1: mAP@0.5 (99.88%) + tooltip
   - Carte 2: mAP@0.75 (98.56%) + tooltip
   - Carte 3: mAP (99.74%) + tooltip

4. **Confusion Matrix**
   - Heatmap 4×4 (LP, PO, CR, ND)
   - Affichage des vraies classes vs prédites
   - Bibliothèque: Recharts

5. **Trend Charts**
   - Graphique linéaire: Évolution Precision/Recall/F1 dans le temps
   - Graphique à barres: Distribution des défauts par type

**Tooltips Obligatoires**:
```tsx
// Exemple de tooltip pour Precision
<Tooltip content="Precision measures the accuracy of positive predictions. High precision means few false alarms." />

// Tooltip pour mAP@0.5
<Tooltip content="Mean Average Precision at 50% IoU threshold. Measures detection accuracy across all classes." />
```

---

#### 6.2.4 Page: History (`/history`)
**Objectif**: Historique complet des analyses effectuées.

**Layout**:

1. **Filtres et Recherche**
   - Champ de recherche (par nom de fichier)
   - Filtre par type de défaut (LP, PO, CR, ND, All)
   - Filtre par sévérité (Critical, High, Medium, Low, All)
   - Date Range Picker

2. **Table des Analyses**
   - Colonnes:
     - Thumbnail (miniature de l'image)
     - Filename
     - Date/Time
     - Defect Types (badges colorés)
     - Num Detections
     - Highest Severity
     - Mean Confidence
     - Actions (View, Export, Delete)
   - Tri par colonne activé
   - Pagination (10, 25, 50, 100 résultats par page)

3. **Modal de Détails**
   - Clic sur "View" → Ouvre modal
   - Contenu modal:
     - Image annotée
     - Liste complète des détections
     - Explications XAI (si disponibles)
     - Boutons: Export PDF, Delete

**États de chargement**:
- Skeleton loader pendant le fetch
- Empty state si aucune analyse

---

#### 6.2.5 Page: Settings (`/settings`)
**Objectif**: Configuration des paramètres utilisateur.

**Sections**:

1. **Detection Settings**
   - Slider: Confidence Threshold (0.1 - 0.9)
   - Toggle: Auto-save analyses
   - Select: Default XAI method

2. **Notification Settings**
   - Toggle: Enable notifications
   - Radio Group: Notification level (All, High+Critical, Critical only)

3. **Export Settings**
   - Checkbox: Include XAI in PDF exports
   - Checkbox: Include metadata in Excel exports

4. **System Info**
   - Backend URL: `http://localhost:8000`
   - Model Version: YOLOv8s-1.0
   - Last Update: 2025-10-21

**Sauvegarde**:
- Bouton "Save Settings" en bas
- Confirmation toast: "Settings saved successfully"

---

### 6.3 Composants Réutilisables

#### 6.3.1 Component: ImageUpload
**Props**:
```typescript
interface ImageUploadProps {
  onUpload: (file: File) => void;
  maxSizeMB?: number;
  acceptedFormats?: string[];
  disabled?: boolean;
}
```

**Features**:
- Drag & Drop zone
- Click to browse
- Image preview
- Validation client-side
- Loading state

---

#### 6.3.2 Component: DetectionResults
**Props**:
```typescript
interface DetectionResultsProps {
  image: string;  // Base64 ou URL
  detections: Detection[];
  loading?: boolean;
}

interface Detection {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  label: number;
  class_abbr: string;    // "LP", "PO", "CR", "ND"
  class_full_name: string;  // "Lack of Penetration", etc.
  severity: "critical" | "high" | "medium" | "low";
}
```

**Rendering**:
- Canvas avec bounding boxes
- Couleurs par sévérité:
  - Critical: Rouge (#EF4444)
  - High: Orange (#F97316)
  - Medium: Jaune (#EAB308)
  - Low: Vert (#22C55E)
- Liste des détections sous l'image

---

#### 6.3.3 Component: XAIExplanations
**Props**:
```typescript
interface XAIExplanationsProps {
  imageId: string;
  explanations: XAIExplanation[];
  consensusScore?: number;
  loading?: boolean;
}

interface XAIExplanation {
  method: "gradcam" | "shap" | "lime" | "ig";
  heatmap_base64: string;
  confidence_score: number;
}
```

**Features**:
- Onglets pour chaque méthode
- Heatmaps superposées
- Affichage du consensus score
- Toggle pour comparaison côte-à-côte

---

#### 6.3.4 Component: MetricsChart
**Props**:
```typescript
interface MetricsChartProps {
  data: MetricDataPoint[];
  type: "line" | "bar" | "area";
  xKey: string;
  yKey: string;
  title?: string;
}
```

**Bibliothèque**: Recharts

---

### 6.4 État Global (Zustand)

#### 6.4.1 Store: analysisStore
```typescript
interface AnalysisState {
  // État
  currentImage: File | null;
  detections: Detection[];
  explanations: XAIExplanation[];
  status: "idle" | "uploading" | "analyzing" | "explaining" | "complete" | "error";
  error: string | null;
  
  // Actions
  setImage: (file: File) => void;
  startAnalysis: () => Promise<void>;
  generateExplanations: (imageId: string) => Promise<void>;
  clearAnalysis: () => void;
  resetError: () => void;
}
```

#### 6.4.2 Store: settingsStore
```typescript
interface SettingsState {
  // Paramètres
  confidenceThreshold: number;
  autoSave: boolean;
  defaultXAIMethod: string;
  notificationsEnabled: boolean;
  notificationLevel: "all" | "high+critical" | "critical";
  
  // Actions
  updateSettings: (settings: Partial<SettingsState>) => void;
  resetToDefaults: () => void;
}
```

---

### 6.5 Client API (Axios)

**Fichier**: `frontend/lib/api.ts`

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/xai-qc`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Endpoints
export const apiEndpoints = {
  // Health Check
  health: () => api.get('/health'),
  
  // Détection
  detect: (formData: FormData) => 
    api.post('/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  // Explications XAI
  explain: (payload: ExplainPayload) => 
    api.post('/explain', payload),
  
  // Métriques
  metrics: (params?: { start_date?: string; end_date?: string }) => 
    api.get('/metrics', { params }),
  
  // Calibration
  calibration: () => 
    api.get('/calibration'),
  
  // Historique
  history: (params?: HistoryParams) => 
    api.get('/history', { params }),
};

// Intercepteurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

---

## 7. Exigences Non-Fonctionnelles

### 7.1 Performance (REQ-PERF)

#### REQ-PERF-001: Temps de Réponse API
**Priorité**: CRITIQUE  
- **Détection**: < 200ms (95th percentile)
- **Explications XAI**: < 2000ms (95th percentile)
- **Métriques**: < 100ms (95th percentile)
- **Historique**: < 300ms (95th percentile)

#### REQ-PERF-002: Temps de Chargement Frontend
**Priorité**: HAUTE  
- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.0s

#### REQ-PERF-003: Débit
**Priorité**: HAUTE  
- **Concurrent Users**: 10 utilisateurs simultanés
- **Throughput**: 100 images/heure par utilisateur

#### REQ-PERF-004: Utilisation des Ressources
**Priorité**: MOYENNE  
- **GPU Memory**: < 5GB VRAM pendant l'inférence
- **CPU**: < 80% pendant l'inférence
- **RAM**: < 4GB pour le backend

---

### 7.2 Scalabilité (REQ-SCAL)

#### REQ-SCAL-001: Croissance des Données
**Priorité**: MOYENNE  
- **Database**: Support jusqu'à 100,000 analyses
- **Storage**: Support jusqu'à 50GB d'images

#### REQ-SCAL-002: Charge de Travail
**Priorité**: BASSE  
- **Horizontal Scaling**: Préparé pour scaling (Docker)
- **Load Balancing**: Non requis (version 1.0)

---

### 7.3 Fiabilité (REQ-REL)

#### REQ-REL-001: Disponibilité
**Priorité**: HAUTE  
- **Uptime**: 95% en environnement local
- **MTBF** (Mean Time Between Failures): > 30 jours

#### REQ-REL-002: Gestion des Erreurs
**Priorité**: CRITIQUE  
- Toutes les erreurs doivent retourner un code HTTP approprié
- Messages d'erreur clairs et actionnables
- Logging structuré de toutes les erreurs

#### REQ-REL-003: Reprise sur Panne
**Priorité**: HAUTE  
- Redémarrage automatique des services via Docker
- Aucune perte de données en cas de crash

---

### 7.4 Maintenabilité (REQ-MAINT)

#### REQ-MAINT-001: Code Quality
**Priorité**: HAUTE  
- **Backend**: Type hints Python, docstrings
- **Frontend**: TypeScript strict mode
- **Tests**: Couverture ≥ 80% pour code critique

#### REQ-MAINT-002: Documentation
**Priorité**: HAUTE  
- README complet avec instructions setup
- API documentation (Swagger/OpenAPI)
- Commentaires inline pour logique complexe

#### REQ-MAINT-003: Logs
**Priorité**: HAUTE  
- Logging structuré (JSON)
- Niveaux: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Rotation des logs (max 100MB par fichier)

---

### 7.5 Utilisabilité (REQ-USE)

#### REQ-USE-001: Interface Utilisateur
**Priorité**: HAUTE  
- UI intuitive, nécessitant < 5 minutes de formation
- Feedback visuel pour toutes les actions
- Messages d'erreur compréhensibles

#### REQ-USE-002: Accessibilité
**Priorité**: MOYENNE  
- Contraste minimum 4.5:1 (WCAG AA)
- Navigation au clavier possible
- Alt text pour toutes les images

#### REQ-USE-003: Responsive Design
**Priorité**: MOYENNE  
- Support desktop (≥ 1280px largeur)
- Tablet partiellement supporté (≥ 768px)
- Mobile non requis (version 1.0)

---

### 7.6 Compatibilité (REQ-COMP)

#### REQ-COMP-001: Navigateurs
**Priorité**: HAUTE  
- Chrome ≥ 100
- Firefox ≥ 100
- Edge ≥ 100
- Safari ≥ 15

#### REQ-COMP-002: Système d'Exploitation
**Priorité**: CRITIQUE  
- **Backend**: Windows 10/11, Linux (Ubuntu 20.04+)
- **Frontend**: Cross-platform (via navigateur)

#### REQ-COMP-003: GPU
**Priorité**: CRITIQUE  
- NVIDIA GPU avec CUDA 12.1+
- Compute Capability ≥ 6.1
- VRAM ≥ 6GB

---

## 8. Sécurité et Conformité

### 8.1 Sécurité (REQ-SEC)

#### REQ-SEC-001: Upload de Fichiers
**Priorité**: CRITIQUE  
- Validation stricte des formats (magic numbers)
- Limite de taille: 10MB
- Scan anti-malware (optionnel)
- Isolation des fichiers uploadés

#### REQ-SEC-002: API
**Priorité**: HAUTE  
- CORS configuré (whitelist origins)
- Rate limiting: 100 requêtes/minute par IP
- Validation des inputs (Pydantic)

#### REQ-SEC-003: Données Sensibles
**Priorité**: MOYENNE  
- Pas de stockage de données personnelles
- Historique supprimable par utilisateur
- Pas de transmission de données à des tiers

#### REQ-SEC-004: Authentification
**Priorité**: BASSE (Version 1.0)  
- Pas d'authentification requise (déploiement local)
- Prêt pour ajout JWT (version future)

---

### 8.2 Conformité (REQ-CONF)

#### REQ-CONF-001: Licences Open Source
**Priorité**: HAUTE  
- Respect des licences (MIT, Apache 2.0, BSD)
- Attribution des dépendances tierces
- Pas de dépendances GPL dans le code commercial

#### REQ-CONF-002: Protection des Données
**Priorité**: MOYENNE  
- RGPD: Droit à l'effacement (historique)
- Pas de collecte de données personnelles

---

## 9. Tests et Validation

### 9.1 Tests Backend

#### 9.1.1 Tests Unitaires (TU)
**Objectif**: Valider chaque fonction individuellement.

**Couverture minimale**: 80%

**Tests prioritaires**:
- `test_yolo_detector.py`: Détection YOLOv8
- `test_xai_methods.py`: Chaque méthode XAI
- `test_metrics.py`: Calcul de métriques
- `test_api_schemas.py`: Validation Pydantic

**Framework**: pytest

**Commande**:
```bash
pytest backend/tests/unit/ --cov=backend/core --cov-report=html
```

---

#### 9.1.2 Tests d'Intégration (TI)
**Objectif**: Valider l'interaction entre composants.

**Tests prioritaires**:
- `test_api_integration.py`: Endpoints API
- `test_database_integration.py`: CRUD SQLAlchemy
- `test_mlflow_integration.py`: Logging MLflow

**Commande**:
```bash
pytest backend/tests/integration/ -v
```

---

#### 9.1.3 Tests de Performance (TP)
**Objectif**: Valider les temps de réponse.

**Métriques à tester**:
- Temps d'inférence YOLOv8: < 200ms
- Génération XAI: < 2000ms
- Endpoint `/detect`: < 300ms
- Endpoint `/explain`: < 2500ms

**Outil**: pytest-benchmark

---

### 9.2 Tests Frontend

#### 9.2.1 Tests Unitaires
**Framework**: Jest + React Testing Library

**Tests prioritaires**:
- Composants UI: Button, Card, Spinner
- Hooks personnalisés
- Fonctions utilitaires

**Commande**:
```bash
npm run test
```

---

#### 9.2.2 Tests End-to-End (E2E)
**Framework**: Playwright

**Scénarios prioritaires**:

**E2E-001: Flux Complet d'Analyse**
1. Naviguer vers `/dashboard`
2. Uploader une image
3. Cliquer sur "Analyze"
4. Vérifier affichage des détections
5. Cliquer sur "Generate Explanations"
6. Vérifier affichage des XAI
7. Cliquer sur "Save Analysis"
8. Vérifier toast de confirmation

**E2E-002: Consultation de Métriques**
1. Naviguer vers `/metrics`
2. Vérifier affichage des cartes de métriques
3. Sélectionner une plage de dates
4. Vérifier mise à jour des données

**Commande**:
```bash
npx playwright test
```

---

### 9.3 Tests de Validation Métier

#### 9.3.1 Validation du Modèle
**Dataset de test**: 20% de RIAWELC (4,881 images)

**Métriques cibles**:
- mAP@0.5 ≥ 99.88%
- mAP@0.75 ≥ 98.56%
- mAP (average) ≥ 99.74%
- Precision ≥ 95%
- Recall ≥ 93%

**Script**:
```bash
python backend/scripts/evaluate.py --data DATA/data.yaml --model models/best.pt
```

---

#### 9.3.2 Validation XAI
**Objectif**: Vérifier la cohérence des explications.

**Tests manuels**:
1. Analyser 50 images de test
2. Vérifier que les heatmaps XAI couvrent les défauts
3. Calculer le consensus score moyen (cible: ≥ 0.7)
4. Vérifier que les 4 méthodes produisent des résultats

---

### 9.4 Tests d'Acceptation Utilisateur (UAT)

#### UAT-001: Facilité d'Utilisation
**Critères**:
- Un nouvel utilisateur peut effectuer une analyse en < 5 minutes
- Toutes les fonctions sont accessibles en < 3 clics

#### UAT-002: Précision Perçue
**Critères**:
- Les défauts sont correctement détectés visuellement
- Les explications XAI sont compréhensibles

#### UAT-003: Performance Perçue
**Critères**:
- L'interface est réactive (pas de lag)
- Les analyses sont rapides (< 5 secondes end-to-end)

---

## 10. Déploiement et Maintenance

### 10.1 Environnements

#### 10.1.1 Environnement de Développement
- **Backend**: Python 3.10.11 + venv
- **Frontend**: Node.js 18+ + npm
- **Database**: SQLite locale
- **GPU**: NVIDIA RTX 4050

#### 10.1.2 Environnement de Production (Local)
- **Conteneurisation**: Docker + Docker Compose
- **Backend**: Container `radikal-backend`
- **Frontend**: Container `radikal-frontend`
- **Volumes**: Persistance DB + models + uploads

---

### 10.2 Déploiement Docker

#### 10.2.1 Dockerfile Backend
```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Installation Python 3.10
RUN apt-get update && apt-get install -y python3.10 python3-pip

# Copie des fichiers
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Téléchargement du modèle
RUN python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

#### 10.2.2 Dockerfile Frontend
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copie package.json et installation
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copie du code source
COPY frontend/ .

# Build de production
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

---

#### 10.2.3 docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: radikal-backend
    ports:
      - "8000:8000"
    volumes:
      - ./DATA:/app/DATA
      - ./backend/models:/app/models
      - ./backend/uploads:/app/uploads
      - ./backend/mlruns:/app/mlruns
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    container_name: radikal-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  uploads:
  mlruns:
```

---

### 10.3 Procédure de Déploiement

#### 10.3.1 Déploiement Initial
```bash
# 1. Cloner le repository
git clone https://github.com/ZenleX-Dost/RadiKal.git
cd RadiKal

# 2. Configuration des variables d'environnement
cp .env.example .env

# 3. Build des images Docker
docker-compose build

# 4. Lancement des services
docker-compose up -d

# 5. Vérification de santé
curl http://localhost:8000/api/xai-qc/health
```

---

#### 10.3.2 Mise à Jour (Update)
```bash
# 1. Pull des derniers changements
git pull origin main

# 2. Arrêt des services
docker-compose down

# 3. Rebuild (si nécessaire)
docker-compose build

# 4. Redémarrage
docker-compose up -d

# 5. Vérification
docker-compose logs -f
```

---

### 10.4 Monitoring et Logs

#### 10.4.1 Logs Backend
**Localisation**: `backend/logs/`

**Format**:
```json
{
  "timestamp": "2025-10-21T14:30:00Z",
  "level": "INFO",
  "message": "Detection completed",
  "metadata": {
    "image_id": "img_1729521234.567",
    "num_detections": 2,
    "inference_time_ms": 145.3
  }
}
```

**Commande de consultation**:
```bash
docker logs -f radikal-backend
```

---

#### 10.4.2 Logs Frontend
**Localisation**: Console navigateur + `frontend/.next/`

**Commande**:
```bash
docker logs -f radikal-frontend
```

---

#### 10.4.3 Monitoring GPU
**Commande**:
```bash
watch -n 1 nvidia-smi
```

**Métriques à surveiller**:
- GPU Utilization: < 90%
- Memory Usage: < 5GB / 6GB
- Temperature: < 80°C

---

### 10.5 Sauvegarde et Restauration

#### 10.5.1 Sauvegarde (Backup)
**Éléments à sauvegarder**:
- Base de données SQLite: `backend/radikal.db`
- Modèles entraînés: `backend/models/`
- Images uploadées: `backend/uploads/`
- Historique MLflow: `backend/mlruns/`

**Script de sauvegarde**:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$DATE"

mkdir -p $BACKUP_DIR
cp backend/radikal.db $BACKUP_DIR/
cp -r backend/models $BACKUP_DIR/
cp -r backend/uploads $BACKUP_DIR/
cp -r backend/mlruns $BACKUP_DIR/

tar -czf backups/radikal_backup_$DATE.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

---

#### 10.5.2 Restauration (Restore)
```bash
#!/bin/bash
BACKUP_FILE=$1

tar -xzf $BACKUP_FILE -C /tmp/
cp /tmp/backup_*/radikal.db backend/
cp -r /tmp/backup_*/models backend/
cp -r /tmp/backup_*/uploads backend/
cp -r /tmp/backup_*/mlruns backend/

docker-compose restart
```

---

### 10.6 Maintenance Préventive

#### 10.6.1 Quotidienne
- ✅ Vérification des logs d'erreur
- ✅ Surveillance de l'utilisation GPU

#### 10.6.2 Hebdomadaire
- ✅ Nettoyage des images uploadées > 7 jours (optionnel)
- ✅ Vérification de l'espace disque
- ✅ Backup de la base de données

#### 10.6.3 Mensuelle
- ✅ Mise à jour des dépendances (pip, npm)
- ✅ Évaluation du modèle sur nouvelles données
- ✅ Revue des métriques de performance

---

## 11. Livrables et Jalons

### 11.1 Livrables Techniques

#### LIV-001: Code Source
- **Contenu**: Repository Git complet
- **Structure**: Backend + Frontend + Docker
- **Documentation**: README.md + commentaires inline
- **Format**: GitHub repository

#### LIV-002: Modèle Entraîné
- **Fichier**: `backend/models/best.pt`
- **Format**: PyTorch (.pt)
- **Taille**: ~22 MB
- **Métriques**: mAP@0.5 ≥ 99.88%

#### LIV-003: Dataset RIAWELC
- **Contenu**: 24,407 images + annotations YOLO
- **Structure**: `DATA/images/` + `DATA/labels/`
- **Format**: PNG 224×224 + TXT (YOLO)
- **Taille**: ~8 GB

#### LIV-004: Containers Docker
- **Images**: `radikal-backend`, `radikal-frontend`
- **Configuration**: `docker-compose.yml`
- **Registry**: Docker Hub (optionnel)

---

### 11.2 Livrables Documentaires

#### LIV-005: Documentation Technique
- **Cahier des Charges**: Ce document (CdC_Part1.md + CdC_Part2.md)
- **API Documentation**: Swagger UI à `/docs`
- **Architecture Diagram**: Diagramme d'architecture système
- **Guide de Déploiement**: Instructions complètes

#### LIV-006: Guide Utilisateur
- **Contenu**: Utilisation de l'interface web
- **Format**: PDF + Markdown
- **Sections**: Installation, Analyse d'images, Métriques, Historique

#### LIV-007: Rapport de Tests
- **Couverture**: Résultats des tests unitaires/intégration
- **Performance**: Benchmarks de temps de réponse
- **Validation**: Résultats d'évaluation du modèle

---

### 11.3 Jalons du Projet

#### Jalon 1: Proof of Concept (J+30)
**Objectifs**:
- ✅ Modèle YOLOv8s entraîné sur RIAWELC
- ✅ Détection fonctionnelle sur images de test
- ✅ mAP@0.5 ≥ 95%

**Livrables**: Notebook Jupyter + modèle .pt

---

#### Jalon 2: Backend Fonctionnel (J+60)
**Objectifs**:
- ✅ API FastAPI opérationnelle
- ✅ 6 endpoints REST implémentés
- ✅ 4 méthodes XAI fonctionnelles
- ✅ Base de données SQLite

**Livrables**: Backend complet + tests unitaires

---

#### Jalon 3: Frontend v1.0 (J+90)
**Objectifs**:
- ✅ Interface web Next.js complète
- ✅ 5 pages implémentées (Home, Dashboard, Metrics, History, Settings)
- ✅ Intégration API backend
- ✅ Gestion d'état avec Zustand

**Livrables**: Frontend complet + tests E2E

---

#### Jalon 4: Intégration Complète (J+110)
**Objectifs**:
- ✅ Backend + Frontend intégrés
- ✅ Docker Compose fonctionnel
- ✅ Tests d'intégration passés
- ✅ Performance validée (< 200ms détection)

**Livrables**: Système complet dockerisé

---

#### Jalon 5: Version Finale (J+120)
**Objectifs**:
- ✅ Documentation complète
- ✅ Tests de validation métier (mAP ≥ 99.88%)
- ✅ UAT passés
- ✅ Guide de déploiement

**Livrables**: Release v1.0 + documentation

---

### 11.4 Critères d'Acceptation Globaux

#### CA-001: Performance du Modèle
- ✅ mAP@0.5 ≥ 99.88%
- ✅ mAP@0.75 ≥ 98.56%
- ✅ mAP (average) ≥ 99.74%
- ✅ Precision ≥ 95%
- ✅ Recall ≥ 93%
- ✅ F1-Score ≥ 94%

#### CA-002: Performance Système
- ✅ Détection < 200ms (95th percentile)
- ✅ XAI génération < 2000ms (95th percentile)
- ✅ API response time < 500ms
- ✅ Frontend LCP < 2.5s

#### CA-003: Fonctionnalités
- ✅ Upload d'images fonctionnel
- ✅ Détection automatique opérationnelle
- ✅ 4 méthodes XAI disponibles
- ✅ Métriques calculées correctement
- ✅ Historique persistant
- ✅ Export PDF/Excel fonctionnel

#### CA-004: Qualité Code
- ✅ Couverture tests ≥ 80%
- ✅ Documentation complète
- ✅ Pas d'erreurs critiques
- ✅ Logs structurés

#### CA-005: Déploiement
- ✅ Docker Compose fonctionnel
- ✅ Démarrage en < 2 minutes
- ✅ Backup/Restore testés
- ✅ Guide de déploiement validé

---

## 12. Annexes

### 12.1 Glossaire

| Terme | Définition |
|-------|------------|
| **AUROC** | Area Under Receiver Operating Characteristic curve - Mesure de performance de classification |
| **Bounding Box** | Rectangle délimitant un objet détecté dans une image |
| **Consensus Score** | Score d'accord entre les 4 méthodes XAI (0-1) |
| **Grad-CAM** | Gradient-weighted Class Activation Mapping - Méthode XAI basée sur gradients |
| **IoU** | Intersection over Union - Métrique de chevauchement de bounding boxes |
| **LIME** | Local Interpretable Model-agnostic Explanations - Méthode XAI locale |
| **mAP** | Mean Average Precision - Métrique de détection d'objets |
| **RIAWELC** | Radiographic Images for Automatic Weld Defects Classification - Dataset |
| **SHAP** | SHapley Additive exPlanations - Méthode XAI basée sur théorie des jeux |
| **XAI** | Explainable AI - Intelligence artificielle explicable |
| **YOLOv8** | You Only Look Once version 8 - Modèle de détection d'objets |

---

### 12.2 Références

#### Papiers Scientifiques
1. **YOLOv8**: Ultralytics YOLO (2023) - https://github.com/ultralytics/ultralytics
2. **Grad-CAM**: Selvaraju et al. (2017) - "Grad-CAM: Visual Explanations from Deep Networks"
3. **SHAP**: Lundberg & Lee (2017) - "A Unified Approach to Interpreting Model Predictions"
4. **LIME**: Ribeiro et al. (2016) - "Why Should I Trust You?"

#### Documentation Technique
- FastAPI: https://fastapi.tiangolo.com/
- Next.js: https://nextjs.org/docs
- PyTorch: https://pytorch.org/docs/stable/index.html
- MLflow: https://mlflow.org/docs/latest/index.html

---

### 12.3 Classes de Défauts Détaillées

#### LP - Lack of Penetration (Manque de Pénétration)
**Description**: Défaut où le métal d'apport n'a pas complètement fusionné avec le métal de base.

**Caractéristiques**:
- Forme: Linéaire, continue ou discontinue
- Localisation: À la racine de la soudure
- Gravité: HAUTE (affaiblit la structure)

**Critères de détection**:
- Ligne sombre continue à la base
- Faible contraste avec le métal de base

---

#### PO - Porosity (Porosité)
**Description**: Présence de cavités gazeuses dans le métal soudé.

**Caractéristiques**:
- Forme: Circulaire ou elliptique
- Distribution: Isolée ou en grappe
- Gravité: MOYENNE à HAUTE (selon taille et densité)

**Critères de détection**:
- Taches circulaires sombres
- Diamètre variable (0.5mm à 5mm)

---

#### CR - Cracks (Fissures)
**Description**: Discontinuité linéaire causée par contraintes mécaniques ou thermiques.

**Caractéristiques**:
- Forme: Linéaire, fine
- Orientation: Longitudinale, transversale, ou en étoile
- Gravité: CRITIQUE (propagation possible)

**Critères de détection**:
- Ligne très fine et sombre
- Contraste élevé avec le métal

---

#### ND - No Defect (Aucun Défaut)
**Description**: Soudure conforme sans défaut détectable.

**Caractéristiques**:
- Texture homogène
- Pas d'anomalie visible
- Gravité: AUCUNE

---

### 12.4 Changelog

#### Version 1.0 (2025-10-21)
- ✅ Version initiale du Cahier des Charges
- ✅ Spécifications complètes backend et frontend
- ✅ Exigences fonctionnelles et non-fonctionnelles
- ✅ Plan de tests et validation
- ✅ Procédures de déploiement

---

**[FIN DU CAHIER DES CHARGES - PARTIE 2/2]**

---

## Signatures et Approbations

| Rôle | Nom | Signature | Date |
|------|-----|-----------|------|
| Chef de Projet | ZenleX-Dost | _____________ | 21/10/2025 |
| Architecte Technique | [À compléter] | _____________ | __/__/2025 |
| Responsable Qualité | [À compléter] | _____________ | __/__/2025 |

---

**Document généré le 21 Octobre 2025**  
**Dernière révision: v1.0**  
**Propriétaire: ZenleX-Dost**  
**Licence: Propriétaire - Tous droits réservés**
