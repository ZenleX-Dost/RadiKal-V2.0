'use client';

/**
 * Metrics Dashboard Page
 */

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { MetricsResponse, CalibrationResponse } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { AlertCircle, TrendingUp, Target, Activity, CheckCircle, HelpCircle } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [calibration, setCalibration] = useState<CalibrationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Metric explanations
  const metricExplanations = {
    precision: "Precision measures the accuracy of positive predictions. It answers: Of all detections the model made, how many were actually correct? Higher is better.",
    recall: "Recall measures the model's ability to find all defects. It answers: Of all actual defects, how many did the model detect? Higher is better.",
    f1Score: "F1 Score is the harmonic mean of Precision and Recall. It provides a single score balancing both metrics. Perfect score is 100%.",
    auroc: "AUROC (Area Under ROC Curve) measures the model's ability to distinguish between defects and non-defects across all thresholds. 100% is perfect.",
    map50: "mAP@0.5 is Mean Average Precision at 50% IoU threshold. It measures detection accuracy when bounding boxes overlap at least 50% with ground truth.",
    map75: "mAP@0.75 is Mean Average Precision at 75% IoU threshold. Stricter metric requiring 75% overlap, indicating more precise localization.",
    mapAvg: "mAP (Average) is the mean of mAP values across IoU thresholds from 50% to 95%. This is the primary COCO-style metric for object detection.",
    truePositives: "Correct detections - the model correctly identified a defect that actually exists.",
    trueNegatives: "Correct rejections - the model correctly identified no defect where none exists.",
    falsePositives: "False alarms - the model detected a defect where none actually exists.",
    falseNegatives: "Missed defects - the model failed to detect an actual defect.",
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const [metricsData, calibrationData] = await Promise.all([
        apiClient.getMetrics(),
        apiClient.getCalibration(),
      ]);
      setMetrics(metricsData);
      setCalibration(calibrationData);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load metrics from backend:', err);
      setError(err.response?.data?.detail || err.message || 'Backend connection failed. Please ensure the backend server is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Error Loading Metrics</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  // Prepare data for charts
  const performanceData = [
    { metric: 'Precision', value: (metrics.detection_metrics.precision || 0) * 100 },
    { metric: 'Recall', value: (metrics.detection_metrics.recall || 0) * 100 },
    { metric: 'F1 Score', value: (metrics.detection_metrics.f1_score || 0) * 100 },
    { metric: 'mAP@50', value: (metrics.detection_metrics["mAP@0.5"] || 0) * 100 },
    { metric: 'AUROC', value: (metrics.detection_metrics.auroc || 0) * 100 },
  ];

  const confusionData = [
    { category: 'True Positives', count: metrics.business_metrics.true_positives || 0 },
    { category: 'True Negatives', count: metrics.business_metrics.true_negatives || 0 },
    { category: 'False Positives', count: metrics.business_metrics.false_positives || 0 },
    { category: 'False Negatives', count: metrics.business_metrics.false_negatives || 0 },
  ];

  const radarData = [
    { metric: 'Precision', value: metrics.detection_metrics.precision || 0 },
    { metric: 'Recall', value: metrics.detection_metrics.recall || 0 },
    { metric: 'F1', value: metrics.detection_metrics.f1_score || 0 },
    { metric: 'mAP', value: metrics.detection_metrics["mAP@0.5"] || 0 },
    { metric: 'AUROC', value: metrics.detection_metrics.auroc || 0 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Performance Metrics</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Monitoring model performance and calibration
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card variant="elevated" className="group relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-1">
                  Precision
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-blue-500 cursor-help" />
                    <span className="absolute left-0 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.precision}
                    </span>
                  </span>
                </p>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {((metrics.detection_metrics.precision || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <Target className="h-12 w-12 text-blue-600 dark:text-blue-400 opacity-20" />
            </div>
          </Card>

          <Card variant="elevated" className="group relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-1">
                  Recall
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-green-500 cursor-help" />
                    <span className="absolute left-0 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.recall}
                    </span>
                  </span>
                </p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {((metrics.detection_metrics.recall || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-12 w-12 text-green-600 dark:text-green-400 opacity-20" />
            </div>
          </Card>

          <Card variant="elevated" className="group relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-1">
                  F1 Score
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-purple-500 cursor-help" />
                    <span className="absolute left-0 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.f1Score}
                    </span>
                  </span>
                </p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                  {((metrics.detection_metrics.f1_score || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <Activity className="h-12 w-12 text-purple-600 dark:text-purple-400 opacity-20" />
            </div>
          </Card>

          <Card variant="elevated" className="group relative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-1">
                  AUROC
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-orange-500 cursor-help" />
                    <span className="absolute left-0 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.auroc}
                    </span>
                  </span>
                </p>
                <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                  {((metrics.detection_metrics.auroc || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <CheckCircle className="h-12 w-12 text-orange-600 dark:text-orange-400 opacity-20" />
            </div>
          </Card>
        </div>

        {/* mAP Metrics - NEW SECTION */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Mean Average Precision (mAP)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card variant="elevated">
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex items-center justify-center gap-1">
                  mAP@0.5
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-blue-500 cursor-help" />
                    <span className="absolute left-1/2 -translate-x-1/2 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.map50}
                    </span>
                  </span>
                </p>
                <p className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {((metrics.detection_metrics["mAP@0.5"] || 0) * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">IoU Threshold: 50%</p>
              </div>
            </Card>

            <Card variant="elevated">
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex items-center justify-center gap-1">
                  mAP@0.75
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-green-500 cursor-help" />
                    <span className="absolute left-1/2 -translate-x-1/2 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.map75}
                    </span>
                  </span>
                </p>
                <p className="text-4xl font-bold text-green-600 dark:text-green-400 mb-1">
                  {((metrics.detection_metrics["mAP@0.75"] || 0) * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">IoU Threshold: 75%</p>
              </div>
            </Card>

            <Card variant="elevated">
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex items-center justify-center gap-1">
                  mAP (Average)
                  <span className="relative group/tooltip">
                    <HelpCircle className="w-4 h-4 text-gray-400 hover:text-purple-500 cursor-help" />
                    <span className="absolute left-1/2 -translate-x-1/2 top-6 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-10">
                      {metricExplanations.mapAvg}
                    </span>
                  </span>
                </p>
                <p className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  {((metrics.detection_metrics["mAP"] || 0) * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">IoU: 0.5:0.95</p>
              </div>
            </Card>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Performance Bar Chart */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Confusion Matrix */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Confusion Matrix</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={confusionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Radar Chart */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Model Performance Radar</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis domain={[0, 1]} />
                  <Radar name="Performance" dataKey="value" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.6} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Segmentation Metrics */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Segmentation Quality</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600">Mean IoU</span>
                    <span className="text-sm font-semibold">{(metrics.segmentation_metrics.iou * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${metrics.segmentation_metrics.iou * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600">Mean Dice Score</span>
                    <span className="text-sm font-semibold">{(metrics.segmentation_metrics.dice_coefficient * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${metrics.segmentation_metrics.dice_coefficient * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600">mAP@50</span>
                    <span className="text-sm font-semibold">{(metrics.detection_metrics["mAP@0.5"] * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${metrics.detection_metrics["mAP@0.5"] * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Calibration & Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Calibration Status */}
          {calibration && (
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Model Calibration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      calibration.calibration_metrics.is_calibrated
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {calibration.calibration_metrics.is_calibrated ? 'Calibrated' : 'Needs Calibration'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Expected Calibration Error (ECE)</span>
                    <span className="text-sm font-semibold">{(calibration.calibration_metrics.ece * 100).toFixed(2)}%</span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Temperature</span>
                    <span className="text-sm font-semibold">{calibration.calibration_metrics.temperature?.toFixed(3) || 'N/A'}</span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Calibration Samples</span>
                    <span className="text-sm font-semibold">{calibration.num_samples_evaluated}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Summary Statistics */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Summary Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Total Inspections</span>
                  <span className="text-sm font-semibold">{metrics.total_inspections}</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Accuracy</span>
                  <span className="text-sm font-semibold">{(metrics.business_metrics.accuracy * 100).toFixed(2)}%</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Date Range</span>
                  <span className="text-sm font-semibold">
                    {new Date(metrics.date_range.start_date).toLocaleDateString()} - {new Date(metrics.date_range.end_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
