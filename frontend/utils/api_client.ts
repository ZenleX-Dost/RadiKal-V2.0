import axios from 'axios';
import { DetectionResponse, ExplanationResponse } from '@/types';

const API_BASE_URL = 'http://localhost:8000/api/xai-qc';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const apiClient = {
    /**
     * Detect defects in an uploaded image.
     * @param file The image file to analyze
     * @param contrast Contrast adjustment factor (default 1.0)
     * @param contrastMethod Contrast adjustment method
     */
    detectDefects: async (
        file: File,
        contrast: number = 1.0,
        contrastMethod: string = 'linear'
    ): Promise<DetectionResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        // Add contrast parameters if needed
        if (contrast !== 1.0 || contrastMethod !== 'linear') {
            formData.append('contrast', contrast.toString());
            formData.append('contrast_method', contrastMethod);
        }

        const response = await api.post<DetectionResponse>('/detect', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Get XAI explanations for a detection.
     * @param params Object containing image_id and original file
     */
    getExplanations: async (params: {
        image_id: string;
        file: File;
        methods?: string[];
        contrast?: number;
        contrastMethod?: string;
    }): Promise<ExplanationResponse> => {
        const formData = new FormData();
        formData.append('file', params.file);

        if (params.methods) {
            formData.append('methods', params.methods.join(','));
        }

        if (params.contrast && params.contrast !== 1.0) {
            formData.append('contrast', params.contrast.toString());
        }

        if (params.contrastMethod && params.contrastMethod !== 'linear') {
            formData.append('contrast_method', params.contrastMethod);
        }

        const response = await api.post<ExplanationResponse>('/explain', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    /**
     * Get analysis history.
     */
    getHistory: async (params: { page: number; limit: number }) => {
        const response = await api.get('/history', { params });
        return response.data;
    },

    /**
     * Get metrics.
     */
    getMetrics: async (params?: { start_date?: string; end_date?: string }) => {
        const response = await api.get('/metrics', { params });
        return response.data;
    },

    /**
     * Export report.
     */
    exportReport: async (format: string, analysisIds?: string[]) => {
        const response = await api.post('/export', { format, analysis_ids: analysisIds });
        return response.data;
    },

    /**
     * Preprocess image with contrast adjustment (real-time preview).
     */
    preprocessImage: async (
        file: File,
        contrast: number = 1.0,
        method: string = 'clahe'
    ): Promise<{
        image_id: string;
        original_base64: string;
        processed_base64: string;
        contrast: number;
        method: string;
        timestamp: string;
    }> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post(
            `/preprocess?contrast=${contrast}&method=${method}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    },

    /**
     * Get available reviewers based on role hierarchy.
     */
    getReviewers: async (currentUserId: string = 'system'): Promise<{
        id: string;
        name: string;
        email: string;
        role: string;
    }[]> => {
        const response = await api.get(`/reviews/reviewers?current_user_id=${currentUserId}`);
        return response.data;
    },

    /**
     * Get review queue.
     */
    getReviewQueue: async (params?: { status?: string; limit?: number }) => {
        const response = await api.get('/reviews/queue', { params });
        return response.data;
    },

    /**
     * Submit review with optional reviewer assignment.
     */
    submitReview: async (review: {
        analysis_id: string;
        status: 'approved' | 'rejected' | 'needs_second_opinion';
        comments?: string;
        reviewer_notes?: string;
        assigned_reviewer_id?: string;
    }, currentUserId: string = 'system') => {
        const response = await api.post(
            `/reviews/submit?current_user_id=${currentUserId}`,
            review
        );
        return response.data;
    }
};
