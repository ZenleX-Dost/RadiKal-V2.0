/**
 * Example usage of enhanced XAI visualization components
 * 
 * This demonstrates how to integrate:
 * - DefectLocalizationView
 * - OperatorMessaging components
 * - XAIExplanations
 */

'use client';

import { useState } from 'react';
import XAIExplanations from '@/components/XAIExplanations';
import { ExplanationResponse } from '@/types';
import { Upload, Loader2 } from 'lucide-react';

export default function XAIAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setError(null);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/api/explain', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const result: ExplanationResponse = await response.json();
      setExplanation(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            XAI Defect Analysis
          </h1>
          <p className="mt-2 text-gray-600">
            Upload a radiographic weld image for AI-powered defect detection and explainability
          </p>
        </div>

        {/* Upload section */}
        <div className="bg-white border-2 border-gray-300 rounded-xl p-6 mb-8 shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Image</h2>
          
          <div className="flex items-center space-x-4">
            <label className="flex-1 cursor-pointer">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-blue-500 transition-colors">
                <div className="flex flex-col items-center justify-center space-y-3">
                  <Upload className="w-12 h-12 text-gray-400" />
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-700">
                      {selectedFile ? selectedFile.name : 'Click to upload or drag and drop'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      PNG, JPG up to 10MB
                    </p>
                  </div>
                </div>
              </div>
              <input
                type="file"
                accept="image/png,image/jpeg"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>

            {selectedFile && (
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <span>Analyze Defects</span>
                )}
              </button>
            )}
          </div>

          {/* Image preview */}
          {imagePreview && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Preview</h3>
              <div className="border-2 border-gray-300 rounded-lg overflow-hidden max-w-md">
                <img src={imagePreview} alt="Preview" className="w-full h-auto" />
              </div>
            </div>
          )}

          {/* Error display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-300 rounded-lg">
              <p className="text-sm text-red-800">
                <strong>Error:</strong> {error}
              </p>
            </div>
          )}
        </div>

        {/* Results section */}
        {explanation && (
          <div className="bg-white border-2 border-gray-300 rounded-xl p-6 shadow-md">
            <XAIExplanations
              explanation={explanation}
              originalImage={imagePreview || undefined}
            />
          </div>
        )}

        {/* Instructions */}
        {!explanation && !loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">How it works</h3>
            <ol className="space-y-2 text-sm text-blue-800">
              <li className="flex items-start space-x-2">
                <span className="font-bold">1.</span>
                <span>Upload a radiographic weld image using the file selector above</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold">2.</span>
                <span>Click "Analyze Defects" to run AI-powered defect detection</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold">3.</span>
                <span>Review the results including:</span>
              </li>
              <ul className="ml-6 mt-2 space-y-1">
                <li>• Defect classification and severity level</li>
                <li>• Grad-CAM heatmap showing defect location</li>
                <li>• Interactive region highlighting</li>
                <li>• Confidence scores for all defect types</li>
                <li>• Actionable recommendations for operators</li>
              </ul>
              <li className="flex items-start space-x-2">
                <span className="font-bold">4.</span>
                <span>Use zoom controls to inspect defect regions in detail</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold">5.</span>
                <span>Click on detected regions to highlight and get more information</span>
              </li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
