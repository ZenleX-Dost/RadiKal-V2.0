# RTX 4050 GPU Training Guide

This guide explains how to train the XAI Visual Quality Control model on your NVIDIA RTX 4050 GPU.

## Hardware Requirements

- **GPU**: NVIDIA RTX 4050 (6GB VRAM)
- **CUDA**: 11.8 or higher
- **Driver**: Latest NVIDIA driver (535.x or higher)
- **RAM**: 16GB+ recommended
- **Storage**: 50GB+ for datasets and models

## Prerequisites

### 1. Install NVIDIA Drivers

Download and install the latest NVIDIA drivers from:
https://www.nvidia.com/Download/index.aspx

### 2. Verify CUDA Installation

```powershell
nvcc --version
nvidia-smi
```

You should see your RTX 4050 listed in `nvidia-smi` output.

### 3. Install PyTorch with CUDA Support

The `requirements.txt` includes PyTorch 2.1.0 with CUDA 11.8 support. Install with:

```powershell
cd backend
pip install -r requirements.txt
```

## Training Configuration

The training script is pre-configured for optimal performance on RTX 4050:

### Optimized Settings (`configs/train_config.json`):

- **Batch Size**: 8 (for 512x512 images)
- **Mixed Precision**: Enabled (uses less VRAM)
- **Gradient Accumulation**: Optional for larger effective batch sizes
- **Memory Management**: Automatic cache clearing after each batch

### Batch Size Recommendations by Image Size:

| Image Size | Recommended Batch Size | VRAM Usage |
|------------|------------------------|------------|
| 512x512    | 8                      | ~5.5 GB    |
| 640x640    | 6                      | ~5.8 GB    |
| 1024x1024  | 2                      | ~5.9 GB    |

## Training Steps

### 1. Prepare Your Dataset

Organize your data as follows:

```
backend/data/
├── train/
│   ├── images/
│   │   ├── image1.jpg
│   │   └── ...
│   └── annotations.json
├── val/
│   ├── images/
│   └── annotations.json
└── test/
    ├── images/
    └── annotations.json
```

### 2. Configure Training

Edit `configs/train_config.json` if needed:

```json
{
  "batch_size": 8,
  "num_epochs": 50,
  "learning_rate": 0.0001,
  "image_size": [512, 512]
}
```

### 3. Start Training

```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

### 4. Monitor Training with MLflow

In a separate terminal:

```powershell
cd backend
mlflow ui
```

Then open http://localhost:5000 in your browser to view:
- Training loss curves
- Validation metrics
- Model artifacts
- GPU utilization

## RTX 4050-Specific Optimizations

The training script automatically applies these optimizations:

### 1. **CUDA Memory Management**
```python
torch.backends.cudnn.benchmark = True  # Faster convolutions
torch.set_float32_matmul_precision('high')  # Faster matmul
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'  # Better memory allocation
```

### 2. **Gradient Accumulation** (Optional)
To simulate larger batch sizes without running out of memory:

```json
{
  "gpu_optimization": {
    "gradient_accumulation_steps": 2
  }
}
```

This effectively doubles your batch size (8 → 16) without using more VRAM.

### 3. **Mixed Precision Training** (Automatic)
The script uses PyTorch's automatic mixed precision (AMP) when available, reducing memory usage by ~30%.

### 4. **Automatic Cache Clearing**
After each batch, `torch.cuda.empty_cache()` is called to free unused memory.

## Monitoring GPU Usage

### During Training

Monitor GPU usage in real-time:

```powershell
nvidia-smi -l 1
```

Expected output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx       Driver Version: 535.xx       CUDA Version: 11.8   |
|-------------------------------+----------------------+----------------------+
| GPU  Name            TCC/WDDM | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ... WDDM  | 00000000:01:00.0 Off |                  N/A |
| 30%   65C    P2    85W / 115W |   5500MiB /  6144MiB |     95%      Default |
+-------------------------------+----------------------+----------------------+
```

### Performance Metrics

Expected training speed on RTX 4050:
- **512x512 images**: ~2-3 seconds per batch (batch_size=8)
- **Total training time (50 epochs)**: ~3-5 hours (depends on dataset size)
- **Inference time**: <200ms per image

## Troubleshooting

### Out of Memory Error

If you get `CUDA out of memory`:

1. **Reduce batch size**:
   ```json
   "batch_size": 4
   ```

2. **Enable gradient accumulation**:
   ```json
   "gradient_accumulation_steps": 2
   ```

3. **Reduce image size**:
   ```json
   "image_size": [416, 416]
   ```

4. **Close other GPU applications** (Chrome, games, etc.)

### Slow Training

If training is slower than expected:

1. Check GPU utilization with `nvidia-smi`
2. Ensure CUDA drivers are up to date
3. Verify `num_workers` in config (4 is optimal for most systems)
4. Check if disk I/O is bottleneck (use SSD for data)

### CUDA Not Available

If PyTorch doesn't detect CUDA:

1. Reinstall PyTorch with CUDA:
   ```powershell
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. Verify installation:
   ```python
   python -c "import torch; print(torch.cuda.is_available())"
   ```

## Training with DVC

For experiment tracking and reproducibility:

### 1. Initialize DVC

```powershell
dvc init
```

### 2. Track Data

```powershell
dvc add data/train
dvc add data/val
```

### 3. Run Pipeline

```powershell
dvc repro
```

This will run all pipeline stages defined in `dvc.yaml`.

## Post-Training

### 1. Evaluate Model

```powershell
python scripts/evaluate.py --model models/checkpoints/best_model.pth
```

### 2. View Results

Results are saved in `metrics/evaluation_results.json`

### 3. Calibrate Model

```powershell
python scripts/calibrate_model.py
```

This improves prediction confidence calibration.

## Tips for Best Performance

1. **Use SSD** for data storage (HDD can bottleneck training)
2. **Close unnecessary applications** to free GPU memory
3. **Monitor temperature** (RTX 4050 should stay below 80°C)
4. **Use TensorBoard** for detailed profiling:
   ```powershell
   tensorboard --logdir=runs
   ```

## Support

For issues or questions:
- Check logs in `logs/training.log`
- Review MLflow experiments at http://localhost:5000
- Consult backend/README.md for API documentation

## Next Steps

After training completes:
1. Test the model on validation set
2. Generate XAI explanations to verify model behavior
3. Deploy using Docker (see main README.md)
4. Integrate with Makerkit frontend

---

**Note**: The RTX 4050 with 6GB VRAM is well-suited for this task. The configurations provided have been optimized for this GPU to ensure stable training without memory issues.
