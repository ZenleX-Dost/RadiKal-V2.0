'use client';

import { useState, useRef, useEffect } from 'react';
import { Sliders, Sun, Moon, Maximize, RotateCcw } from 'lucide-react';

interface ContrastAdjusterProps {
    imageSrc: string; // Original image source (base64 or URL)
    initialContrast?: number;
    initialMethod?: string;
    onApply: (contrast: number, method: string) => void;
    onCancel?: () => void;
}

const CONTRAST_METHODS = [
    { id: 'linear', label: 'Linear', description: 'Simple brightness/contrast scaling' },
    { id: 'histogram', label: 'Histogram Eq', description: 'Equalize histogram for better distribution' },
    { id: 'clahe', label: 'CLAHE', description: 'Adaptive usage for local contrast (Best for X-ray)' },
    { id: 'gamma', label: 'Gamma', description: 'Non-linear correction (Power law)' },
];

export default function ContrastAdjuster({
    imageSrc,
    initialContrast = 1.0,
    initialMethod = 'linear',
    onApply,
    onCancel
}: ContrastAdjusterProps) {
    const [contrast, setContrast] = useState(initialContrast);
    const [method, setMethod] = useState(initialMethod);
    const [previewUrl, setPreviewUrl] = useState<string>(imageSrc);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Apply preview effect using CSS or Canvas
    // Note: Only 'linear' and basic 'gamma' can be easily previewed with CSS. 
    // Advanced methods like CLAHE need backend or complex JS libs. 
    // For MVP, we will simulate linear/gamma with CSS filters and just show placeholder/info for others.

    const getCssFilter = () => {
        if (method === 'linear') {
            // Linear contrast in CSS matches roughly
            return `contrast(${contrast})`;
        } else if (method === 'gamma') {
            // Gamma can be approximated with brightness/contrast combo or just brightness for simple cases
            // But CSS doesn't have direct gamma. We use contrast/brightness approximation.
            // Gamma < 1 brightens shadows, > 1 darkens.
            // We'll just use contrast() for preview consistency for now as gamma is tricky in CSS.
            return `contrast(${contrast})`;
        }
        return 'none';
    };

    const handleApply = () => {
        onApply(contrast, method);
    };

    const handleReset = () => {
        setContrast(1.0);
        setMethod('linear');
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Sliders className="w-5 h-5 text-blue-600" />
                    Image Enhancement
                </h3>
                <button
                    onClick={handleReset}
                    className="text-sm text-gray-500 hover:text-blue-600 flex items-center gap-1"
                >
                    <RotateCcw className="w-3 h-3" /> Reset
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Controls */}
                <div className="md:col-span-1 space-y-6">
                    {/* Method Selection */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">Enhancement Method</label>
                        <div className="space-y-2">
                            {CONTRAST_METHODS.map((m) => (
                                <button
                                    key={m.id}
                                    onClick={() => setMethod(m.id)}
                                    className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${method === m.id
                                            ? 'bg-blue-50 text-blue-700 border border-blue-200 font-medium'
                                            : 'bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100'
                                        }`}
                                >
                                    <div className="flex justify-between items-center">
                                        <span>{m.label}</span>
                                        {method === m.id && <div className="w-2 h-2 rounded-full bg-blue-500"></div>}
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1">{m.description}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Contrast Slider */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <label className="text-sm font-medium text-gray-700">Intensity Factor</label>
                            <span className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                                {contrast.toFixed(2)}x
                            </span>
                        </div>

                        <div className="flex items-center gap-3">
                            <Moon className="w-4 h-4 text-gray-400" />
                            <input
                                type="range"
                                min="0.5"
                                max="2.5"
                                step="0.1"
                                value={contrast}
                                onChange={(e) => setContrast(parseFloat(e.target.value))}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                            <Sun className="w-4 h-4 text-gray-400" />
                        </div>
                        <p className="text-xs text-gray-500">
                            Values &gt; 1.0 increase contrast, values &lt; 1.0 decrease it.
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-2 flex gap-3">
                        <button
                            onClick={handleApply}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                            Apply to Analysis
                        </button>
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                </div>

                {/* Preview */}
                <div className="md:col-span-2 bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center relative min-h-[300px]">
                    <div className="absolute top-3 left-3 bg-black/50 text-white text-xs px-2 py-1 rounded backdrop-blur-sm z-10">
                        Preview: {method === 'linear' || method === 'gamma' ? 'Approximation' : 'Backend Processing Required'}
                    </div>

                    <div
                        className="relative max-w-full max-h-[400px] overflow-hidden"
                        style={{
                            filter: getCssFilter(),
                            transition: 'filter 0.2s ease-out'
                        }}
                    >
                        <img
                            src={imageSrc}
                            alt="Preview"
                            className="max-w-full max-h-[400px] object-contain"
                        />
                    </div>

                    {(method === 'clahe' || method === 'histogram') && (
                        <div className="absolute bottom-4 left-4 right-4 bg-yellow-500/90 text-white text-xs px-3 py-2 rounded text-center backdrop-blur-sm">
                            Note: {method.toUpperCase()} effect will be applied on server. Preview is approximate.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
