Write-Host "==================================="
Write-Host "RadiKal Model Training"
Write-Host "==================================="
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..."
& "C:\Users\Amine EL-Hend\Documents\GitHub\RadiKal\venv\Scripts\Activate.ps1"

# Change to backend directory
Set-Location "C:\Users\Amine EL-Hend\Documents\GitHub\RadiKal\backend"

# Start training
Write-Host ""
Write-Host "Starting training..."
Write-Host "Dataset: RIAWELC (24,407 images)"
Write-Host "Epochs: 50"
Write-Host "Batch Size: 8"
Write-Host "Expected Duration: 4-6 hours"
Write-Host ""
Write-Host "==================================="
Write-Host ""

# Run training
python scripts/train.py --data_dir data/riawelc_coco --epochs 50 --batch_size 8 --output_dir models/checkpoints

Write-Host ""
Write-Host "Training completed!"
