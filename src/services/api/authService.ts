import { User, UserRole } from '../../types';
import { MOCK_USERS } from '../mockData';
import { apiClient } from './client';

export interface LoginResponse {
  user: User;
  token: string;
}

export const authService = {
  // Demo users getter
  getDemoUsers: (): User[] => {
    return MOCK_USERS;
  },

  getCurrentUser: async (): Promise<User | null> => {
    const cached = localStorage.getItem('brandshield_current_user');
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch (e) {
        // ignore
      }
    }
    // Default demo brand owner
    return MOCK_USERS[0];
  },

  startCustomerOtp: async (phone: string): Promise<{ success: boolean; message: string; cooldown_seconds: number; expires_in_seconds: number; verification_required: boolean }> => {
    const cleanPhone = phone.trim();
    try {
      return await apiClient.request<{ success: boolean; message: string; cooldown_seconds: number; expires_in_seconds: number; verification_required: boolean }>('/auth/otp/send', {
        method: 'POST',
        body: JSON.stringify({ phone_number: cleanPhone })
      });
    } catch (err: any) {
      console.warn('Backend start OTP error:', err);
      throw err;
    }
  },

  customerSignInWithPhone: async (phone: string, otp: string): Promise<LoginResponse> => {
    const cleanPhone = phone.trim();
    const cleanCode = otp.trim().replace(/\D/g, '');
    try {
      const res = await apiClient.request<any>('/auth/otp/verify', {
        method: 'POST',
        body: JSON.stringify({ phone_number: cleanPhone, code: cleanCode })
      });
      if (res && res.access_token) {
        apiClient.setToken(res.access_token);
        const userObj: User = {
          id: res.user?.id || `user_${Date.now()}`,
          name: res.user?.phone_number || cleanPhone,
          email: 'customer@brandshield.ai',
          phone: cleanPhone,
          isPhoneVerified: true,
          role: 'customer',
          createdAt: res.user?.created_at || new Date().toISOString()
        };
        localStorage.setItem('brandshield_current_user', JSON.stringify(userObj));
        return { user: userObj, token: res.access_token };
      }
      throw new Error(res?.message || 'Verification failed. Please check the code.');
    } catch (err: any) {
      console.warn('Backend verify OTP error:', err);
      throw err;
    }
  },

  brandOwnerSignIn: async (email: string, password?: string): Promise<LoginResponse> => {
    if (!apiClient.isMockMode) {
      try {
        const res = await apiClient.request<LoginResponse>('/auth/brand-owner/login', {
          method: 'POST',
          body: JSON.stringify({ email, password })
        });
        localStorage.setItem('brandshield_current_user', JSON.stringify(res.user));
        apiClient.setToken(res.token);
        return res;
      } catch (err) {
        console.warn('Falling back to mock brand owner auth', err);
      }
    }

    // Mock login
    await new Promise(r => setTimeout(r, 700));
    const user = MOCK_USERS.find(u => u.role === 'brand_owner') || MOCK_USERS[0];
    localStorage.setItem('brandshield_current_user', JSON.stringify(user));
    apiClient.setToken('mock_jwt_token_brand_owner');
    return { user, token: 'mock_jwt_token_brand_owner' };
  },

  switchUserRole: (role: UserRole): User => {
    const user = MOCK_USERS.find(u => u.role === role) || {
      id: `user_${role}_demo`,
      name: role === 'brand_owner' ? 'Elena Rostova (ApexBank)' : 'David Chen',
      email: role === 'brand_owner' ? 'elena@apexbank.com' : 'david.chen@gmail.com',
      isPhoneVerified: true,
      role: role,
      associatedBrandId: role === 'brand_owner' ? 'brand_apex_bank' : undefined,
      createdAt: new Date().toISOString()
    };
    localStorage.setItem('brandshield_current_user', JSON.stringify(user));
    return user;
  },

  signOut: async (): Promise<void> => {
    localStorage.removeItem('brandshield_current_user');
    apiClient.setToken(null);
  }
};
