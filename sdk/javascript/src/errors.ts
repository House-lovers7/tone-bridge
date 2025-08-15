/**
 * Custom error classes for ToneBridge SDK
 */

export class ToneBridgeError extends Error {
  public readonly statusCode: number;
  public readonly code?: string;
  public readonly details?: any;

  constructor(
    message: string,
    statusCode: number = 0,
    code?: string,
    details?: any
  ) {
    super(message);
    this.name = 'ToneBridgeError';
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;

    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ToneBridgeError);
    }
  }

  /**
   * Check if error is a specific type
   */
  is(code: string): boolean {
    return this.code === code;
  }

  /**
   * Convert to JSON
   */
  toJSON(): object {
    return {
      name: this.name,
      message: this.message,
      statusCode: this.statusCode,
      code: this.code,
      details: this.details
    };
  }
}

/**
 * Authentication error
 */
export class AuthenticationError extends ToneBridgeError {
  constructor(message: string = 'Authentication failed', details?: any) {
    super(message, 401, 'AUTH_FAILED', details);
    this.name = 'AuthenticationError';
  }
}

/**
 * Authorization error
 */
export class AuthorizationError extends ToneBridgeError {
  constructor(message: string = 'Authorization failed', details?: any) {
    super(message, 403, 'AUTH_FORBIDDEN', details);
    this.name = 'AuthorizationError';
  }
}

/**
 * Validation error
 */
export class ValidationError extends ToneBridgeError {
  constructor(message: string = 'Validation failed', details?: any) {
    super(message, 400, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
  }
}

/**
 * Rate limit error
 */
export class RateLimitError extends ToneBridgeError {
  public readonly retryAfter?: number;

  constructor(
    message: string = 'Rate limit exceeded',
    retryAfter?: number,
    details?: any
  ) {
    super(message, 429, 'RATE_LIMIT_EXCEEDED', details);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

/**
 * Network error
 */
export class NetworkError extends ToneBridgeError {
  constructor(message: string = 'Network error', details?: any) {
    super(message, 0, 'NETWORK_ERROR', details);
    this.name = 'NetworkError';
  }
}

/**
 * Timeout error
 */
export class TimeoutError extends ToneBridgeError {
  constructor(message: string = 'Request timeout', details?: any) {
    super(message, 408, 'TIMEOUT', details);
    this.name = 'TimeoutError';
  }
}

/**
 * Server error
 */
export class ServerError extends ToneBridgeError {
  constructor(
    message: string = 'Internal server error',
    statusCode: number = 500,
    details?: any
  ) {
    super(message, statusCode, 'SERVER_ERROR', details);
    this.name = 'ServerError';
  }
}

/**
 * WebSocket error
 */
export class WebSocketError extends ToneBridgeError {
  constructor(message: string = 'WebSocket error', details?: any) {
    super(message, 0, 'WEBSOCKET_ERROR', details);
    this.name = 'WebSocketError';
  }
}