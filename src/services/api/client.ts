export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')
    ? 'https://so-sio-backend.onrender.com/api/v1'
    : 'http://localhost:8000/api/v1');

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

export class ApiClient {
  private baseUrl: string;
  private token: string | null = null;
  public isMockMode: boolean = true;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.token = typeof localStorage !== 'undefined' ? localStorage.getItem('brandshield_token') : null;
    
    // Check if backend is explicitly configured or disabled
    const mockOverride = typeof localStorage !== 'undefined' ? localStorage.getItem('brandshield_force_demo') : null;
    if (mockOverride !== null) {
      this.isMockMode = mockOverride === 'true';
    } else {
      // Connect to real backend by default (with seamless fallback if offline)
      this.isMockMode = false;
    }
  }

  public async checkHealth(): Promise<{ ok: boolean; data?: any }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        return { ok: true, data };
      }
      return { ok: false };
    } catch {
      return { ok: false };
    }
  }

  public setToken(token: string | null) {
    this.token = token;
    if (typeof localStorage !== 'undefined') {
      if (token) {
        localStorage.setItem('brandshield_token', token);
      } else {
        localStorage.removeItem('brandshield_token');
      }
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public setMockMode(enabled: boolean) {
    this.isMockMode = enabled;
    localStorage.setItem('brandshield_force_demo', String(enabled));
  }

  public async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...restOptions } = options;
    
    let url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null) {
          searchParams.append(key, String(val));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const authHeaders: Record<string, string> = {};
    if (this.token) {
      authHeaders['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...authHeaders,
          ...headers,
        },
        ...restOptions,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message =
          errorData.error?.message ||
          errorData.detail ||
          errorData.message ||
          `HTTP Error ${response.status}: ${response.statusText}`;
        throw new Error(message);
      }

      return await response.json();
    } catch (err: any) {
      console.warn(`[BrandShield API] Backend request failed (${endpoint}):`, err.message);
      throw err;
    }
  }
}

export const apiClient = new ApiClient();
