/**
 * TypeScript types for RadiKal application.
 */

// Backend API response types (matches FastAPI schemas)
export interface DetectionBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  label: number;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

export interface DetectionResponse {
  image_id: string;
  detections: DetectionBox[];
  segmentation_masks: string[];
  inference_time_ms: number;
  timestamp: string;
  model_version: string;
}

// Frontend display types (transformed from backend)
export interface Detection {
  detection_id: string;
  bbox: [number, number, number, number];
  confidence: number;
  class_name: string;
  class_full_name?: string; // Full form of the defect name
  severity: 'high' | 'medium' | 'low' | 'critical';
  mask_base64: string | null;
  // Additional fields from backend
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label: number;
}

export interface ExplanationHeatmap {
  method: string;
  heatmap_base64: string;
  confidence_score: number;
}

export interface ExplanationResponse {
  image_id: string;
  detection_id: string;
  explanations: ExplanationHeatmap[];
  consensus_score: number;
  timestamp: string;
}

// Nested metrics types matching backend schemas
export interface BusinessMetrics {
  true_positives: number;
  true_negatives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
}

export interface DetectionMetrics {
  "mAP@0.5": number;
  "mAP@0.75": number;
  "mAP": number;
  precision: number;
  recall: number;
  f1_score: number;
  auroc: number;
}

export interface SegmentationMetrics {
  iou: number;
  dice_coefficient: number;
  pixel_accuracy: number;
}

export interface MetricsResponse {
  business_metrics: BusinessMetrics;
  detection_metrics: DetectionMetrics;
  segmentation_metrics: SegmentationMetrics;
  total_inspections: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
  timestamp: string;
}

export interface CalibrationMetrics {
  ece: number;
  mce: number;
  avg_confidence: number;
  avg_accuracy: number;
  is_calibrated: boolean;
  temperature?: number;
}

export interface CalibrationResponse {
  calibration_metrics: CalibrationMetrics;
  last_calibration_date?: string;
  num_samples_evaluated: number;
  timestamp: string;
}

export interface ExportResponse {
  export_id: string;
  download_url: string;
  format: string;
  timestamp: string;
  expires_at: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  model_loaded: boolean;
  device: string;
  version: string;
}

export interface AnalysisHistoryItem {
  id: number;
  image_id: string;
  filename: string;
  timestamp: string;
  num_detections: number;
  has_defects: boolean;
  highest_severity: string;
  mean_confidence: number;
  mean_uncertainty: number;
  status: string;
}

export interface AnalysisHistoryResponse {
  analyses: AnalysisHistoryItem[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
