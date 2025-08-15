/**
 * ToneBridge API Client
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { TransformService } from './services/transform';
import { AnalyzeService } from './services/analyze';
import { AutoTransformService } from './services/auto-transform';
import { WebSocketClient } from './websocket';
import { 
  ToneBridgeConfig, 
  AuthResponse, 
  User,
  ToneBridgeError 
} from './types';
import { DEFAULT_CONFIG } from './constants';

/**
 * Main ToneBridge client class
 * @example
 * ```typescript
 * const client = new ToneBridgeClient({
 *   apiKey: 'your-api-key',
 *   baseUrl: 'https://api.tonebridge.io'
 * });
 * ```
 */
export class ToneBridgeClient {
  private config: ToneBridgeConfig;
  private axios: AxiosInstance;
  private token?: string;
  private refreshToken?: string;
  
  // Services
  public transform: TransformService;
  public analyze: AnalyzeService;
  public autoTransform: AutoTransformService;
  public ws?: WebSocketClient;

  constructor(config: Partial<ToneBridgeConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    
    // Initialize axios instance
    this.axios = axios.create({
      baseURL: this.config.baseUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': `ToneBridge-SDK-JS/${DEFAULT_CONFIG.version}`
      }
    });

    // Add request interceptor for auth
    this.axios.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        } else if (this.config.apiKey) {
          config.headers['X-API-Key'] = this.config.apiKey;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401 && this.refreshToken) {
          // Try to refresh token
          try {
            await this.refreshAuth();
            // Retry original request
            return this.axios.request(error.config);
          } catch (refreshError) {
            throw new ToneBridgeError('Authentication failed', 401);
          }
        }
        throw this.handleError(error);
      }
    );

    // Initialize services
    this.transform = new TransformService(this.axios);
    this.analyze = new AnalyzeService(this.axios);
    this.autoTransform = new AutoTransformService(this.axios);

    // Initialize WebSocket if enabled
    if (this.config.enableWebSocket) {
      this.initWebSocket();
    }
  }

  /**
   * Authenticate with email and password
   * @param email User email
   * @param password User password
   * @returns Promise with auth response
   */
  async authenticate(email: string, password: string): Promise<AuthResponse> {
    try {
      const response = await this.axios.post<AuthResponse>('/auth/login', {
        email,
        password
      });

      this.token = response.data.access_token;
      this.refreshToken = response.data.refresh_token;

      // Reinitialize WebSocket with auth
      if (this.config.enableWebSocket && this.token) {
        this.initWebSocket();
      }

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Authenticate with API key
   * @param apiKey API key
   */
  setApiKey(apiKey: string): void {
    this.config.apiKey = apiKey;
  }

  /**
   * Set access token directly
   * @param token Access token
   */
  setAccessToken(token: string): void {
    this.token = token;
    
    // Reinitialize WebSocket with new token
    if (this.config.enableWebSocket && this.ws) {
      this.initWebSocket();
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshAuth(): Promise<AuthResponse> {
    if (!this.refreshToken) {
      throw new ToneBridgeError('No refresh token available', 401);
    }

    try {
      const response = await this.axios.post<AuthResponse>('/auth/refresh', {
        refresh_token: this.refreshToken
      });

      this.token = response.data.access_token;
      this.refreshToken = response.data.refresh_token;

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    try {
      const response = await this.axios.get<User>('/profile');
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    try {
      const response = await this.axios.put<User>('/profile', data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Logout and clear tokens
   */
  logout(): void {
    this.token = undefined;
    this.refreshToken = undefined;
    
    // Close WebSocket connection
    if (this.ws) {
      this.ws.disconnect();
    }
  }

  /**
   * Initialize WebSocket client
   */
  private initWebSocket(): void {
    const wsUrl = this.config.baseUrl?.replace('http', 'ws') + '/ws';
    
    this.ws = new WebSocketClient({
      url: wsUrl,
      token: this.token,
      reconnect: true,
      maxReconnectAttempts: this.config.maxRetries
    });

    // Set up event handlers
    this.ws.on('connected', () => {
      if (this.config.onConnect) {
        this.config.onConnect();
      }
    });

    this.ws.on('disconnected', () => {
      if (this.config.onDisconnect) {
        this.config.onDisconnect();
      }
    });

    this.ws.on('message', (data) => {
      if (this.config.onMessage) {
        this.config.onMessage(data);
      }
    });

    this.ws.on('error', (error) => {
      if (this.config.onError) {
        this.config.onError(error);
      }
    });

    this.ws.connect();
  }

  /**
   * Handle API errors
   */
  private handleError(error: any): ToneBridgeError {
    if (error.response) {
      // Server responded with error
      const { status, data } = error.response;
      return new ToneBridgeError(
        data.message || 'Request failed',
        status,
        data.code,
        data.details
      );
    } else if (error.request) {
      // Request made but no response
      return new ToneBridgeError('No response from server', 0);
    } else {
      // Request setup error
      return new ToneBridgeError(error.message || 'Request failed', 0);
    }
  }

  /**
   * Make a custom API request
   * @param config Axios request config
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.axios.request<T>(config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get axios instance for advanced usage
   */
  getAxiosInstance(): AxiosInstance {
    return this.axios;
  }
}