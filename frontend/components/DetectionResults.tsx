'use client';

/**
 * Component to display detection results with bounding boxes.
 */

import { Detection } from '@/types';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface DetectionResultsProps {
  imageUrl: string;
  detections: Detection[];
  meanUncertainty: number;
}

export default function DetectionResults({
  imageUrl,
  detections,
  meanUncertainty,
}: DetectionResultsProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-100 border-red-600';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 border-yellow-600';
      case 'low':
        return 'text-green-600 bg-green-100 border-green-600';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-600';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="h-5 w-5" />;
      case 'medium':
        return <Info className="h-5 w-5" />;
      case 'low':
        return <CheckCircle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Image with detections */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Detection Results</h3>
        <div className="relative border-2 border-gray-300 rounded-lg overflow-hidden max-h-[500px] flex items-center justify-center bg-gray-50">
          <img src={imageUrl} alt="Analyzed" className="w-full h-auto max-h-[500px] object-contain" />
        </div>
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">
            <strong>Mean Uncertainty:</strong> {(meanUncertainty * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-blue-700 mt-1">
            Lower values indicate higher model confidence
          </p>
        </div>
      </div>

      {/* Detections list */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">
          Detected Defects ({detections.length})
        </h3>
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {detections.map((detection, idx) => (
            <div
              key={detection.detection_id}
              className={`p-4 border-2 rounded-lg ${getSeverityColor(detection.severity)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  {getSeverityIcon(detection.severity)}
                  <div>
                    <h4 className="font-bold text-lg">
                      {detection.class_name}
                    </h4>
                    {detection.class_full_name && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {detection.class_full_name}
                      </p>
                    )}
                    <p className="text-sm opacity-90 mt-1">
                      Confidence: {(detection.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                <span className="text-xs font-medium px-2 py-1 rounded uppercase">
                  {detection.severity}
                </span>
              </div>
              <div className="mt-2 text-xs opacity-75">
                <p>
                  BBox: [{detection.bbox.map(v => v.toFixed(0)).join(', ')}]
                </p>
                <p>ID: {detection.detection_id.slice(0, 8)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
