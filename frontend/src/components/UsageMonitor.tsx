'use client';

import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { apiClient, handleApiError } from '../lib/api';
import { UsageStats } from '../lib/types';

export default function UsageMonitor() {
  const [usageData, setUsageData] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsageStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getUsageStats();
      setUsageData(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsageStats();
  }, []);

  const getProgressColor = (percentage: number): string => {
    if (percentage < 50) return 'bg-green-500';
    if (percentage < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };



  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center text-black">
          API Usage Monitor
        </h3>
        <button
          onClick={fetchUsageStats}
          disabled={loading}
          className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors disabled:opacity-50"
          title="Refresh usage stats"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error ? (
        <div className="text-sm text-gray-800">
          <p className="mb-2">Usage monitor temporarily unavailable</p>
          <p className="text-xs">Rate limiting still protecting costs</p>
        </div>
      ) : usageData ? (
        <>
          {usageData.rate_limiting_enabled ? (
            <div className="space-y-3">
              {/* Usage Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-700 mb-1">Hourly Usage</div>
                  <div className="text-lg font-semibold text-black">${usageData.current_hourly_usage.toFixed(2)}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-700 mb-1">Remaining</div>
                  <div className="text-lg font-semibold text-black">${usageData.remaining_budget.toFixed(2)}</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(usageData.percentage_used)}`}
                    style={{ width: `${Math.min(usageData.percentage_used, 100)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span>
                    {usageData.percentage_used.toFixed(1)}% of ${usageData.hourly_limit} limit used
                  </span>
                </div>
              </div>

              {/* Warnings */}
              {usageData.percentage_used > 95 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="text-red-800 text-sm font-medium">Very close to usage limit!</div>
                </div>
              )}
              {usageData.percentage_used > 80 && usageData.percentage_used <= 95 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="text-yellow-800 text-sm font-medium">Approaching usage limit!</div>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-blue-800 text-sm">$10/hour limit prevents abuse</div>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="text-yellow-800 text-sm">Rate limiting not enabled</div>
            </div>
          )}
        </>
      ) : loading ? (
        <div className="flex items-center justify-center py-4">
          <RefreshCw className="w-4 h-4 animate-spin mr-2" />
          <span className="text-sm text-gray-600">Loading usage data...</span>
        </div>
      ) : (
        <div className="text-sm text-gray-600">
          <p>Usage tracking: API not available</p>
          <p className="text-xs mt-1">Rate limiting active in production</p>
        </div>
      )}
    </div>
  );
}
