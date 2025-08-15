/**
 * Type definitions for ToneBridge SDK
 */

// Configuration
export interface ToneBridgeConfig {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
  maxRetries?: number;
  version?: string;
  enableWebSocket?: boolean;
  // Callbacks
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (data: any) => void;
  onError?: (error: Error) => void;
}

// Authentication
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

// Transformation
export interface TransformRequest {
  text: string;
  transformation_type: TransformationType;
  intensity?: number; // 0-3
  options?: TransformOptions;
  metadata?: Record<string, any>;
}

export interface TransformOptions {
  preserve_formatting?: boolean;
  include_signature?: boolean;
  target_audience?: string;
  custom_instructions?: string;
  language?: string;
}

export interface TransformResponse {
  success: boolean;
  data: {
    original_text: string;
    transformed_text: string;
    transformation_type: string;
    intensity: number;
    suggestions?: string[];
    metadata?: Record<string, any>;
    processing_time_ms?: number;
  };
}

export type TransformationType = 
  | 'soften'
  | 'clarify'
  | 'structure'
  | 'summarize'
  | 'terminology'
  | 'requirement_structuring'
  | 'background_completion'
  | 'custom';

// Analysis
export interface AnalyzeRequest {
  text: string;
  analysis_types?: AnalysisType[];
  include_suggestions?: boolean;
  metadata?: Record<string, any>;
}

export interface AnalyzeResponse {
  success: boolean;
  data: {
    text: string;
    tone: string;
    clarity_score: number;
    priority: Priority;
    priority_quadrant?: string;
    sentiment: {
      polarity: number;
      subjectivity: number;
    };
    suggestions?: string[];
    improvements?: string[];
    metadata?: Record<string, any>;
  };
}

export type AnalysisType = 
  | 'tone'
  | 'clarity'
  | 'priority'
  | 'sentiment'
  | 'structure'
  | 'completeness';

export type Priority = 'critical' | 'high' | 'medium' | 'low';

// Auto-Transform
export interface AutoTransformConfig {
  enabled: boolean;
  default_transformation_type: TransformationType;
  default_intensity: number;
  min_message_length: number;
  max_processing_delay_ms: number;
  require_confirmation: boolean;
  show_preview: boolean;
  preserve_original: boolean;
}

export interface AutoTransformRule {
  id?: string;
  rule_name: string;
  description?: string;
  enabled: boolean;
  priority: number;
  trigger_type: TriggerType;
  trigger_value: any;
  transformation_type: TransformationType;
  transformation_intensity: number;
  transformation_options?: TransformOptions;
  platforms?: string[];
  channels?: string[];
  user_roles?: string[];
}

export type TriggerType = 
  | 'keyword'
  | 'sentiment'
  | 'recipient'
  | 'channel'
  | 'time'
  | 'pattern';

export interface AutoTransformTemplate {
  id: string;
  template_name: string;
  category: string;
  description: string;
  rule_config: any;
  is_system: boolean;
}

export interface MessageContext {
  message: string;
  user_id: string;
  tenant_id: string;
  platform: string;
  channel_id?: string;
  recipient_ids?: string[];
  metadata?: Record<string, any>;
}

export interface TransformationResult {
  should_transform: boolean;
  rule_id?: string;
  rule_name?: string;
  transformation_type: TransformationType;
  transformation_intensity: number;
  transformation_options?: TransformOptions;
  confidence: number;
  reason?: string;
}

// Batch operations
export interface BatchTransformRequest {
  items: TransformRequest[];
  parallel?: boolean;
  stop_on_error?: boolean;
}

export interface BatchTransformResponse {
  success: boolean;
  results: TransformResponse[];
  failed_count: number;
  total_processing_time_ms: number;
}

// History
export interface TransformationHistory {
  id: string;
  user_id: string;
  original_text: string;
  transformed_text: string;
  transformation_type: string;
  intensity: number;
  created_at: string;
  metadata?: Record<string, any>;
}

// Dictionaries
export interface Dictionary {
  id: string;
  name: string;
  description?: string;
  entries: DictionaryEntry[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DictionaryEntry {
  original: string;
  replacement: string;
  context?: string;
  case_sensitive?: boolean;
}

// WebSocket
export interface WebSocketConfig {
  url: string;
  token?: string;
  reconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

export interface WebSocketMessage {
  type: 'transform' | 'analyze' | 'notification' | 'error';
  data: any;
  timestamp: string;
  id: string;
}

// Errors
export interface ErrorDetails {
  field?: string;
  reason?: string;
  suggestion?: string;
}