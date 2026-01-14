# User Guide

Comprehensive guide to using RadiKal  V2.0 for weld defect analysis.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Image Analysis](#image-analysis)
3. [Understanding Results](#understanding-results)
4. [XAI Explanations](#xai-explanations)
5. [Batch Processing](#batch-processing)
6. [Export and Reporting](#export-and-reporting)
7. [Advanced Features](#advanced-features)

---

## Getting Started

### Accessing the Application

1. Open your web browser
2. Navigate to: http://localhost:3000
3. You'll see the RadiKal dashboard

### Interface Overview

The application consists of several main sections:

- **Dashboard**: Overview and quick stats
- **Analysis**: Single image analysis
- **Batch**: Multiple image processing
- **History**: Past analyses
- **Settings**: Configuration options

---

## Image Analysis

### Single Image Analysis

#### Step 1: Upload Image

1. Click on "Analysis" in the navigation menu
2. Click "Upload Image" or drag and drop a radiographic image
3. Supported formats: PNG, JPG, JPEG
4. Maximum file size: 10MB

#### Step 2: Select Analysis Mode

Choose from three analysis modes:

**Classification Mode** (Fastest)
- Uses YOLOv8 only
- Identifies defect type
- Processing time: ~50ms
- Use when: You only need defect classification

**Hybrid Mode** (Recommended)
- Uses both YOLOv8 + SAM2
- Full classification and segmentation
- Processing time: ~2.3s
- Use when: You need complete defect analysis

**Segmentation Mode**
- Uses SAM2 only
- Pixel-level defect localization
- Processing time: ~2s
- Use when: You need precise defect boundaries

#### Step 3: Select XAI Methods

Choose which explainability methods to apply:

- **Grad-CAM**: Fast, intuitive visual explanations
- **SHAP**: Game-theory based explanations
- **LIME**: Local explanations
- **Integrated Gradients**: Attribution-based explanations
- **All**: Apply all methods (slower but comprehensive)

#### Step 4: Configure Segmentation (Hybrid/Segmentation Mode)

If using segmentation, select guidance strategy:

- **Auto**: Automatic detection (recommended)
- **Center**: Assumes defect at image center
- **Grid**: Thorough grid-based search

#### Step 5: Analyze

Click "Analyze Image" to start processing.

---

## Understanding Results

### Classification Results

**Predicted Class**
- Defect type: LP (Lack of Penetration), PO (Porosity), CR (Cracks), or ND (No Defect)
- Full name provided for clarity

**Confidence Score**
- Range: 0-100%
- Higher is better
- >90%: High confidence
- 70-90%: Moderate confidence
- <70%: Low confidence (review recommended)

**Class Probabilities**
- Probability distribution across all 4 classes
- Sum equals 100%
- Shows alternative possibilities

### Segmentation Results (Hybrid/Segmentation Mode)

**Defect Mask**
- Color overlay showing exact defect location
- Pixel-level precision

**Bounding Box**
- Rectangle around defect area
- Format: [x, y, width, height]

**Coverage Percentage**
- Percentage of image covered by defect
- Indicates defect severity

**Centroid**
- Center point of defect
- Format: [x, y] coordinates

**Number of Segments**
- Count of distinct defect regions
- Most defects have 1 segment
- Multiple segments may indicate multiple defects

---

## XAI Explanations

### Viewing Explanations

After analysis, click the "XAI Explanations" tab to view:

1. **Heatmap Overlay**: Visual explanation showing important regions
2. **Method Details**: Information about the XAI method used
3. **Confidence Score**: How reliable the explanation is

### Understanding XAI Methods

#### Grad-CAM (Gradient-weighted Class Activation Mapping)

**What it shows**: Regions the model "looked at" for classification

**How to interpret**:
- Red/Warm colors: High importance
- Blue/Cool colors: Low importance
- Focus should be on defect area

**Best for**: Quick visual confirmation

**Speed**: Fast (~150ms)

#### SHAP (SHapley Additive exPlanations)

**What it shows**: Pixel contributions to the prediction

**How to interpret**:
- Positive values: Pixels supporting the prediction
- Negative values: Pixels contradicting the prediction
- Magnitude indicates strength

**Best for**: Detailed analysis

**Speed**: Slow (~850ms)

#### LIME (Local Interpretable Model-agnostic Explanations)

**What it shows**: Local explanation around the prediction

**How to interpret**:
- Highlighted regions show important areas
- Works by testing perturbations

**Best for**: Understanding specific predictions

**Speed**: Medium (~500ms)

#### Integrated Gradients

**What it shows**: Attribution of pixels to prediction

**How to interpret**:
- Shows accumulated gradients
- More precise than Grad-CAM
- Similar visualization to SHAP

**Best for**: Research and detailed analysis

**Speed**: Medium (~400ms)

### Consensus Score

When multiple XAI methods are used:

- **Consensus Score**: Agreement between methods (0-1)
- >0.85: High agreement
- 0.70-0.85: Moderate agreement
- <0.70: Low agreement (investigate further)

---

## Batch Processing

### Processing Multiple Images

#### Step 1: Navigate to Batch Processing

Click "Batch" in the navigation menu

#### Step 2: Upload Images

- Drag and drop multiple images (up to 10)
- Or click "Upload Images" to select files
- Progress bar shows upload status

#### Step 3: Configure Analysis

- **Analysis Mode**: Choose classification, hybrid, or segmentation
- **XAI Methods**: Select which methods to apply
- **Concurrent Processing**: Number of images to process simultaneously (default: 3)

#### Step 4: Start Batch Analysis

1. Click "Start Batch Analysis"
2. Monitor progress in real-time
3. Each image shows individual progress
4. Overall progress displayed at top

#### Step 5: Review Results

- Click on each image to view detailed results
- Compare results across images
- Export all results when complete

### Batch Statistics

After processing, view:

- Total images processed
- Success/failure count
- Average confidence
- Defect distribution
- Processing time

---

## Export and Reporting

### Export Options

#### PDF Export

- **Includes**:
  - Original images
  - Analysis results
  - XAI visualizations
  - Metadata and timestamps
  - Summary statistics

- **Customization**:
  - Page size (A4, Letter)
  - Orientation (Portrait, Landscape)
  - Include/exclude sections
  - Branding options

#### Excel Export

- **Includes**:
  - Tabular data for all analyses
  - Classification results
  - Segmentation metrics
  - XAI scores
  - Timestamps and metadata

- **Features**:
  - Filterable columns
  - Sortable data
  - Charts and graphs
  - Pivot table ready

### Exporting Results

1. Select analyses to export (single or multiple)
2. Click "Export" button
3. Choose format (PDF or Excel)
4. Select included content
5. Click "Generate Export"
6. Download when ready

---

## Advanced Features

### Real-time Notifications

Enable browser notifications for:

- Analysis completion
- Batch processing updates
- System alerts
- Error notifications

**To enable**:
1. Click bell icon in header
2. Allow browser notifications
3. Configure notification preferences in Settings

### Advanced Settings

Access via Settings > Advanced

**Notification Preferences**
- Enable/disable per notification type  
- Sound alerts
- Desktop notifications

**API Settings**
- Timeout duration
- Retry attempts
- Cache configuration

**Performance Tuning**
- GPU memory allocation
- Concurrent analysis limit
- Image preprocessing options

**Security Settings**
- Multi-factor authentication
- Audit logging
- Session timeout

### Keyboard Shortcuts

- `Ctrl/Cmd + U`: Upload image
- `Ctrl/Cmd + Enter`: Start analysis
- `Ctrl/Cmd + B`: Batch processing
- `Ctrl/Cmd + E`: Export results
- `Ctrl/Cmd + H`: View history
- `?`: Show keyboard shortcuts

### Mobile Support

RadiKal is responsive and works on tablets and mobile devices:

- Touch-friendly interface
- Optimized layouts
- All core features available
- Reduced visualizations for performance

---

## Best Practices

### Image Quality

For best results:

- **Resolution**: 224x224 or higher
- **Format**: PNG preferred (lossless)
- **Quality**: High quality, minimal compression
- **Lighting**: Consistent illumination
- **Focus**: Sharp, clear images

### Analysis Mode Selection

- **Quick checks**: Use Classification mode
- **Detailed analysis**: Use Hybrid mode
- **Research/validation**: Use all XAI methods
- **Batch processing**: Use Classification mode for speed

### Interpreting Low Confidence

If confidence < 70%:

1. Check image quality
2. Review XAI explanations
3. Consider manual inspection
4. Run multiple XAI methods
5. Check for edge cases

### Data Management

- Regularly export historical data
- Archive old analyses
- Monitor storage usage
- Backup important results

---

## Troubleshooting

### Common Issues

**Image won't upload**
- Check file size (<10MB)
- Verify format (PNG, JPG, JPEG)
- Try different browser
- Clear browser cache

**Analysis takes too long**
- Use Classification mode instead of Hybrid
- Reduce number of XAI methods
- Check network connection
- Ensure backend is running

**Low confidence scores**
- Verify image quality
- Check for unusual lighting
- Ensure proper defect visibility
- Review training data coverage

**Segmentation not working**
- Verify SAM2 model is loaded
- Check GPU availability
- Try different guidance strategy
- Reduce image size

For more detailed troubleshooting, see the [Troubleshooting Guide](troubleshooting.md).

---

## Getting Help

- **Documentation**: This guide and other docs
- **API Reference**: [API Reference](api-reference.md)
- **Technical Issues**: [Troubleshooting](troubleshooting.md)
- **Support**: Open GitHub issue or contact support

---

## Next Steps

- Explore the [API Reference](api-reference.md) for integration
- Learn about [SAM2 Integration](sam2-guide.md) for advanced segmentation
- Read about [XAI Methods](xai-methods.md) for deeper understanding
- Review [Architecture](architecture.md) for system design
