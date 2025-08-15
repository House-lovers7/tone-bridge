package tonebridge

import (
	"context"
	"fmt"
	"net/http"
)

const (
	// MaxTextLength is the maximum allowed text length
	MaxTextLength = 10000
	// DefaultIntensity is the default transformation intensity
	DefaultIntensity = 2
)

// TransformService handles text transformation operations
type TransformService struct {
	client *Client
}

// Transform performs a text transformation
func (s *TransformService) Transform(ctx context.Context, req *TransformRequest) (*TransformResponse, error) {
	if err := s.validateTransformRequest(req); err != nil {
		return nil, err
	}

	var result TransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/transform", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// Soften softens harsh language
func (s *TransformService) Soften(ctx context.Context, text string, intensity int, options *TransformOptions) (*TransformResponse, error) {
	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationSoften,
		Intensity:          intensity,
		Options:            options,
	})
}

// Clarify clarifies confusing text
func (s *TransformService) Clarify(ctx context.Context, text string, intensity int, options *TransformOptions) (*TransformResponse, error) {
	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationClarify,
		Intensity:          intensity,
		Options:            options,
	})
}

// Structure structures unorganized text
func (s *TransformService) Structure(ctx context.Context, text string, intensity int, options *TransformOptions) (*TransformResponse, error) {
	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationStructure,
		Intensity:          intensity,
		Options:            options,
	})
}

// Summarize summarizes long text
func (s *TransformService) Summarize(ctx context.Context, text string, intensity int, options *TransformOptions) (*TransformResponse, error) {
	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationSummarize,
		Intensity:          intensity,
		Options:            options,
	})
}

// TransformTerminology converts technical terminology to non-technical
func (s *TransformService) TransformTerminology(ctx context.Context, text string, options *TransformOptions) (*TransformResponse, error) {
	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationTerminology,
		Intensity:          DefaultIntensity,
		Options:            options,
	})
}

// StructureRequirements structures requirements into 4 quadrants
func (s *TransformService) StructureRequirements(ctx context.Context, text string, options *TransformOptions) (*TransformResponse, error) {
	req := map[string]interface{}{
		"text": text,
	}
	if options != nil {
		req["options"] = options
	}

	var result TransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/advanced/structure-requirements", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// CompleteBackground completes missing background information
func (s *TransformService) CompleteBackground(ctx context.Context, text string, options *TransformOptions) (*TransformResponse, error) {
	req := map[string]interface{}{
		"text": text,
	}
	if options != nil {
		req["options"] = options
	}

	var result TransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/advanced/complete-background", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AdjustTone adjusts tone with specific intensity
func (s *TransformService) AdjustTone(ctx context.Context, text string, intensity int, targetTone string) (*TransformResponse, error) {
	req := map[string]interface{}{
		"text":      text,
		"intensity": intensity,
	}
	if targetTone != "" {
		req["target_tone"] = targetTone
	}

	var result TransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/advanced/adjust-tone", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AutoDetectIntensityResult represents the auto-detect intensity result
type AutoDetectIntensityResult struct {
	Intensity  int     `json:"intensity"`
	Confidence float64 `json:"confidence"`
}

// AutoDetectIntensity auto-detects optimal transformation intensity
func (s *TransformService) AutoDetectIntensity(ctx context.Context, text string, transformationType TransformationType) (*AutoDetectIntensityResult, error) {
	req := map[string]interface{}{
		"text":                text,
		"transformation_type": transformationType,
	}

	var result AutoDetectIntensityResult
	err := s.client.Request(ctx, http.MethodPost, "/advanced/auto-detect-intensity", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// GetTonePresets gets available tone presets
func (s *TransformService) GetTonePresets(ctx context.Context) ([]TonePreset, error) {
	var result []TonePreset
	err := s.client.Request(ctx, http.MethodGet, "/advanced/tone-presets", nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// BatchTransform performs batch transformation
func (s *TransformService) BatchTransform(ctx context.Context, req *BatchTransformRequest) (*BatchTransformResponse, error) {
	if len(req.Items) == 0 {
		return nil, NewValidationError("no items to transform")
	}

	// Validate each item
	for _, item := range req.Items {
		if err := s.validateTransformRequest(&item); err != nil {
			return nil, err
		}
	}

	var result BatchTransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/transform/batch", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// CustomTransform performs transformation with custom instructions
func (s *TransformService) CustomTransform(ctx context.Context, text string, instructions string, options *TransformOptions) (*TransformResponse, error) {
	if options == nil {
		options = &TransformOptions{}
	}
	options.CustomInstructions = instructions

	return s.Transform(ctx, &TransformRequest{
		Text:               text,
		TransformationType: TransformationCustom,
		Intensity:          DefaultIntensity,
		Options:            options,
	})
}

// HistoryOptions represents options for getting history
type HistoryOptions struct {
	Limit  int `json:"limit,omitempty"`
	Offset int `json:"offset,omitempty"`
}

// GetHistory gets transformation history
func (s *TransformService) GetHistory(ctx context.Context, opts *HistoryOptions) ([]TransformationHistory, error) {
	endpoint := "/history"
	if opts != nil {
		endpoint = fmt.Sprintf("%s?limit=%d&offset=%d", endpoint, opts.Limit, opts.Offset)
	}

	var result []TransformationHistory
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// validateTransformRequest validates a transform request
func (s *TransformService) validateTransformRequest(req *TransformRequest) error {
	if req.Text == "" {
		return ErrTextRequired
	}

	if len(req.Text) > MaxTextLength {
		return ErrTextTooLong
	}

	if req.TransformationType == "" {
		return NewValidationError("transformation type is required")
	}

	if req.Intensity < 0 || req.Intensity > 3 {
		return ErrInvalidIntensity
	}

	return nil
}