'use client';

/**
 * Component to display detection results with bounding boxes.
 */

import { Detection } from '@/types';
import { AlertTriangle, CheckCircle, Info, ImageOff } from 'lucide-react';
import { useRef, useEffect, useState } from 'react';

interface DetectionResultsProps {
  imageUrl: string;
  detections: Detection[];
  meanUncertainty: number;
}

// Placeholder SVG for when image fails to load
const PLACEHOLDER_IMAGE = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23f3f4f6" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%239ca3af" font-size="16"%3EImage not available%3C/text%3E%3C/svg%3E';

export default function DetectionResults({
  imageUrl,
  detections,
  meanUncertainty,
}: DetectionResultsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { text: 'text-red-600 bg-red-100 border-red-600', box: '#EF4444' };
      case 'high':
        return { text: 'text-red-600 bg-red-100 border-red-600', box: '#EF4444' };
      case 'medium':
        return { text: 'text-yellow-600 bg-yellow-100 border-yellow-600', box: '#EAB308' };
      case 'low':
        return { text: 'text-green-600 bg-green-100 border-green-600', box: '#10B981' };
      default:
        return { text: 'text-gray-600 bg-gray-100 border-gray-600', box: '#6B7280' };
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
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

  // Draw bounding boxes on canvas when image loads or detections change
  useEffect(() => {
    const image = imageRef.current;
    const canvas = canvasRef.current;

    if (!image || !canvas || !imageUrl) return;

    const drawBoundingBoxes = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const naturalWidth = image.naturalWidth;
      const naturalHeight = image.naturalHeight;

      if (naturalWidth === 0 || naturalHeight === 0) return;

      // Set canvas to natural image size for crisp rendering
      canvas.width = naturalWidth;
      canvas.height = naturalHeight;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw each detection at original resolution
      detections.forEach((detection, idx) => {
        const [x1, y1, x2, y2] = detection.bbox;
        const width = x2 - x1;
        const height = y2 - y1;

        // Get color based on severity
        const color = getSeverityColor(detection.severity).box;

        // Draw bounding box with thicker line for visibility
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.strokeRect(x1, y1, width, height);

        // Draw semi-transparent filled rectangle
        ctx.fillStyle = color + '15'; // Add transparency
        ctx.fillRect(x1, y1, width, height);

        // Calculate font size based on image size
        const fontSize = Math.max(16, Math.floor(naturalWidth / 40));
        const label = `${detection.class_name} ${(detection.confidence * 100).toFixed(0)}%`;
        ctx.font = `bold ${fontSize}px Arial`;
        const textMetrics = ctx.measureText(label);
        const textHeight = fontSize + 4;
        const padding = 6;

        // Draw label background at top
        const labelY = Math.max(textHeight + padding, y1);
        ctx.fillStyle = color;
        ctx.fillRect(
          x1,
          labelY - textHeight - padding,
          textMetrics.width + padding * 2,
          textHeight + padding
        );

        // Label text - Always white for visibility
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, x1 + padding, labelY - padding);

        // Draw detection number badge
        const badgeSize = fontSize + 10;
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1, badgeSize, badgeSize);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${idx + 1}`, x1 + badgeSize / 2, y1 + badgeSize / 2);

        // Reset text alignment
        ctx.textAlign = 'left';
        ctx.textBaseline = 'alphabetic';
      });
    };

    // Draw when image loads
    if (image.complete && image.naturalWidth > 0) {
      drawBoundingBoxes();
    } else {
      image.onload = drawBoundingBoxes;
    }

    // Redraw on window resize
    const resizeObserver = new ResizeObserver(() => {
      if (image.complete && image.naturalWidth > 0) {
        drawBoundingBoxes();
      }
    });
    resizeObserver.observe(image);

    return () => {
      resizeObserver.disconnect();
    };
  }, [imageUrl, detections]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Image with detections */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          Detection Results
          {detections.length > 0 && (
            <span className="text-sm font-normal text-gray-500">
              (Bounding boxes drawn on image)
            </span>
          )}
        </h3>
        <div className="relative border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-50 flex items-center justify-center min-h-[200px]">
          {/* Loading indicator */}
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {/* Error state */}
          {imageError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
              <ImageOff className="h-12 w-12 mb-2" />
              <p className="text-sm">Failed to load image</p>
            </div>
          )}

          <div className="relative" style={{ maxHeight: '500px', maxWidth: '100%' }}>
            {/* Base image */}
            <img
              ref={imageRef}
              src={imageError ? PLACEHOLDER_IMAGE : (imageUrl || PLACEHOLDER_IMAGE)}
              alt="Analyzed"
              className={`block max-h-[500px] w-auto h-auto ${!imageLoaded ? 'opacity-0' : 'opacity-100'} transition-opacity duration-200`}
              style={{ objectFit: 'contain' }}
              onLoad={() => {
                setImageLoaded(true);
                setImageError(false);
              }}
              onError={() => {
                setImageError(true);
                setImageLoaded(true);
              }}
            />
            {/* Canvas overlay for bounding boxes - exactly same size as image */}
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
            />
          </div>
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
              className={`p-4 border-2 rounded-lg ${getSeverityColor(detection.severity).text}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 text-xs font-bold">
                    {idx + 1}
                  </div>
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
                  Location: [{detection.bbox.map(v => v.toFixed(0)).join(', ')}]
                </p>
                <p className="text-gray-400">
                  Size: {(detection.bbox[2] - detection.bbox[0]).toFixed(0)} × {(detection.bbox[3] - detection.bbox[1]).toFixed(0)} px
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
