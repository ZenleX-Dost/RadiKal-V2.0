# Consensus Score Implementation

## Overview
The consensus score is now properly implemented and displayed in the RadiKal application. It represents the agreement level between different XAI (Explainable AI) methods when multiple methods are used for analysis.

## What is Consensus Score?

The consensus score quantifies how much the different XAI explanation methods (Grad-CAM, LIME, SHAP) agree on which regions of the image are important for the prediction. A higher consensus score (closer to 1.0 or 100%) means the methods are in strong agreement, while a lower score indicates disagreement.

**Important**: The consensus score is only meaningful when **multiple XAI methods successfully generate heatmaps**. If only one method works (e.g., only Grad-CAM), the consensus score will be 1.0 (100%) by default since there's nothing to compare against.

### How Multiple Methods Enable Real Consensus

For a true consensus calculation:
1. **Grad-CAM** - Uses gradient information from the model's convolutional layers
2. **LIME** - Uses superpixel perturbations to identify important regions
3. **SHAP** - Uses gradient × input attribution to approximate Shapley values

Each method must:
- Successfully generate an explanation
- Produce a normalized heatmap (H, W) array
- Be added to the `heatmaps_for_aggregation` dictionary

The consensus score is then calculated by comparing these heatmaps pairwise.

### Calculation Methods

The consensus score can be calculated using three different metrics:

1. **Correlation** (default): Measures the average pairwise correlation between heatmaps
2. **IoU (Intersection over Union)**: Measures overlap of binarized heatmaps
3. **Dice Coefficient**: Similar to IoU but uses a different formula

## Implementation Details

### Backend Changes

#### 1. `backend/core/xai/classification_explainer.py`
- **Line ~369-397**: Modified LIME to extract heatmap using `generate_heatmap()` method
  - Now adds LIME heatmap to `heatmaps_for_aggregation` dictionary
  - Generates overlay for display using Grad-CAM's overlay function
- **Line ~399-437**: Modified SHAP to extract heatmap using `generate_heatmap()` method
  - Now adds SHAP heatmap to `heatmaps_for_aggregation` dictionary
  - Generates overlay for display
- **Line ~439-454**: Modified aggregation logic to compute real consensus score
  - Now calls `self._aggregator.compute_consensus_score()` with correlation method
  - Returns actual agreement between XAI methods instead of just using confidence

**Critical Fix**: Previously, only Grad-CAM's heatmap was added to aggregation, so consensus was always 100%. Now all three methods contribute their heatmaps when they succeed.

```python
# LIME now extracts heatmap for aggregation
lime_heatmap = self.lime.generate_heatmap(
    original_image,
    target_class=target_class,
    normalize=True
)
heatmaps_for_aggregation['lime'] = lime_heatmap

# SHAP now extracts heatmap for aggregation
shap_heatmap = self.shap_explainer.generate_heatmap(
    img_tensor,
    target_class=target_class,
    normalize=True
)
heatmaps_for_aggregation['shap'] = shap_heatmap

# Compute real consensus score from all methods
consensus_score = self._aggregator.compute_consensus_score(
    heatmaps_for_aggregation,
    method='correlation'
)
```

#### 2. `backend/api/routes.py`
- **Line ~546-551**: Updated validation logic
- Removed check that replaced `0.0` consensus scores with confidence
- Now only replaces `None` or `NaN` values (0.0 is a valid low consensus score)

```python
# Only replace consensus_score if it's None or NaN (not if it's 0.0, which is valid)
if consensus_score is None or (isinstance(consensus_score, float) and math.isnan(consensus_score)):
    consensus_score = explanation_result['prediction']['confidence']
```

#### 3. `backend/core/xai/aggregator.py`
- Already had `compute_consensus_score()` method implemented
- Computes pairwise correlations between normalized heatmaps
- Returns score in range [0, 1] where higher = better agreement

### Frontend Changes

#### 1. `frontend-makerkit/apps/web/app/home/analysis/page.tsx`
- **Line ~635-650**: Added third metric card for Consensus Score
- Changed from 2-column to 3-column grid layout
- Shows consensus score with purple styling and "XAI Agreement" label
- **New**: Displays number of methods used in consensus calculation

```tsx
<p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
  {explanationResult.explanations?.length > 1 
    ? `Agreement across ${explanationResult.explanations.length} methods` 
    : 'Single method (no comparison)'}
</p>
```

#### 2. `frontend-makerkit/apps/web/components/XAIExplanations.tsx`
- **Line ~113-127**: Added Consensus Score to Advanced Details section
- Shows alongside Model Confidence, Computation Time, and Analysis ID
- **New**: Shows "(X methods)" or "(single method)" indicator

```tsx
<p className="text-gray-600">
  {(explanation.consensus_score * 100).toFixed(2)}%
  {explanation.explanations?.length > 1 && (
    <span className="text-xs text-gray-500 ml-2">
      ({explanation.explanations.length} methods)
    </span>
  )}
  {explanation.explanations?.length === 1 && (
    <span className="text-xs text-gray-500 ml-2">
      (single method)
    </span>
  )}
</p>
```

#### 3. `frontend-makerkit/apps/web/components/SegmentationResults.tsx`
- **Line ~95-107**: Added Consensus Score card to SAM2 segmentation results
- 4th metric card with green styling showing analysis agreement
- Appears alongside Segments Found, Coverage, and Centroid

```tsx
<div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border-2 border-green-200 dark:border-green-800">
  <div className="flex items-center gap-3 mb-2">
    <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
    <p className="text-xs font-semibold text-green-700 dark:text-green-300 uppercase">Consensus Score</p>
  </div>
  <p className="text-3xl font-bold text-green-900 dark:text-green-100">
    {((hybridResult.consensus_score || 0) * 100).toFixed(1)}%
  </p>
  <p className="text-xs text-green-600 dark:text-green-400 mt-1">Analysis agreement</p>
</div>
```

## Where Consensus Score Appears

The consensus score is now displayed in three locations:

1. **XAI Analysis Results Page** (`/home/analysis`)
   - Main metrics section (3-column layout)
   - Shows Method, Confidence, and Consensus Score

2. **XAI Explanations Component** (Advanced Details)
   - Expandable section with detailed metrics
   - Shows Model Confidence, Consensus Score, Computation Time, Analysis ID

3. **SAM2 Segmentation Results**
   - When using hybrid analysis mode
   - Shows alongside segmentation metrics

## Interpreting Consensus Scores

| Score Range | Interpretation | Action |
|-------------|----------------|--------|
| 90-100% | Excellent agreement | High confidence in explanation |
| 70-89% | Good agreement | Reliable explanation |
| 50-69% | Moderate agreement | Review carefully |
| Below 50% | Poor agreement | Use caution, methods disagree |

### When Consensus is Calculated

- **Multi-method analysis**: When using "All Methods" and **multiple methods succeed**
  - Requires at least 2 of: Grad-CAM, LIME, SHAP
  - Each method must successfully generate a heatmap
  - Common scenario: Only Grad-CAM works → consensus = 100% (single method)
  - Real consensus: Grad-CAM + LIME + SHAP all work → actual agreement calculated
- **Single method**: Returns 1.0 (100%) as there's nothing to compare
- **No XAI methods**: Falls back to model confidence

### Ensuring Real Consensus Scores

For meaningful consensus results, you need to ensure LIME and SHAP dependencies are installed:

```bash
# Install LIME dependencies
pip install lime scikit-learn scikit-image

# Install SHAP dependencies  
pip install shap

# Verify installation
python -c "import lime; import shap; print('All XAI methods available')"
```

If dependencies are missing:
- LIME will show: `'LIME not available - sklearn/lime dependencies missing'`
- SHAP will show: `'SHAP not available - shap dependency missing'`
- Consensus will default to 100% (only Grad-CAM works)

## Testing

Run the existing tests to verify consensus calculation:

```bash
cd backend
pytest tests/test_xai.py::test_consensus_score_correlation
pytest tests/test_xai.py::test_consensus_score_iou
pytest tests/test_xai.py::test_consensus_score_dice
```

## Usage Example

1. Upload a radiographic weld image
2. Select "XAI Heatmaps" mode
3. Choose "All Methods" to use Grad-CAM, LIME, and SHAP
4. The consensus score will show how much these methods agree on the defect location
5. High consensus (>80%) = all methods highlight similar regions
6. Low consensus (<50%) = methods disagree, investigate further

## Technical Notes

- Consensus uses normalized heatmaps for fair comparison
- Correlation method is default as it's most robust
- Score is computed in `XAIAggregator.compute_consensus_score()`
- Backend computes score once during aggregation
- Frontend displays pre-computed value from API response

## References

- Implementation: `backend/core/xai/aggregator.py` lines 104-133
- Tests: `backend/tests/test_xai.py` lines 216-260
- Type definitions: `frontend-makerkit/apps/web/types/index.ts` lines 91, 213
