'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, Role, TokenResponse } from '@moc-healthy/contracts';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: Role) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('moc_access_token');
    const storedUser = localStorage.getItem('moc_user_profile');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('moc_access_token');
        localStorage.removeItem('moc_user_profile');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        return { success: false, error: data.detail || 'Đăng nhập không thành công' };
      }

      const tokenData = data as TokenResponse;
      setToken(tokenData.access_token);
      localStorage.setItem('moc_access_token', tokenData.access_token);
      localStorage.setItem('moc_refresh_token', tokenData.refresh_token);

      // Fetch user profile
      const meRes = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
      });

      if (meRes.ok) {
        const userProfile = (await meRes.json()) as UserProfile;
        setUser(userProfile);
        localStorage.setItem('moc_user_profile', JSON.stringify(userProfile));
      }

      return { success: true };
    } catch (err) {
      return { success: false, error: 'Không thể kết nối đến máy chủ API' };
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem('moc_access_token');
    localStorage.removeItem('moc_refresh_token');
    localStorage.removeItem('moc_user_profile');
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.is_superuser) return true;
    if (user.roles.includes('ADMIN') || user.roles.includes('OWNER')) return true;
    return user.permissions.includes(permission);
  };

  const hasRole = (role: Role): boolean => {
    if (!user) return false;
    if (user.is_superuser || user.roles.includes('ADMIN')) return true;
    return user.roles.includes(role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        hasPermission,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
