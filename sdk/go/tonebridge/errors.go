package tonebridge

import (
	"errors"
	"fmt"
)

var (
	// ErrNoRefreshToken is returned when no refresh token is available
	ErrNoRefreshToken = errors.New("no refresh token available")
	
	// ErrInvalidInput is returned when input validation fails
	ErrInvalidInput = errors.New("invalid input")
	
	// ErrTextRequired is returned when text is required but not provided
	ErrTextRequired = errors.New("text is required")
	
	// ErrTextTooLong is returned when text exceeds maximum length
	ErrTextTooLong = errors.New("text exceeds maximum length")
	
	// ErrInvalidIntensity is returned when intensity is out of valid range
	ErrInvalidIntensity = errors.New("intensity must be between 0 and 3")
	
	// ErrNoConnection is returned when WebSocket is not connected
	ErrNoConnection = errors.New("no connection established")
)

// ToneBridgeError represents an API error
type ToneBridgeError struct {
	StatusCode int                    `json:"status_code"`
	Message    string                 `json:"message"`
	Code       string                 `json:"code,omitempty"`
	Details    map[string]interface{} `json:"details,omitempty"`
}

// Error implements the error interface
func (e *ToneBridgeError) Error() string {
	if e.Code != "" {
		return fmt.Sprintf("[%s] %s (status: %d)", e.Code, e.Message, e.StatusCode)
	}
	return fmt.Sprintf("%s (status: %d)", e.Message, e.StatusCode)
}

// Is checks if the error has a specific code
func (e *ToneBridgeError) Is(code string) bool {
	return e.Code == code
}

// APIError represents the error response from the API
type APIError struct {
	Error   string                 `json:"error,omitempty"`
	Message string                 `json:"message"`
	Code    string                 `json:"code,omitempty"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// AuthenticationError represents an authentication error
type AuthenticationError struct {
	*ToneBridgeError
}

// NewAuthenticationError creates a new authentication error
func NewAuthenticationError(message string) *AuthenticationError {
	return &AuthenticationError{
		ToneBridgeError: &ToneBridgeError{
			StatusCode: 401,
			Message:    message,
			Code:       "AUTH_FAILED",
		},
	}
}

// AuthorizationError represents an authorization error
type AuthorizationError struct {
	*ToneBridgeError
}

// NewAuthorizationError creates a new authorization error
func NewAuthorizationError(message string) *AuthorizationError {
	return &AuthorizationError{
		ToneBridgeError: &ToneBridgeError{
			StatusCode: 403,
			Message:    message,
			Code:       "AUTH_FORBIDDEN",
		},
	}
}

// ValidationError represents a validation error
type ValidationError struct {
	*ToneBridgeError
	Fields []FieldError `json:"fields,omitempty"`
}

// FieldError represents a field-specific validation error
type FieldError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// NewValidationError creates a new validation error
func NewValidationError(message string, fields ...FieldError) *ValidationError {
	return &ValidationError{
		ToneBridgeError: &ToneBridgeError{
			StatusCode: 400,
			Message:    message,
			Code:       "VALIDATION_ERROR",
		},
		Fields: fields,
	}
}

// RateLimitError represents a rate limit error
type RateLimitError struct {
	*ToneBridgeError
	RetryAfter int `json:"retry_after,omitempty"`
}

// NewRateLimitError creates a new rate limit error
func NewRateLimitError(message string, retryAfter int) *RateLimitError {
	return &RateLimitError{
		ToneBridgeError: &ToneBridgeError{
			StatusCode: 429,
			Message:    message,
			Code:       "RATE_LIMIT_EXCEEDED",
		},
		RetryAfter: retryAfter,
	}
}

// ServerError represents a server error
type ServerError struct {
	*ToneBridgeError
}

// NewServerError creates a new server error
func NewServerError(message string, statusCode int) *ServerError {
	return &ServerError{
		ToneBridgeError: &ToneBridgeError{
			StatusCode: statusCode,
			Message:    message,
			Code:       "SERVER_ERROR",
		},
	}
}