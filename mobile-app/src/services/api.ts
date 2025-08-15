import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';
import Toast from 'react-native-toast-message';

// API configuration
const API_URL = __DEV__ 
  ? Constants.expoConfig?.extra?.devApiUrl || 'http://localhost:8082'
  : Constants.expoConfig?.extra?.apiUrl || 'https://api.tonebridge.io';

const API_VERSION = '/api/v1';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
        if (refreshToken) {
          const response = await axios.post(`${API_URL}${API_VERSION}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access_token);
          await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
        
        Toast.show({
          type: 'error',
          text1: 'セッション期限切れ',
          text2: 'もう一度ログインしてください',
        });

        // Navigate to login screen (handled by auth context)
        return Promise.reject(refreshError);
      }
    }

    // Show error toast for other errors
    if (error.response && error.response.status !== 401) {
      const errorMessage = (error.response.data as any)?.message || 'エラーが発生しました';
      Toast.show({
        type: 'error',
        text1: 'エラー',
        text2: errorMessage,
      });
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    const { access_token, refresh_token, user } = response.data;
    
    await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);
    
    return { user, access_token };
  },

  register: async (data: {
    email: string;
    password: string;
    name: string;
    organization?: string;
  }) => {
    const response = await apiClient.post('/auth/register', data);
    const { access_token, refresh_token, user } = response.data;
    
    await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh_token);
    
    return { user, access_token };
  },

  logout: async () => {
    await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
  },

  getProfile: async () => {
    const response = await apiClient.get('/profile');
    return response.data;
  },

  updateProfile: async (data: Partial<{
    name: string;
    email: string;
    organization: string;
    preferences: any;
  }>) => {
    const response = await apiClient.put('/profile', data);
    return response.data;
  },
};

// Transform API
export const transformAPI = {
  transform: async (data: {
    text: string;
    type: 'soften' | 'clarify' | 'structure' | 'summarize' | 'terminology' | 'requirements' | 'background';
    options?: {
      tone_level?: number;
      target_audience?: string;
      context?: string;
    };
  }) => {
    const response = await apiClient.post('/transform', data);
    return response.data;
  },

  analyze: async (text: string) => {
    const response = await apiClient.post('/analyze', { text });
    return response.data;
  },

  getHistory: async (params?: {
    limit?: number;
    offset?: number;
    type?: string;
  }) => {
    const response = await apiClient.get('/history', { params });
    return response.data;
  },

  getTransformation: async (id: string) => {
    const response = await apiClient.get(`/transformations/${id}`);
    return response.data;
  },
};

// Advanced Transform API
export const advancedTransformAPI = {
  structureRequirements: async (text: string, context?: string) => {
    const response = await apiClient.post('/advanced/structure-requirements', {
      text,
      context,
    });
    return response.data;
  },

  completeBackground: async (text: string, context?: string) => {
    const response = await apiClient.post('/advanced/complete-background', {
      text,
      context,
    });
    return response.data;
  },

  scorePriority: async (messages: string[]) => {
    const response = await apiClient.post('/advanced/batch-score-priorities', {
      messages,
    });
    return response.data;
  },

  adjustTone: async (text: string, intensity: number, style?: string) => {
    const response = await apiClient.post('/advanced/adjust-tone', {
      text,
      intensity,
      style,
    });
    return response.data;
  },

  getTonePresets: async () => {
    const response = await apiClient.get('/advanced/tone-presets');
    return response.data;
  },
};

// Dictionary API
export const dictionaryAPI = {
  getDictionaries: async () => {
    const response = await apiClient.get('/dictionaries');
    return response.data;
  },

  createDictionary: async (data: {
    name: string;
    description?: string;
    terms: Array<{ original: string; replacement: string }>;
  }) => {
    const response = await apiClient.post('/dictionaries', data);
    return response.data;
  },

  updateDictionary: async (id: string, data: Partial<{
    name: string;
    description: string;
    terms: Array<{ original: string; replacement: string }>;
  }>) => {
    const response = await apiClient.put(`/dictionaries/${id}`, data);
    return response.data;
  },

  deleteDictionary: async (id: string) => {
    await apiClient.delete(`/dictionaries/${id}`);
  },
};

// WebSocket connection
export const createWebSocketConnection = (token: string) => {
  const WS_URL = __DEV__ 
    ? 'ws://localhost:3001'
    : 'wss://ws.tonebridge.io';

  const socket = require('socket.io-client').io(WS_URL, {
    auth: { token },
    transports: ['websocket'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  });

  return socket;
};

export default apiClient;