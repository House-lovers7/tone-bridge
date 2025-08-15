/**
 * Constants for ToneBridge SDK
 */

import { ToneBridgeConfig } from './types';

export const DEFAULT_CONFIG: ToneBridgeConfig = {
  baseUrl: 'https://api.tonebridge.io/api/v1',
  timeout: 30000, // 30 seconds
  maxRetries: 3,
  version: '1.0.0',
  enableWebSocket: false
};

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  REFRESH: '/auth/refresh',
  LOGOUT: '/auth/logout',
  
  // Profile
  PROFILE: '/profile',
  
  // Transform
  TRANSFORM: '/transform',
  BATCH_TRANSFORM: '/transform/batch',
  
  // Analyze
  ANALYZE: '/analyze',
  
  // Advanced
  STRUCTURE_REQUIREMENTS: '/advanced/structure-requirements',
  COMPLETE_BACKGROUND: '/advanced/complete-background',
  SCORE_PRIORITY: '/advanced/score-priority',
  BATCH_SCORE_PRIORITIES: '/advanced/batch-score-priorities',
  ADJUST_TONE: '/advanced/adjust-tone',
  AUTO_DETECT_INTENSITY: '/advanced/auto-detect-intensity',
  TONE_PRESETS: '/advanced/tone-presets',
  
  // Auto-transform
  AUTO_EVALUATE: '/auto-transform/evaluate',
  AUTO_TRANSFORM: '/auto-transform/transform',
  AUTO_CONFIG: '/auto-transform/config',
  AUTO_RULES: '/auto-transform/rules',
  AUTO_TEMPLATES: '/auto-transform/templates',
  
  // History
  HISTORY: '/history',
  
  // Dictionaries
  DICTIONARIES: '/dictionaries'
};

export const TRANSFORMATION_TYPES = {
  SOFTEN: 'soften',
  CLARIFY: 'clarify',
  STRUCTURE: 'structure',
  SUMMARIZE: 'summarize',
  TERMINOLOGY: 'terminology',
  REQUIREMENT_STRUCTURING: 'requirement_structuring',
  BACKGROUND_COMPLETION: 'background_completion',
  CUSTOM: 'custom'
} as const;

export const TRIGGER_TYPES = {
  KEYWORD: 'keyword',
  SENTIMENT: 'sentiment',
  RECIPIENT: 'recipient',
  CHANNEL: 'channel',
  TIME: 'time',
  PATTERN: 'pattern'
} as const;

export const PRIORITY_LEVELS = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
} as const;

export const ANALYSIS_TYPES = {
  TONE: 'tone',
  CLARITY: 'clarity',
  PRIORITY: 'priority',
  SENTIMENT: 'sentiment',
  STRUCTURE: 'structure',
  COMPLETENESS: 'completeness'
} as const;

export const PLATFORMS = {
  SLACK: 'slack',
  TEAMS: 'teams',
  DISCORD: 'discord',
  OUTLOOK: 'outlook',
  WEB: 'web'
} as const;

export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  MESSAGE: 'message',
  ERROR: 'error',
  TRANSFORM: 'transform',
  ANALYZE: 'analyze',
  NOTIFICATION: 'notification'
} as const;

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  RATE_LIMITED: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503
} as const;

export const DEFAULT_INTENSITY = 2;
export const MIN_INTENSITY = 0;
export const MAX_INTENSITY = 3;

export const DEFAULT_MIN_MESSAGE_LENGTH = 50;
export const DEFAULT_MAX_PROCESSING_DELAY = 500;

export const MAX_BATCH_SIZE = 100;
export const MAX_TEXT_LENGTH = 10000;