'use client';

/**
 * Component to display XAI explanations with heatmaps.
 */

import { ExplanationHeatmap } from '@/types';
import { useState } from 'react';

interface XAIExplanationsProps {
  explanations: ExplanationHeatmap[];
  consensusScore: number;
}

export default function XAIExplanations({
  explanations,
  consensusScore,
}: XAIExplanationsProps) {
  const [selectedMethod, setSelectedMethod] = useState<string>(
    explanations[0]?.method || ''
  );

  const selectedExplanation = explanations.find(
    (exp) => exp.method === selectedMethod
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">XAI Explanations</h3>
        <div className="px-4 py-2 bg-green-100 border border-green-300 rounded-lg">
          <p className="text-sm text-green-900">
            <strong>Consensus Score:</strong> {(consensusScore * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Method selector */}
      <div className="flex flex-wrap gap-2">
        {explanations.map((exp) => (
          <button
            key={exp.method}
            onClick={() => setSelectedMethod(exp.method)}
            className={`
              px-4 py-2 rounded-lg font-medium transition-colors
              ${
                selectedMethod === exp.method
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }
            `}
          >
            {exp.method.toUpperCase()}
            <span className="ml-2 text-xs opacity-75">
              ({(exp.confidence_score * 100).toFixed(0)}%)
            </span>
          </button>
        ))}
      </div>

      {/* Selected heatmap */}
      {selectedExplanation && (
        <div className="space-y-3">
          <div className="border-2 border-gray-300 rounded-lg overflow-hidden">
            <img
              src={`data:image/png;base64,${selectedExplanation.heatmap_base64}`}
              alt={`${selectedMethod} heatmap`}
              className="w-full h-auto"
            />
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>Method:</strong> {selectedMethod.toUpperCase()}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Confidence:</strong>{' '}
              {(selectedExplanation.confidence_score * 100).toFixed(2)}%
            </p>
            <p className="text-xs text-gray-600 mt-2">
              {getMethodDescription(selectedMethod)}
            </p>
          </div>
        </div>
      )}

      {/* Comparison grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {explanations.map((exp) => (
          <div
            key={exp.method}
            className="border border-gray-300 rounded-lg overflow-hidden cursor-pointer hover:border-blue-500 transition-colors"
            onClick={() => setSelectedMethod(exp.method)}
          >
            <img
              src={`data:image/png;base64,${exp.heatmap_base64}`}
              alt={`${exp.method} thumbnail`}
              className="w-full h-auto"
            />
            <div className="p-2 text-center bg-gray-50">
              <p className="text-xs font-medium">{exp.method.toUpperCase()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getMethodDescription(method: string): string {
  const descriptions: Record<string, string> = {
    'grad-cam': 'Visualizes which regions of the image the model focuses on using gradient-weighted class activation mapping.',
    'shap': 'Uses Shapley values to explain the contribution of each pixel to the model\'s prediction.',
    'lime': 'Generates local explanations by perturbing the input image and observing prediction changes.',
    'integrated-gradients': 'Computes the gradient of the output with respect to the input along a path from a baseline.',
  };
  return descriptions[method] || 'AI explainability method visualization.';
}
