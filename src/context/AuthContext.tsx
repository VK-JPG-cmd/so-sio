import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { authService, apiClient } from '../services/api';

interface AuthContextType {
  user: User | null;
  role: UserRole;
  isDemoMode: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  switchRole: (role: UserRole) => void;
  toggleDemoMode: () => void;
  signOut: () => Promise<void>;
  loginCustomerWithOtp: (phone: string, otp: string) => Promise<void>;
  loginBrandOwner: (email: string, password?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(apiClient.isMockMode);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error('Error loading current user', err);
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const switchRole = (newRole: UserRole) => {
    const newUser = authService.switchUserRole(newRole);
    setUser(newUser);
  };

  const toggleDemoMode = () => {
    const next = !isDemoMode;
    setIsDemoMode(next);
    apiClient.setMockMode(next);
  };

  const loginCustomerWithOtp = async (phone: string, otp: string) => {
    setIsLoading(true);
    try {
      const res = await authService.customerSignInWithPhone(phone, otp);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const loginBrandOwner = async (email: string, password?: string) => {
    setIsLoading(true);
    try {
      const res = await authService.brandOwnerSignIn(email, password);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    await authService.signOut();
    setUser(null);
  };

  const role: UserRole = user?.role || 'guest';

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isDemoMode,
        isLoading,
        setUser,
        switchRole,
        toggleDemoMode,
        signOut,
        loginCustomerWithOtp,
        loginBrandOwner
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
