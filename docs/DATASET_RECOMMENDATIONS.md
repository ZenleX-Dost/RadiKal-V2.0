# 🎯 Open-Source Dataset Recommendations for RadiKal XAI

**Updated**: October 14, 2025

---

## ⭐ **Top Recommendation: GDXray Casting Defects**

### **Why GDXray is Perfect:**
- ✅ **Real industrial X-ray images** (not synthetic)
- ✅ **6,076 images** of casting defects
- ✅ **Multiple defect types**: cracks, gas pores, shrinkage, sand inclusion
- ✅ **Well-annotated** with bounding boxes
- ✅ **Free for research** use
- ✅ **Widely used** in academic research (proven quality)
- ✅ **Perfect for XAI visualization** (clear defect regions)

### **Quick Start:**
```powershell
# Download and prepare dataset
cd backend
python scripts/download_gdxray.py --category castings --output data/gdxray

# Expected output:
# - data/gdxray/train/ (~4,253 images)
# - data/gdxray/val/ (~911 images)
# - data/gdxray/test/ (~912 images)
```

**Website**: http://dmery.sitios.ing.uc.cl/Castings/

---

## 📦 **All Recommended Datasets**

### **1. GDXray (Industrial X-Ray)** ⭐⭐⭐⭐⭐
- **Best for**: Industrial defect detection, XAI visualization
- **Size**: 19,407 images total (6,076 casting defects)
- **Categories**: Castings, Welds, Baggage, Nature, Settings
- **Format**: JPEG + XML annotations
- **License**: Free for research
- **Download**: http://dmery.sitios.ing.uc.cl/Castings/
- **Paper**: Mery et al. (2015) "GDXray: The Database of X-ray Images for Nondestructive Testing"

---

### **2. MVTec Anomaly Detection (AD)** ⭐⭐⭐⭐⭐
- **Best for**: Anomaly detection, pixel-perfect XAI
- **Size**: 5,354 high-resolution images
- **Categories**: 15 classes (textures + objects)
- **Format**: Images + pixel-level masks
- **License**: CC BY-NC-SA 4.0
- **Download**: https://www.mvtec.com/company/research/datasets/mvtec-ad
- **Paper**: Bergmann et al. (2019) "MVTec AD — A Comprehensive Real-World Dataset"

**Why it's excellent**:
- Industry standard benchmark
- Pixel-perfect annotations
- Great for segmentation-based XAI
- Very high image quality

---

### **3. Kaggle Steel Defect Detection** ⭐⭐⭐⭐
- **Best for**: Large-scale training, segmentation
- **Size**: 12,568 training + 5,506 test images
- **Categories**: 4 types of steel surface defects
- **Format**: Images + RLE encoded masks
- **License**: Competition rules (free download)
- **Download**: https://www.kaggle.com/competitions/severstal-steel-defect-detection/data

**Installation**:
```powershell
# Install Kaggle CLI
pip install kaggle

# Set up Kaggle credentials
# 1. Go to https://www.kaggle.com/account
# 2. Create API token
# 3. Place kaggle.json in ~/.kaggle/

# Download dataset
kaggle competitions download -c severstal-steel-defect-detection
```

---

### **4. NEU Surface Defect Database** ⭐⭐⭐⭐
- **Best for**: Quick testing, balanced dataset
- **Size**: 1,800 images (300 per class)
- **Categories**: 6 surface defect types
  - Rolled-in scale (RS)
  - Patches (Pa)
  - Crazing (Cr)
  - Pitted surface (PS)
  - Inclusion (In)
  - Scratches (Sc)
- **Format**: 300×200 grayscale images + bounding boxes
- **License**: Free for research
- **Download**: http://faculty.neu.edu.cn/yunhyan/NEU_surface_defect_database.html

**Why it's good**:
- Small, manageable size
- Perfect for prototyping
- Well-balanced classes
- Quick to train

---

### **5. PCB Defect Dataset (DeepPCB)** ⭐⭐⭐⭐
- **Best for**: Electronics inspection, PCB manufacturing
- **Size**: 1,500 image pairs
- **Defect types**: Open, short, mousebite, spur, pin hole, spurious copper
- **Format**: Template + defect image pairs
- **License**: Open source (MIT)
- **Download**: https://github.com/tangsanli5201/DeepPCB

**Installation**:
```powershell
git clone https://github.com/tangsanli5201/DeepPCB.git
cd DeepPCB
# Follow repository instructions
```

---

### **6. DAGM 2007 (Texture Defects)** ⭐⭐⭐
- **Best for**: Texture inspection, controlled environment
- **Size**: 10 classes, 1,000 images per class
- **Format**: Grayscale images with synthetic defects
- **License**: Free for research
- **Download**: https://conferences.mpi-inf.mpg.de/dagm/2007/prizes.html

**Why it's useful**:
- Classic benchmark
- Easy to start with
- Good for algorithm validation

---

## 🎯 **Decision Matrix**

| Dataset | Size | Real/Synthetic | XAI-Friendly | Training Time | Best Use Case |
|---------|------|----------------|--------------|---------------|---------------|
| **GDXray** | 6K | Real X-ray | ⭐⭐⭐⭐⭐ | 3-5 hrs | **Industrial defects** |
| **MVTec AD** | 5K | Real photos | ⭐⭐⭐⭐⭐ | 2-4 hrs | Anomaly detection |
| **Steel (Kaggle)** | 18K | Real photos | ⭐⭐⭐⭐ | 8-12 hrs | Large-scale training |
| **NEU Surface** | 1.8K | Real photos | ⭐⭐⭐⭐ | 1-2 hrs | Quick prototyping |
| **PCB (DeepPCB)** | 1.5K | Real photos | ⭐⭐⭐ | 1-2 hrs | Electronics inspection |
| **DAGM 2007** | 10K | Synthetic | ⭐⭐⭐ | 2-3 hrs | Algorithm testing |

---

## 🚀 **Recommended Workflow**

### **Option A: Start with GDXray (Recommended)**
```powershell
# 1. Download GDXray casting defects
cd backend
python scripts/download_gdxray.py --category castings

# 2. Update training config
# Edit configs/train_config.json:
#   "data_dir": "data/gdxray"

# 3. Train model
python scripts/train.py --config configs/train_config.json --gpu 0

# Time: ~3-5 hours
# Expected mAP: 0.70-0.85
```

### **Option B: Quick Test with NEU**
```powershell
# 1. Download manually from:
#    http://faculty.neu.edu.cn/yunhyan/NEU_surface_defect_database.html

# 2. Extract to: backend/data/neu-surface/

# 3. Convert format and train
python scripts/convert_neu_dataset.py --input data/neu-surface --output data/neu-prepared
python scripts/train.py --config configs/train_config.json --gpu 0

# Time: ~1-2 hours
# Expected mAP: 0.65-0.80
```

### **Option C: Large-Scale with Kaggle Steel**
```powershell
# 1. Download from Kaggle
kaggle competitions download -c severstal-steel-defect-detection
unzip severstal-steel-defect-detection.zip -d data/steel/

# 2. Convert segmentation masks to bounding boxes
python scripts/convert_steel_dataset.py

# 3. Train model
python scripts/train.py --config configs/train_config.json --gpu 0

# Time: ~8-12 hours
# Expected mAP: 0.75-0.90
```

---

## 📊 **Dataset Comparison**

### **For RadiKal XAI, prioritize:**
1. ✅ **Real industrial images** (not synthetic)
2. ✅ **Clear defect regions** (good for XAI heatmaps)
3. ✅ **Bounding box annotations** (for detection)
4. ✅ **Multiple defect types** (challenging problem)
5. ✅ **Reasonable size** (3K-10K images optimal)

### **GDXray Scores:**
- ✅ Real industrial X-rays (score: 10/10)
- ✅ Clear defects (score: 10/10)
- ✅ Bounding boxes (score: 10/10)
- ✅ Multiple types (score: 9/10)
- ✅ 6K images (score: 10/10)
- **Total: 49/50** ⭐⭐⭐⭐⭐

---

## 💡 **Pro Tips**

### **1. Start Small**
- Download NEU dataset first (1.8K images)
- Test your pipeline (1-2 hours training)
- Verify XAI visualizations work
- Then scale up to GDXray

### **2. Combine Datasets**
- Train on GDXray castings (6K)
- Fine-tune on your specific domain
- Transfer learning works great

### **3. Data Augmentation**
- Rotate, flip, scale images
- Add noise for robustness
- Can effectively 5x your dataset

### **4. Validation Strategy**
- Use 70/15/15 split (train/val/test)
- Keep test set separate until final evaluation
- Monitor validation mAP during training

---

## 📚 **Citation Information**

If you use these datasets, please cite:

**GDXray**:
```
@article{mery2015gdxray,
  title={GDXray: The database of X-ray images for nondestructive testing},
  author={Mery, Domingo and Riffo, Vladimir and Zscherpel, Uwe and Mondrag{\'o}n, Guillermo and Lillo, Iv{\'a}n and Zuccar, Iv{\'a}n and Lobel, Hans and Carrasco, Miguel},
  journal={Journal of Nondestructive Evaluation},
  volume={34},
  number={4},
  pages={1--12},
  year={2015}
}
```

**MVTec AD**:
```
@inproceedings{bergmann2019mvtec,
  title={MVTec AD--A comprehensive real-world dataset for unsupervised anomaly detection},
  author={Bergmann, Paul and Fauser, Michael and Sattlegger, David and Steger, Carsten},
  booktitle={CVPR},
  pages={9592--9600},
  year={2019}
}
```

---

## 🆘 **Need Help?**

- **GDXray**: Check `backend/scripts/download_gdxray.py`
- **Questions**: Open issue on GitHub
- **Documentation**: See `ACTION_PLAN.md` and `RTX4050_TRAINING_GUIDE.md`

---

**Ready to download? Run:**
```powershell
cd backend
python scripts/download_gdxray.py --category castings
```

**Happy training! 🚀**
