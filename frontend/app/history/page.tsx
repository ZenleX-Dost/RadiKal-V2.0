'use client';

/**
 * History/Logs Page - View past analyses
 */

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { AlertCircle } from 'lucide-react';
import { Search, Calendar, Filter, Download } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AnalysisHistoryItem } from '@/types';

export default function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Fetch history from API
  useEffect(() => {
    loadHistory();
  }, [page, selectedStatus]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters: any = {};
      if (selectedStatus !== 'all') {
        filters.status = selectedStatus;
      }

      const response = await apiClient.getHistory(page, 20, filters);
      setHistory(response.analyses);
      setTotalCount(response.total_count);
      setHasMore(response.has_more);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load history');
      console.error('Error loading history:', err);
    } finally {
      setLoading(false);
    }
  };

  // Client-side filtering for search
  const filteredHistory = history.filter((item) => {
    const matchesSearch = item.filename.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Analysis History</h1>
          <p className="text-gray-600 dark:text-gray-300">Review past defect detection analyses</p>
        </div>

        {/* Filters */}
        <Card variant="elevated" className="mb-8">
          <CardContent>
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by filename..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Status Filter */}
              <div className="flex gap-2">
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="processing">Processing</option>
                  <option value="failed">Failed</option>
                </select>

                <Button variant="secondary" size="md">
                  <Calendar className="h-4 w-4 mr-2" />
                  Date Range
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Table */}
        <Card variant="elevated">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Analysis Results ({filteredHistory.length})</CardTitle>
              <Button variant="primary" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Timestamp
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      File Name
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Detections
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Confidence
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Uncertainty
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center">
                        <div className="flex justify-center items-center">
                          <Spinner size="lg" />
                          <span className="ml-3 text-gray-600 dark:text-gray-300">Loading history...</span>
                        </div>
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center">
                        <div className="flex flex-col items-center text-red-600 dark:text-red-400">
                          <AlertCircle className="w-12 h-12 mb-2" />
                          <p className="font-medium">Failed to load history</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{error}</p>
                          <Button onClick={loadHistory} variant="primary" size="sm" className="mt-3">
                            Retry
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ) : filteredHistory.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                        {searchQuery ? 'No results found for your search.' : 'No analysis history yet. Upload an image to get started!'}
                      </td>
                    </tr>
                  ) : (
                    filteredHistory.map((item) => (
                      <tr key={item.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                          {new Date(item.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                          {item.filename}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                          {item.num_detections}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                          {(item.mean_confidence * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                          {item.mean_uncertainty !== null ? `${(item.mean_uncertainty * 100).toFixed(1)}%` : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            item.status === 'completed' 
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
                              : item.status === 'failed'
                              ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                              : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => {
                              // Navigate to dashboard with this analysis
                              // For now, show an alert with details
                              alert(`Analysis ID: ${item.id}\nFilename: ${item.filename}\nDetections: ${item.num_detections}\nConfidence: ${(item.mean_confidence * 100).toFixed(1)}%\nStatus: ${item.status}`);
                            }}
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {!loading && !error && totalCount > 0 && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div className="text-sm text-gray-600 dark:text-gray-300">
                  Showing {filteredHistory.length} of {totalCount} analyses
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={!hasMore}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
