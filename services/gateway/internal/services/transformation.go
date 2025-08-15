package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
	"github.com/sony/gobreaker"
	"go.uber.org/zap"

	"github.com/tonebridge/gateway/internal/models"
	"github.com/tonebridge/gateway/internal/repository"
)

type TransformationService struct {
	transformRepo *repository.TransformationRepository
	redis         *redis.Client
	llmServiceURL string
	httpClient    *http.Client
	circuitBreaker *gobreaker.CircuitBreaker
	logger        *zap.SugaredLogger
}

func NewTransformationService(
	transformRepo *repository.TransformationRepository,
	redis *redis.Client,
	llmServiceURL string,
	logger *zap.SugaredLogger,
) *TransformationService {
	// Configure circuit breaker
	settings := gobreaker.Settings{
		Name:        "LLM Service",
		MaxRequests: 3,
		Interval:    10 * time.Second,
		Timeout:     30 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 3 && failureRatio >= 0.6
		},
		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			logger.Infow("Circuit breaker state changed", 
				"name", name, "from", from.String(), "to", to.String())
		},
	}
	
	cb := gobreaker.NewCircuitBreaker(settings)
	
	return &TransformationService{
		transformRepo:  transformRepo,
		redis:          redis,
		llmServiceURL:  llmServiceURL,
		httpClient:     &http.Client{Timeout: 30 * time.Second},
		circuitBreaker: cb,
		logger:         logger,
	}
}

func (s *TransformationService) TransformText(ctx context.Context, userID uuid.UUID, req *models.TransformRequest) (*models.TransformResponse, error) {
	// Create cache key
	cacheKey := fmt.Sprintf("transform:%s:%s:%s", 
		req.TransformationType, req.TargetTone, hashText(req.Text))
	
	// Check cache
	cached, err := s.redis.Get(ctx, cacheKey).Result()
	if err == nil && cached != "" {
		s.logger.Debugw("Cache hit", "key", cacheKey)
		var response models.TransformResponse
		if err := json.Unmarshal([]byte(cached), &response); err == nil {
			// Save to history even for cached results
			s.saveTransformation(ctx, userID, req, &response)
			return &response, nil
		}
	}
	
	// Call LLM service through circuit breaker
	result, err := s.circuitBreaker.Execute(func() (interface{}, error) {
		return s.callLLMService(ctx, "/transform", map[string]interface{}{
			"text":                req.Text,
			"transformation_type": req.TransformationType,
			"target_tone":         req.TargetTone,
			"options":            req.Options,
		})
	})
	
	if err != nil {
		s.logger.Errorw("LLM service call failed", "error", err)
		return nil, fmt.Errorf("transformation service unavailable: %w", err)
	}
	
	// Parse response
	var llmResponse map[string]interface{}
	if err := json.Unmarshal(result.([]byte), &llmResponse); err != nil {
		return nil, fmt.Errorf("failed to parse LLM response: %w", err)
	}
	
	response := &models.TransformResponse{
		OriginalText:    req.Text,
		TransformedText: llmResponse["transformed_text"].(string),
		Metadata:        llmResponse["metadata"].(map[string]interface{}),
	}
	
	if suggestions, ok := llmResponse["suggestions"].([]interface{}); ok {
		for _, s := range suggestions {
			response.Suggestions = append(response.Suggestions, s.(string))
		}
	}
	
	// Cache the response (24 hours)
	responseJSON, _ := json.Marshal(response)
	s.redis.Set(ctx, cacheKey, responseJSON, 24*time.Hour)
	
	// Save to database
	s.saveTransformation(ctx, userID, req, response)
	
	return response, nil
}

func (s *TransformationService) AnalyzeText(ctx context.Context, userID uuid.UUID, req *models.AnalyzeRequest) (*models.AnalyzeResponse, error) {
	// Call LLM service
	result, err := s.circuitBreaker.Execute(func() (interface{}, error) {
		return s.callLLMService(ctx, "/analyze", map[string]interface{}{
			"text": req.Text,
		})
	})
	
	if err != nil {
		s.logger.Errorw("LLM service analysis failed", "error", err)
		return nil, fmt.Errorf("analysis service unavailable: %w", err)
	}
	
	// Parse response
	var response models.AnalyzeResponse
	if err := json.Unmarshal(result.([]byte), &response); err != nil {
		return nil, fmt.Errorf("failed to parse analysis response: %w", err)
	}
	
	return &response, nil
}

func (s *TransformationService) GetUserHistory(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*models.Transformation, error) {
	return s.transformRepo.GetUserHistory(ctx, userID, limit, offset)
}

func (s *TransformationService) GetDictionaries(ctx context.Context, organization, category string) ([]*models.Dictionary, error) {
	// TODO: Implement dictionary repository and fetch
	return []*models.Dictionary{}, nil
}

func (s *TransformationService) CreateDictionary(ctx context.Context, req *models.CreateDictionaryRequest) (*models.Dictionary, error) {
	// TODO: Implement dictionary creation
	dictionary := &models.Dictionary{
		ID:         uuid.New(),
		Term:       req.Term,
		Definition: req.Definition,
		Category:   req.Category,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	
	if len(req.Alternatives) > 0 {
		alts, _ := json.Marshal(req.Alternatives)
		dictionary.Alternatives = alts
	}
	
	return dictionary, nil
}

func (s *TransformationService) UpdateDictionary(ctx context.Context, id uuid.UUID, updates map[string]interface{}) (*models.Dictionary, error) {
	// TODO: Implement dictionary update
	return nil, fmt.Errorf("not implemented")
}

func (s *TransformationService) DeleteDictionary(ctx context.Context, id uuid.UUID) error {
	// TODO: Implement dictionary deletion
	return fmt.Errorf("not implemented")
}

func (s *TransformationService) callLLMService(ctx context.Context, endpoint string, payload interface{}) ([]byte, error) {
	url := s.llmServiceURL + endpoint
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}
	
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("LLM service returned status %d: %s", resp.StatusCode, string(body))
	}
	
	return body, nil
}

func (s *TransformationService) saveTransformation(ctx context.Context, userID uuid.UUID, req *models.TransformRequest, resp *models.TransformResponse) {
	metadata, _ := json.Marshal(resp.Metadata)
	
	transformation := &models.Transformation{
		UserID:             userID,
		OriginalText:       req.Text,
		TransformedText:    resp.TransformedText,
		TransformationType: req.TransformationType,
		TargetTone:         req.TargetTone,
		Metadata:           metadata,
	}
	
	if err := s.transformRepo.Create(ctx, transformation); err != nil {
		s.logger.Errorw("Failed to save transformation", "error", err)
	}
}

func hashText(text string) string {
	// Simple hash for cache key (in production, use proper hashing)
	if len(text) > 100 {
		return text[:100]
	}
	return text
}