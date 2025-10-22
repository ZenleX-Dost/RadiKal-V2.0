'use client';

import type { Metadata } from 'next';
import { useState } from 'react';
import './globals.css';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import ToastContainer from '@/components/Toast';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <html lang="en">
      <body className="bg-gray-50 dark:bg-gray-900">
        <ErrorBoundary>
          <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <Sidebar 
              isOpen={sidebarOpen} 
              onClose={() => setSidebarOpen(false)} 
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Navbar */}
              <Navbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

              {/* Page Content */}
              <main className="flex-1 overflow-y-auto">
                <div className="container mx-auto px-4 py-6 max-w-7xl">
                  {children}
                </div>
              </main>
            </div>
          </div>

          {/* Toast Notifications */}
          <ToastContainer />
        </ErrorBoundary>
      </body>
    </html>
  );
}
