# XAI Methods

Comprehensive guide to Explainable AI (XAI) methods in RadiKal V2.0.

## Overview

RadiKal V2.0 implements four state-of-the-art XAI methods to provide transparent, interpretable insights into model predictions:

1. **Grad-CAM** - Gradient-weighted Class Activation Mapping
2. **SHAP** - SHapley Additive exPlanations
3. **LIME** - Local Interpretable Model-agnostic Explanations
4. **Integrated Gradients** - Attribution-based explanations

---

## Why Explainability Matters

### Industry Requirements

- **Regulatory Compliance**: Many industries require explainable AI decisions
- **Trust Building**: Stakeholders can understand and trust model predictions
- **Error Detection**: Identify when model focuses on wrong features
- **Model Improvement**: Understand model behavior for refinement

### Use Cases

- Verify defect detection reasoning
- Compare multiple explanation methods
- Build confidence in automated decisions
- Understand edge cases and failures

---

## Grad-CAM

### Overview

Gradient-weighted Class Activation Mapping (Grad-CAM) visualizes which regions of an image are important for a prediction.

### How It Works

1. Extract feature maps from last convolutional layer
2. Compute gradients of target class with respect to feature maps
3. Weight feature maps by gradient importance
4. Generate heatmap showing important regions

### Interpretation

- **Red/Hot colors**: High importance (model focused here)
- **Blue/Cool colors**: Low importance (model ignored this)
- **Expected**: Focus should align with defect location

### Characteristics

- **Speed**: Very fast (~150ms)
- **Accuracy**: Good for initial insights
- **Use Case**: Quick visual confirmation

### Code Example

```python
from core.xai.gradcam import GradCAM

gradcam = GradCAM(model)
heatmap = gradcam.generate(image, target_class=0)  # LP class
```

### API Usage

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=gradcam" \
  -F "file=@image.png"
```

---

## SHAP

### Overview

SHapley Additive exPlanations (SHAP) provides game-theory based explanations showing each pixel's contribution to the prediction.

### How It Works

1. Based on Shapley values from cooperative game theory
2. Computes marginal contribution of each feature (pixel)
3. Ensures fair attribution across all features
4. Produces additive feature importance

### Interpretation

- **Positive values**: Pixels supporting the prediction
- **Negative values**: Pixels contradicting the prediction
- **Magnitude**: Strength of contribution

### Characteristics

- **Speed**: Slow (~850ms)
- **Accuracy**: Very high, theoretically grounded
- **Use Case**: Detailed analysis, research

### Code Example

```python
from core.xai.shap_explainer import SHAPExplainer

shap = SHAPExplainer(model)
explanation = shap.explain(image, target_class=0)
```

### API Usage

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=shap" \
  -F "file=@image.png"
```

### Advantages

- Theoretically sound (Shapley values)
- Consistent and accurate
- Handles feature interactions

### Disadvantages

- Computationally expensive
- Slower than other methods
- May be overkill for simple cases

---

## LIME

### Overview

Local Interpretable Model-agnostic Explanations (LIME) explains predictions by approximating the model locally with an interpretable model.

### How It Works

1. Generate perturbed versions of input image
2. Get model predictions for perturbed images
3. Train simple linear model on perturbations
4. Use linear model to explain original prediction

### Interpretation

- **Highlighted regions**: Important for prediction
- **Segmented areas**: LIME works with superpixels
- **Local explanation**: Valid only for this specific prediction

### Characteristics

- **Speed**: Medium (~500ms)
- **Accuracy**: Good for local explanations
- **Use Case**: Understanding specific predictions

### Code Example

```python
from core.xai.lime_explainer import LIMEExplainer

lime = LIMEExplainer(model)
explanation = lime.explain(image, num_samples=1000)
```

### API Usage

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=lime" \
  -F "file=@image.png"
```

### Advantages

- Model-agnostic (works with any model)
- Intuitive superpixel-based explanations
- Good for local understanding

### Disadvantages

- Results can vary between runs
- Approximation may not be perfect
- Slower than Grad-CAM

---

## Integrated Gradients

### Overview

Integrated Gradients (IG) attributes the prediction to input features by integrating gradients along a path from a baseline to the input.

### How It Works

1. Define baseline image (usually black/zero)
2. Create interpolated images from baseline to input
3. Compute gradients at each interpolation step
4. Integrate gradients to get attribution

### Interpretation

- **Attribution scores**: How much each pixel contributed
- **Positive/negative**: Support or contradict prediction
- **Accumulated gradients**: Shows full path of contribution

### Characteristics

- **Speed**: Medium (~400ms)
- **Accuracy**: High, mathematically principled
- **Use Case**: Research, detailed analysis

### Code Example

```python
from core.xai.integrated_gradients import IntegratedGradientsExplainer

ig = IntegratedGradientsExplainer(model)
attribution = ig.explain(image, target_class=0, steps=50)
```

### API Usage

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=ig" \
  -F "file=@image.png"
```

### Advantages

- Theoretically sound (axioms satisfied)
- No hyperparameters
- Complete attribution

### Disadvantages

- Requires choosing baseline
- Slower than Grad-CAM
- Less intuitive than some methods

---

## Consensus Scoring

### Overview

When multiple XAI methods are used, RadiKal computes a consensus score measuring agreement between methods.

### How It Works

1. Generate heatmaps from all methods
2. Normalize heatmaps to [0, 1]
3. Compute correlation between heatmaps
4. Average correlations for consensus score

### Interpretation

- **>0.85**: High agreement (confident explanation)
- **0.70-0.85**: Moderate agreement (review recommended)
- **<0.70**: Low agreement (investigate further)

### Use Cases

- Validate explanation reliability
- Identify uncertain predictions
- Combine multiple viewpoints

### Code Example

```python
from core.xai.consensus import compute_consensus

heatmaps = [gradcam_heatmap, shap_heatmap, lime_heatmap, ig_heatmap]
consensus_score = compute_consensus(heatmaps)
aggregated_heatmap = aggregate_heatmaps(heatmaps)
```

---

## Comparison Matrix

| Method | Speed | Accuracy | Theoretical | Use Case |
|--------|-------|----------|-------------|----------|
| Grad-CAM | Fast (~150ms) | Good | No | Quick checks |
| SHAP | Slow (~850ms) | Excellent | Yes | Detailed analysis |
| LIME | Medium (~500ms) | Good | No | Local explanations |
| Integrated Gradients | Medium (~400ms) | Excellent | Yes | Research |

---

## Best Practices

### Method Selection

**For quick validation**:
- Use Grad-CAM only

**For important decisions**:
- Use Grad-CAM + SHAP
- Check consensus score

**For research/audit**:
- Use all four methods
- Analyze consensus and disagreements

### Interpreting Results

1. **Check focus regions**: Should align with defect
2. **Compare methods**: Multiple methods should agree
3. **Review outliers**: Low consensus needs investigation
4. **Validate reasoning**: Does explanation make sense?

### Common Pitfalls

- **Over-reliance on single method**: Always cross-validate
- **Ignoring low consensus**: Signals uncertainty
- **Misinterpreting heatmaps**: Red doesn't always mean "defect"
- **Not considering context**: Explanations are approximate

---

## API Integration

### Request All Methods

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=gradcam,shap,lime,ig" \
  -F "file=@image.png"
```

### Response

```json
{
  "image_id": "uuid",
  "classification": {
    "predicted_class_name": "LP",
    "confidence": 0.95
  },
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "...",
      "confidence_score": 0.92,
      "computation_time_ms": 150
    },
    {
      "method": "shap",
      "heatmap_base64": "...",
      "confidence_score": 0.88,
      "computation_time_ms": 850
    },
    {
      "method": "lime",
      "heatmap_base64": "...",
      "confidence_score": 0.85,
      "computation_time_ms": 500
    },
    {
      "method": "ig",
      "heatmap_base64": "...",
      "confidence_score": 0.87,
      "computation_time_ms": 400
    }
  ],
  "aggregated_heatmap": "...",
  "consensus_score": 0.88
}
```

---

## Frontend Visualization

### Display Heatmaps

```typescript
{explanations.map(exp => (
  <div key={exp.method}>
    <h3>{exp.method.toUpperCase()}</h3>
    <img src={`data:image/png;base64,${exp.heatmap_base64}`} />
    <p>Confidence: {(exp.confidence_score * 100).toFixed(1)}%</p>
    <p>Time: {exp.computation_time_ms}ms</p>
  </div>
))}
```

### Show Consensus

```typescript
<div className={`consensus ${
  consensusScore > 0.85 ? 'high' : 
  consensusScore > 0.70 ? 'medium' : 'low'
}`}>
  <p>Consensus Score: {(consensusScore * 100).toFixed(1)}%</p>
</div>
```

---

## Advanced Topics

### Custom Baselines

For Integrated Gradients:

```python
# Black baseline (default)
baseline = np.zeros_like(image)

# Mean baseline
baseline = np.mean(image) * np.ones_like(image)

# Blur baseline
from scipy.ndimage import gaussian_filter
baseline = gaussian_filter(image, sigma=10)
```

### Target Class Selection

```python
# Explain predicted class (default)
explanation = explainer.explain(image)

# Explain specific class
explanation = explainer.explain(image, target_class=1)  # PO class

# Explain all classes
for class_idx in range(4):
    explanation = explainer.explain(image, target_class=class_idx)
```

### Batch Explanations

```python
# Multiple images
images = [img1, img2, img3]
explanations = [explainer.explain(img) for img in images]

# Aggregate across batch
avg_heatmap = np.mean([exp.heatmap for exp in explanations], axis=0)
```

---

## Performance Optimization

### Caching

```python
# Cache explainer instances
_gradcam_cache = {}

def get_gradcam(model_path):
    if model_path not in _gradcam_cache:
        _gradcam_cache[model_path] = GradCAM(load_model(model_path))
    return _gradcam_cache[model_path]
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

def explain_all(image, methods=['gradcam', 'shap', 'lime', 'ig']):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            method: executor.submit(explainers[method].explain, image)
            for method in methods
        }
        return {method: future.result() for method, future in futures.items()}
```

---

## Research and References

### Papers

- **Grad-CAM**: Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization" (2017)
- **SHAP**: Lundberg & Lee, "A Unified Approach to Interpreting Model Predictions" (2017)
- **LIME**: Ribeiro et al., "Why Should I Trust You?: Explaining the Predictions of Any Classifier" (2016)
- **Integrated Gradients**: Sundararajan et al., "Axiomatic Attribution for Deep Networks" (2017)

### Additional Resources

- [Christoph Molnar's Interpretable ML Book](https://christophm.github.io/interpretable-ml-book/)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [Captum Library](https://captum.ai/)

---

## Troubleshooting

### Heatmaps Look Random

**Possible causes**:
- Model not trained properly
- Image preprocessing issues
- Wrong target class

**Solutions**:
1. Verify model performance
2. Check image normalization
3. Use correct target class

### Low Consensus Score

**Causes**:
- Model uncertainty
- Complex prediction
- Edge case

**Actions**:
1. Review image quality
2. Check prediction confidence
3. Manual inspection recommended

### Methods Taking Too Long

**Solutions**:
1. Use only Grad-CAM for speed
2. Reduce LIME samples parameter
3. Reduce IG steps parameter
4. Process on GPU

---

## Support

For XAI-related questions:

1. Review this guide
2. Check [API Reference](api-reference.md)
3. See [Troubleshooting Guide](troubleshooting.md)
4. Open GitHub issue with example
