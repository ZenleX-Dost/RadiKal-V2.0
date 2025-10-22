'use client';

/**
 * Settings Page
 */

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Save, User, Settings as SettingsIcon, Bell } from 'lucide-react';

// Define settings interface
interface UserSettings {
  displayName: string;
  email: string;
  apiUrl: string;
  confidenceThreshold: number;
  notifications: boolean;
  notificationEmail: string;
  sendAfterAnalysis: boolean;
  sendDailySummary: boolean;
  notifyHighSeverityOnly: boolean;
}

export default function SettingsPage() {
  const [mounted, setMounted] = useState(false);
  const [displayName, setDisplayName] = useState('User');
  const [email, setEmail] = useState('user@example.com');
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const [notifications, setNotifications] = useState(true);
  const [notificationEmail, setNotificationEmail] = useState('');
  const [sendAfterAnalysis, setSendAfterAnalysis] = useState(true);
  const [sendDailySummary, setSendDailySummary] = useState(false);
  const [notifyHighSeverityOnly, setNotifyHighSeverityOnly] = useState(true);

  // Load settings from localStorage on mount
  useEffect(() => {
    setMounted(true);
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      try {
        const settings: UserSettings = JSON.parse(savedSettings);
        setDisplayName(settings.displayName || 'User');
        setEmail(settings.email || 'user@example.com');
        setApiUrl(settings.apiUrl || 'http://localhost:8000');
        setConfidenceThreshold(settings.confidenceThreshold || 0.5);
        setNotifications(settings.notifications !== undefined ? settings.notifications : true);
        setNotificationEmail(settings.notificationEmail || '');
        setSendAfterAnalysis(settings.sendAfterAnalysis !== undefined ? settings.sendAfterAnalysis : true);
        setSendDailySummary(settings.sendDailySummary || false);
        setNotifyHighSeverityOnly(settings.notifyHighSeverityOnly !== undefined ? settings.notifyHighSeverityOnly : true);
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    }
  }, []);

  const handleSave = () => {
    // Save all settings to localStorage
    const settings: UserSettings = {
      displayName,
      email,
      apiUrl,
      confidenceThreshold,
      notifications,
      notificationEmail,
      sendAfterAnalysis,
      sendDailySummary,
      notifyHighSeverityOnly,
    };
    
    localStorage.setItem('userSettings', JSON.stringify(settings));
    alert('Settings saved successfully!');
  };

  // Prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Settings</h1>
          <p className="text-gray-600 dark:text-gray-300">Manage your application preferences</p>
        </div>

        {/* User Profile */}
        <Card variant="elevated" className="mb-6">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <User className="h-5 w-5 text-gray-600" />
              <CardTitle>User Profile</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card variant="elevated" className="mb-6">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <SettingsIcon className="h-5 w-5 text-gray-600" />
              <CardTitle>API Configuration</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Backend API URL
                </label>
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card variant="elevated" className="mb-6">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Bell className="h-5 w-5 text-gray-600" />
              <CardTitle>Email Notifications</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">Enable email notifications</span>
                <button
                  onClick={() => setNotifications(!notifications)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifications ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              
              {notifications && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-4 animate-fade-in">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Notification Email
                    </label>
                    <input
                      type="email"
                      value={notificationEmail}
                      onChange={(e) => setNotificationEmail(e.target.value)}
                      placeholder="your-email@example.com"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Analysis results will be sent to this email address
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={sendAfterAnalysis}
                        onChange={(e) => setSendAfterAnalysis(e.target.checked)}
                        className="rounded" 
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Send email after each analysis</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={sendDailySummary}
                        onChange={(e) => setSendDailySummary(e.target.checked)}
                        className="rounded" 
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Send daily summary report</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={notifyHighSeverityOnly}
                        onChange={(e) => setNotifyHighSeverityOnly(e.target.checked)}
                        className="rounded" 
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Notify only for high-severity defects</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button variant="primary" size="lg" onClick={handleSave}>
            <Save className="h-5 w-5 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  );
}
