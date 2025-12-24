'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/utils/api_client';
import { AlertCircle, CheckCircle, XCircle, Users, ChevronDown } from 'lucide-react';

interface ReviewItem {
  analysis_id: string;
  image_name: string;
  upload_timestamp: string;
  defect_type: string | null;
  severity: string | null;
  confidence: number;
  review_status: string;
  image_base64: string | null;
}

interface Reviewer {
  id: string;
  name: string;
  email: string;
  role: string;
}

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [reviewers, setReviewers] = useState<Reviewer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null);
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'rejected' | 'needs_second_opinion'>('approved');
  const [comments, setComments] = useState('');
  const [assignedReviewerId, setAssignedReviewerId] = useState('');
  const [showReviewerSelect, setShowReviewerSelect] = useState(false);

  useEffect(() => {
    loadQueue();
    loadReviewers();
  }, []);

  const loadQueue = async () => {
    try {
      const data = await apiClient.getReviewQueue({ limit: 50 });
      setQueue(data);
    } catch (error) {
      console.error('Failed to load review queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadReviewers = async () => {
    try {
      const data = await apiClient.getReviewers();
      setReviewers(data);
    } catch (error) {
      console.error('Failed to load reviewers:', error);
    }
  };

  const handleReview = async () => {
    if (!selectedItem) return;

    try {
      await apiClient.submitReview({
        analysis_id: selectedItem.analysis_id,
        status: reviewStatus,
        comments,
        assigned_reviewer_id: reviewStatus === 'needs_second_opinion' ? assignedReviewerId : undefined,
      });

      // Close modal and refresh queue
      setSelectedItem(null);
      setComments('');
      setAssignedReviewerId('');
      loadQueue();
    } catch (error) {
      console.error('Failed to submit review:', error);
    }
  };

  const getSeverityColor = (severity: string | null) => {
    switch (severity?.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role.toLowerCase()) {
      case 'manager':
        return <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-700">Manager</span>;
      case 'project_chief':
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-700">Project Chief</span>;
      case 'technician':
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-700">Technician</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">{role}</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Review Queue</h1>
        <p className="text-gray-600 mt-2">Review AI predictions and request second opinions</p>
      </div>

      <div className="grid gap-4">
        {queue.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <CheckCircle className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-gray-600">No items in review queue</p>
          </div>
        ) : (
          queue.map((item) => (
            <div key={item.analysis_id} className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                {/* Image Preview */}
                <div className="flex-shrink-0">
                  {item.image_base64 ? (
                    <img
                      src={`data:image/jpeg;base64,${item.image_base64}`}
                      alt={item.image_name}
                      className="w-32 h-32 object-cover rounded border"
                    />
                  ) : (
                    <div className="w-32 h-32 bg-gray-200 rounded border flex items-center justify-center">
                      <span className="text-gray-400 text-sm">No preview</span>
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{item.image_name}</h3>
                  <p className="text-sm text-gray-500">
                    {new Date(item.upload_timestamp).toLocaleString()}
                  </p>

                  <div className="mt-2 flex items-center gap-4">
                    <div>
                      <span className="text-sm text-gray-600">Defect Type: </span>
                      <span className="font-medium">{item.defect_type || 'None'}</span>
                    </div>
                    {item.severity && (
                      <div>
                        <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(item.severity)}`}>
                          {item.severity}
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-sm text-gray-600">Confidence: </span>
                      <span className="font-medium">{(item.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                {/* Review Button */}
                <button
                  onClick={() => setSelectedItem(item)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Review
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Review Modal */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Review Analysis</h2>

            {/* Image */}
            <div className="mb-4">
              {selectedItem.image_base64 ? (
                <img
                  src={`data:image/jpeg;base64,${selectedItem.image_base64}`}
                  alt={selectedItem.image_name}
                  className="w-full h-64 object-contain rounded border"
                />
              ) : (
                <div className="w-full h-64 bg-gray-200 rounded border flex items-center justify-center">
                  <span className="text-gray-400">No preview available</span>
                </div>
              )}
            </div>

            {/* Details */}
            <div className="mb-4 space-y-2">
              <div>
                <span className="font-semibold">File: </span>
                {selectedItem.image_name}
              </div>
              <div>
                <span className="font-semibold">Defect Type: </span>
                {selectedItem.defect_type || 'None detected'}
              </div>
              {selectedItem.severity && (
                <div>
                  <span className="font-semibold">Severity: </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(selectedItem.severity)}`}>
                    {selectedItem.severity}
                  </span>
                </div>
              )}
              <div>
                <span className="font-semibold">Confidence: </span>
                {(selectedItem.confidence * 100).toFixed(1)}%
              </div>
            </div>

            {/* Review Status */}
            <div className="mb-4">
              <label className="block font-semibold mb-2">Review Decision</label>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setReviewStatus('approved');
                    setShowReviewerSelect(false);
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg border-2 transition-colors ${
                    reviewStatus === 'approved'
                      ? 'border-green-600 bg-green-50 text-green-700'
                      : 'border-gray-300 hover:border-green-300'
                  }`}
                >
                  <CheckCircle className="inline mr-2 h-5 w-5" />
                  Approve
                </button>
                <button
                  onClick={() => {
                    setReviewStatus('rejected');
                    setShowReviewerSelect(false);
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg border-2 transition-colors ${
                    reviewStatus === 'rejected'
                      ? 'border-red-600 bg-red-50 text-red-700'
                      : 'border-gray-300 hover:border-red-300'
                  }`}
                >
                  <XCircle className="inline mr-2 h-5 w-5" />
                  Reject
                </button>
                <button
                  onClick={() => {
                    setReviewStatus('needs_second_opinion');
                    setShowReviewerSelect(true);
                  }}
                  className={`flex-1 py-2 px-4 rounded-lg border-2 transition-colors ${
                    reviewStatus === 'needs_second_opinion'
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-300 hover:border-blue-300'
                  }`}
                >
                  <Users className="inline mr-2 h-5 w-5" />
                  Second Opinion
                </button>
              </div>
            </div>

            {/* Reviewer Selection (shown when requesting second opinion) */}
            {showReviewerSelect && reviewStatus === 'needs_second_opinion' && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <label className="block font-semibold mb-2 text-blue-900">
                  <Users className="inline mr-2 h-5 w-5" />
                  Assign to Reviewer
                </label>
                <select
                  value={assignedReviewerId}
                  onChange={(e) => setAssignedReviewerId(e.target.value)}
                  className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a reviewer...</option>
                  {reviewers.map((reviewer) => (
                    <option key={reviewer.id} value={reviewer.id}>
                      {reviewer.name} ({reviewer.role})
                    </option>
                  ))}
                </select>

                {/* Reviewer List Preview */}
                <div className="mt-3 space-y-2">
                  <p className="text-sm text-blue-700 font-medium">Available Reviewers:</p>
                  {reviewers.map((reviewer) => (
                    <div key={reviewer.id} className="flex items-center justify-between text-sm">
                      <div>
                        <span className="font-medium">{reviewer.name}</span>
                        <span className="text-gray-500 ml-2">{reviewer.email}</span>
                      </div>
                      {getRoleBadge(reviewer.role)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Comments */}
            <div className="mb-4">
              <label className="block font-semibold mb-2">Comments (Optional)</label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Add any notes or observations..."
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                rows={4}
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleReview}
                disabled={reviewStatus === 'needs_second_opinion' && !assignedReviewerId}
                className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                Submit Review
              </button>
              <button
                onClick={() => {
                  setSelectedItem(null);
                  setComments('');
                  setAssignedReviewerId('');
                  setShowReviewerSelect(false);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
