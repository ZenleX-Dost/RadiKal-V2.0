#  RadiKal XAI - Operator Quick Start Guide

## What is XAI (Explainable AI)?

**XAI shows you WHERE the defects are and WHY the AI made its decision.**

Instead of just saying "This weld has porosity," RadiKal now shows you:
-  **Where** the porosity is located (highlighted in red on the image)
-  **How confident** the AI is (percentage score)
-  **What to do** next (repair, inspect further, or approve)

---

##  How to Use RadiKal XAI

### Step 1: Upload Your Radiographic Image

1. Open RadiKal application at http://localhost:3000
2. Click "Upload Image" button
3. Select your weld radiograph (JPG or PNG format)
4. Click "Analyze"

### Step 2: View Classification Result

You'll see:
```
┌─────────────────────────────────────────┐
│ Classification: Porosity (PO)           │
│ Confidence: 89.2%                       │
│ Severity: MEDIUM                      │
└─────────────────────────────────────────┘
```

### Step 3: Check the Heatmap

The **Grad-CAM heatmap** shows where the AI detected the defect:

- 🔴 **Red areas**: High confidence (defect is here!)
- 🟡 **Yellow areas**: Medium confidence
- 🔵 **Blue areas**: Low confidence (probably okay)

### Step 4: Read the Location Description

Example:
```
📍 Location: Primary defect in central region (coverage: 8.5%)
```

This tells you:
- **Where**: Central part of the weld
- **How much**: Covers 8.5% of the image area

### Step 5: Follow the Recommendation

Based on severity, you'll get one of these:

**⚠️ CRITICAL** (Lack of Penetration, Cracks):
```
This weld requires immediate attention.
Recommend rejection and repair according to 
welding procedure specifications.
```
→ **Action**: Mark for rejection and repair

**⚡ MEDIUM** (Porosity):
```
Assess defect density and size against 
acceptance criteria. May require further 
evaluation or repair depending on standards.
```
→ **Action**: Measure and compare to standards

**✅ ACCEPTABLE** (No Defect):
```
Weld meets quality standards.
Proceed with production or final inspection.
```
→ **Action**: Approve for next stage

---

##  Understanding the Defect Types

| Code | Name | What It Means | Severity |
|------|------|---------------|----------|
| **LP** | Lack of Penetration | Weld didn't fuse completely at the root | 🔴 CRITICAL |
| **PO** | Porosity | Small gas bubbles trapped in the weld | 🟡 MEDIUM |
| **CR** | Cracks | Linear breaks in the weld metal | 🔴 CRITICAL |
| **ND** | No Defect | Weld is acceptable | 🟢 ACCEPTABLE |

---

##  Reading the Visualization Panel

The XAI system generates a panel showing:

### Left Side: Original Image
- Your radiographic image as uploaded
- No modifications

### Right Side: Defect Localization (Grad-CAM)
- **Red highlight**: Where the AI thinks the defect is
- **Intensity**: Brighter red = higher confidence

### Bottom Info:
```
Classification: Porosity (PO)
Confidence: 89.2%
Severity: MEDIUM
Location: Primary defect in central region (coverage: 8.5%)
```

### Probability Bars:
```
LP: ██░░░░░░░░░░░░░░░░░░  5.2%
PO: ████████████████████████████████████  89.2%  ← Predicted
CR: █░░░░░░░░░░░░░░░░░░░  3.1%
ND: █░░░░░░░░░░░░░░░░░░░  2.5%
```

---

## ✅ Quality Assurance Workflow

### For Inspectors:

1. **Upload radiograph** → RadiKal analyzes image
2. **Check heatmap** → Verify highlighted regions match visual inspection
3. **Read confidence** → If >80%, trust the AI; if <60%, review manually
4. **Follow recommendation** → Take appropriate action
5. **Log decision** → Record in quality management system

### For Welding Supervisors:

1. **Review batch results** → Check for patterns (e.g., all LP defects in one area)
2. **Monitor trends** → Are defect rates increasing?
3. **Take corrective action** → Adjust welding parameters if needed
4. **Train welders** → Show them the heatmaps to understand common issues

---

##  Tips for Best Results

### ✅ DO:
- Use high-quality radiographic images (clear, well-exposed)
- Upload images in standard radiography format (JPG, PNG)
- Review heatmaps to understand AI reasoning
- Cross-check critical defects manually

### ❌ DON'T:
- Rely solely on AI for critical decisions (always verify)
- Use blurry or poorly exposed images
- Ignore low-confidence predictions (<50%)
- Skip manual inspection for CRITICAL severity defects

---

##  Troubleshooting

### Issue: Heatmap shows uniform color (all blue or all red)

**Possible Causes**:
- Image quality too low
- Unusual radiograph angle
- Defect type not in training data

**Solution**: Review image manually and retake radiograph if needed

### Issue: AI misclassifies defect

**Example**: Says "No Defect" but you see porosity

**Possible Causes**:
- Defect is very minor (below detection threshold)
- Unusual defect appearance
- Model needs retraining

**Solution**: 
1. Check confidence score (if low, trust your judgment)
2. Mark for manual review
3. Report to system administrator for model improvement

### Issue: Low confidence (<50%)

**What It Means**: AI is uncertain

**Solution**: 
- Always inspect manually
- Consider retaking radiograph
- Get second opinion from supervisor

---

##  Training Resources

### For New Operators:

1. **Watch tutorial video** (coming soon)
2. **Practice with test images** in the `examples/` folder
3. **Compare AI results** with your visual inspection
4. **Learn from feedback** when AI is correct vs. incorrect

### Understanding Confidence Scores:

- **90-100%**: Very high confidence - AI is almost certain
- **70-90%**: High confidence - AI is confident but verify critical defects
- **50-70%**: Medium confidence - Double-check manually
- **Below 50%**: Low confidence - AI is guessing, inspect manually

---

##  Example Cases

### Case 1: Clear Porosity Detection
```
Image: weld_sample_001.jpg
Classification: Porosity (PO)
Confidence: 92.5%
Location: Upper-left region (coverage: 6.2%)
Heatmap: Strong red highlight in upper-left corner
Recommendation: MEDIUM - Assess density against standards

Action Taken: Measured porosity density, within acceptable limits ✅
```

### Case 2: Borderline Lack of Penetration
```
Image: weld_sample_002.jpg
Classification: Lack of Penetration (LP)
Confidence: 68.3%
Location: Central region (coverage: 11.8%)
Heatmap: Moderate red highlight in center
Recommendation: CRITICAL - Requires immediate attention

Action Taken: Manual inspection confirmed LP, marked for repair ⚠️
```

### Case 3: Acceptable Weld
```
Image: weld_sample_003.jpg
Classification: No Defect (ND)
Confidence: 95.7%
Location: No significant regions detected
Heatmap: Mostly blue with minimal activation
Recommendation: ACCEPTABLE - Proceed to next stage

Action Taken: Approved for production ✅
```

---

##  Key Takeaways

1. **XAI shows WHERE and WHY** - Not just "what" the defect is
2. **Heatmaps are visual guides** - Red = defect location
3. **Confidence matters** - Higher confidence = more reliable
4. **Severity drives action** - CRITICAL → Reject, MEDIUM → Assess, ACCEPTABLE → Approve
5. **Always verify critical defects** - AI assists, but you're the expert

---

## 📧 Support

Questions or issues? Contact:
- **Technical Support**: radikal-support@company.com
- **Training**: radikal-training@company.com
- **System Admin**: radikal-admin@company.com

---

**Last Updated**: January 2025  
**Version**: 2.0 (with XAI Grad-CAM)  
**Status**: Production Ready ✅
