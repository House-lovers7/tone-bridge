package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/sony/gobreaker"
	"go.uber.org/zap"

	"github.com/tonebridge/api-gateway/internal/config"
)

type ProxyService struct {
	config         *config.Config
	httpClient     *http.Client
	circuitBreaker map[string]*gobreaker.CircuitBreaker
	logger         *zap.SugaredLogger
}

func NewProxyService(cfg *config.Config, logger *zap.SugaredLogger) *ProxyService {
	// Create HTTP client with connection pooling
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
		DisableCompression:  false,
	}

	httpClient := &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second,
	}

	// Initialize circuit breakers for each service
	circuitBreakers := make(map[string]*gobreaker.CircuitBreaker)
	
	services := map[string]string{
		"transform":     cfg.TransformServiceURL,
		"analyze":       cfg.AnalyzeServiceURL,
		"auto-transform": cfg.AutoTransformServiceURL,
		"ml":            cfg.MLServiceURL,
	}

	for name := range services {
		circuitBreakers[name] = gobreaker.NewCircuitBreaker(gobreaker.Settings{
			Name:        name,
			MaxRequests: 3,
			Interval:    10 * time.Second,
			Timeout:     60 * time.Second,
			ReadyToTrip: func(counts gobreaker.Counts) bool {
				failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
				return counts.Requests >= 3 && failureRatio >= 0.6
			},
			OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
				logger.Infof("Circuit breaker %s: %s -> %s", name, from, to)
			},
		})
	}

	return &ProxyService{
		config:         cfg,
		httpClient:     httpClient,
		circuitBreaker: circuitBreakers,
		logger:         logger,
	}
}

// ProxyRequest forwards a request to a backend service
func (s *ProxyService) ProxyRequest(ctx context.Context, service string, method string, path string, body interface{}, headers map[string]string) (interface{}, error) {
	// Get service URL
	serviceURL := s.getServiceURL(service)
	if serviceURL == "" {
		return nil, fmt.Errorf("unknown service: %s", service)
	}

	url := serviceURL + path

	// Prepare request body
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonBody)
	}

	// Execute with circuit breaker
	result, err := s.circuitBreaker[service].Execute(func() (interface{}, error) {
		return s.executeRequest(ctx, method, url, reqBody, headers)
	})

	if err != nil {
		s.logger.Errorf("Proxy request failed for %s: %v", service, err)
		return nil, err
	}

	return result, nil
}

func (s *ProxyService) executeRequest(ctx context.Context, method string, url string, body io.Reader, headers map[string]string) (interface{}, error) {
	// Create request
	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	for key, value := range headers {
		req.Header.Set(key, value)
	}

	// Add tracing headers
	if requestID := ctx.Value("request_id"); requestID != nil {
		req.Header.Set("X-Request-ID", requestID.(string))
	}

	// Execute request
	startTime := time.Now()
	resp, err := s.httpClient.Do(req)
	duration := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Log request
	s.logger.Debugf("Proxy request: %s %s -> %d (%v)", method, url, resp.StatusCode, duration)

	// Read response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	// Check status code
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("service returned error: %d - %s", resp.StatusCode, string(respBody))
	}

	// Parse response
	var result interface{}
	if err := json.Unmarshal(respBody, &result); err != nil {
		// Return raw response if not JSON
		return string(respBody), nil
	}

	return result, nil
}

func (s *ProxyService) getServiceURL(service string) string {
	switch service {
	case "transform":
		return s.config.TransformServiceURL
	case "analyze":
		return s.config.AnalyzeServiceURL
	case "auto-transform":
		return s.config.AutoTransformServiceURL
	case "ml":
		return s.config.MLServiceURL
	default:
		return ""
	}
}

// TransformText proxies a transform request
func (s *ProxyService) TransformText(ctx context.Context, request map[string]interface{}) (interface{}, error) {
	return s.ProxyRequest(ctx, "transform", "POST", "/transform", request, nil)
}

// AnalyzeText proxies an analyze request
func (s *ProxyService) AnalyzeText(ctx context.Context, request map[string]interface{}) (interface{}, error) {
	return s.ProxyRequest(ctx, "analyze", "POST", "/analyze", request, nil)
}

// EvaluateAutoTransform proxies an auto-transform evaluation request
func (s *ProxyService) EvaluateAutoTransform(ctx context.Context, request map[string]interface{}) (interface{}, error) {
	return s.ProxyRequest(ctx, "auto-transform", "POST", "/evaluate", request, nil)
}

// GetServiceHealth checks the health of a backend service
func (s *ProxyService) GetServiceHealth(service string) (bool, error) {
	serviceURL := s.getServiceURL(service)
	if serviceURL == "" {
		return false, fmt.Errorf("unknown service: %s", service)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	resp, err := s.httpClient.Get(serviceURL + "/health")
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK, nil
}

// GetAllServicesHealth checks the health of all backend services
func (s *ProxyService) GetAllServicesHealth() map[string]bool {
	services := []string{"transform", "analyze", "auto-transform", "ml"}
	health := make(map[string]bool)

	for _, service := range services {
		healthy, _ := s.GetServiceHealth(service)
		health[service] = healthy
	}

	return health
}