/**
 * Zustand store for authentication state.
 * Integrates with backend user API for role-based authentication.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const API_BASE = 'http://localhost:8000/api/users';

interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string;
  role: 'manager' | 'project_chief' | 'technician';
  is_active: boolean;
}

interface ReviewerItem {
  id: number;
  username: string;
  full_name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  sessionToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, fullName: string, role: string, email?: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  getAvailableReviewers: () => Promise<ReviewerItem[]>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      sessionToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
          }

          set({
            user: data.user,
            sessionToken: data.session_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          set({
            error: error.message || 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      register: async (username: string, password: string, fullName: string, role: string, email?: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              username,
              password,
              full_name: fullName,
              role,
              email: email || null,
            }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
          }

          // Auto-login after registration
          await get().login(username, password);
        } catch (error: any) {
          set({
            error: error.message || 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        const { sessionToken } = get();

        if (sessionToken) {
          try {
            await fetch(`${API_BASE}/logout?session_token=${sessionToken}`, {
              method: 'POST',
            });
          } catch (error) {
            console.error('Logout error:', error);
          }
        }

        set({
          user: null,
          sessionToken: null,
          isAuthenticated: false,
          error: null,
        });
      },

      fetchCurrentUser: async () => {
        const { sessionToken } = get();

        if (!sessionToken) {
          set({ user: null, isAuthenticated: false });
          return;
        }

        try {
          const response = await fetch(`${API_BASE}/me?session_token=${sessionToken}`);

          if (response.ok) {
            const user = await response.json();
            set({ user, isAuthenticated: true });
          } else {
            // Session expired
            set({ user: null, sessionToken: null, isAuthenticated: false });
          }
        } catch (error) {
          console.error('Failed to fetch user:', error);
          set({ user: null, sessionToken: null, isAuthenticated: false });
        }
      },

      getAvailableReviewers: async (): Promise<ReviewerItem[]> => {
        const { user } = get();

        try {
          const url = user
            ? `${API_BASE}/reviewers?exclude_user_id=${user.id}`
            : `${API_BASE}/reviewers`;

          const response = await fetch(url);

          if (response.ok) {
            return await response.json();
          }
          return [];
        } catch (error) {
          console.error('Failed to fetch reviewers:', error);
          return [];
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        sessionToken: state.sessionToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
