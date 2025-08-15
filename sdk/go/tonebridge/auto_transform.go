package tonebridge

import (
	"context"
	"fmt"
	"net/http"
)

// AutoTransformService handles auto-transformation operations
type AutoTransformService struct {
	client *Client
}

// GetConfig gets the auto-transform configuration
func (s *AutoTransformService) GetConfig(ctx context.Context) (*AutoTransformConfig, error) {
	var result AutoTransformConfig
	err := s.client.Request(ctx, http.MethodGet, "/auto-transform/config", nil, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// UpdateConfig updates the auto-transform configuration
func (s *AutoTransformService) UpdateConfig(ctx context.Context, config *AutoTransformConfig) (*AutoTransformConfig, error) {
	if config == nil {
		return nil, NewValidationError("config is required")
	}

	var result AutoTransformConfig
	err := s.client.Request(ctx, http.MethodPut, "/auto-transform/config", config, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// EnableAutoTransform enables auto-transform
func (s *AutoTransformService) EnableAutoTransform(ctx context.Context) error {
	config := &AutoTransformConfig{
		Enabled: true,
	}
	_, err := s.UpdateConfig(ctx, config)
	return err
}

// DisableAutoTransform disables auto-transform
func (s *AutoTransformService) DisableAutoTransform(ctx context.Context) error {
	config := &AutoTransformConfig{
		Enabled: false,
	}
	_, err := s.UpdateConfig(ctx, config)
	return err
}

// CreateRule creates a new auto-transform rule
func (s *AutoTransformService) CreateRule(ctx context.Context, rule *AutoTransformRule) (*AutoTransformRule, error) {
	if err := s.validateRule(rule); err != nil {
		return nil, err
	}

	var result AutoTransformRule
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/rules", rule, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// GetRule gets a specific rule by ID
func (s *AutoTransformService) GetRule(ctx context.Context, ruleID string) (*AutoTransformRule, error) {
	if ruleID == "" {
		return nil, NewValidationError("rule ID is required")
	}

	endpoint := fmt.Sprintf("/auto-transform/rules/%s", ruleID)
	var result AutoTransformRule
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ListRules lists all auto-transform rules
func (s *AutoTransformService) ListRules(ctx context.Context, filters *RuleFilters) ([]AutoTransformRule, error) {
	endpoint := "/auto-transform/rules"
	if filters != nil {
		query := ""
		if filters.Enabled != nil {
			query = fmt.Sprintf("?enabled=%v", *filters.Enabled)
		}
		if filters.TriggerType != "" {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("trigger_type=%s", filters.TriggerType)
		}
		if filters.Platform != "" {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("platform=%s", filters.Platform)
		}
		endpoint += query
	}

	var result []AutoTransformRule
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// UpdateRule updates an existing rule
func (s *AutoTransformService) UpdateRule(ctx context.Context, ruleID string, updates *AutoTransformRule) (*AutoTransformRule, error) {
	if ruleID == "" {
		return nil, NewValidationError("rule ID is required")
	}
	if updates == nil {
		return nil, NewValidationError("updates are required")
	}

	endpoint := fmt.Sprintf("/auto-transform/rules/%s", ruleID)
	var result AutoTransformRule
	err := s.client.Request(ctx, http.MethodPut, endpoint, updates, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// DeleteRule deletes a rule
func (s *AutoTransformService) DeleteRule(ctx context.Context, ruleID string) error {
	if ruleID == "" {
		return NewValidationError("rule ID is required")
	}

	endpoint := fmt.Sprintf("/auto-transform/rules/%s", ruleID)
	return s.client.Request(ctx, http.MethodDelete, endpoint, nil, nil)
}

// EnableRule enables a specific rule
func (s *AutoTransformService) EnableRule(ctx context.Context, ruleID string) error {
	updates := &AutoTransformRule{
		Enabled: true,
	}
	_, err := s.UpdateRule(ctx, ruleID, updates)
	return err
}

// DisableRule disables a specific rule
func (s *AutoTransformService) DisableRule(ctx context.Context, ruleID string) error {
	updates := &AutoTransformRule{
		Enabled: false,
	}
	_, err := s.UpdateRule(ctx, ruleID, updates)
	return err
}

// EvaluateRules evaluates rules for a given message context
func (s *AutoTransformService) EvaluateRules(ctx context.Context, messageCtx *MessageContext) (*TransformationResult, error) {
	if err := s.validateMessageContext(messageCtx); err != nil {
		return nil, err
	}

	var result TransformationResult
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/evaluate", messageCtx, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ApplyTransformation applies auto-transformation to a message
func (s *AutoTransformService) ApplyTransformation(ctx context.Context, messageCtx *MessageContext) (*AutoTransformResponse, error) {
	if err := s.validateMessageContext(messageCtx); err != nil {
		return nil, err
	}

	var result AutoTransformResponse
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/apply", messageCtx, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ListTemplates lists available auto-transform templates
func (s *AutoTransformService) ListTemplates(ctx context.Context, category string) ([]AutoTransformTemplate, error) {
	endpoint := "/auto-transform/templates"
	if category != "" {
		endpoint = fmt.Sprintf("%s?category=%s", endpoint, category)
	}

	var result []AutoTransformTemplate
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// GetTemplate gets a specific template by ID
func (s *AutoTransformService) GetTemplate(ctx context.Context, templateID string) (*AutoTransformTemplate, error) {
	if templateID == "" {
		return nil, NewValidationError("template ID is required")
	}

	endpoint := fmt.Sprintf("/auto-transform/templates/%s", templateID)
	var result AutoTransformTemplate
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ApplyTemplate applies a template to create a new rule
func (s *AutoTransformService) ApplyTemplate(ctx context.Context, templateID string, customization map[string]interface{}) (*AutoTransformRule, error) {
	if templateID == "" {
		return nil, NewValidationError("template ID is required")
	}

	req := map[string]interface{}{
		"template_id":   templateID,
		"customization": customization,
	}

	var result AutoTransformRule
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/templates/apply", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// GetHistory gets auto-transform history
func (s *AutoTransformService) GetHistory(ctx context.Context, filters *HistoryFilters) ([]AutoTransformHistory, error) {
	endpoint := "/auto-transform/history"
	if filters != nil {
		query := ""
		if filters.UserID != "" {
			query = fmt.Sprintf("?user_id=%s", filters.UserID)
		}
		if filters.RuleID != "" {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("rule_id=%s", filters.RuleID)
		}
		if filters.StartDate != "" {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("start_date=%s", filters.StartDate)
		}
		if filters.EndDate != "" {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("end_date=%s", filters.EndDate)
		}
		if filters.Limit > 0 {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("limit=%d", filters.Limit)
		}
		if filters.Offset > 0 {
			if query == "" {
				query = "?"
			} else {
				query += "&"
			}
			query += fmt.Sprintf("offset=%d", filters.Offset)
		}
		endpoint += query
	}

	var result []AutoTransformHistory
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// GetStatistics gets auto-transform statistics
func (s *AutoTransformService) GetStatistics(ctx context.Context, period string) (*AutoTransformStatistics, error) {
	endpoint := "/auto-transform/stats"
	if period != "" {
		endpoint = fmt.Sprintf("%s?period=%s", endpoint, period)
	}

	var result AutoTransformStatistics
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// TestRule tests a rule against sample text
func (s *AutoTransformService) TestRule(ctx context.Context, rule *AutoTransformRule, sampleText string) (*RuleTestResult, error) {
	if rule == nil {
		return nil, NewValidationError("rule is required")
	}
	if sampleText == "" {
		return nil, NewValidationError("sample text is required")
	}

	req := map[string]interface{}{
		"rule":        rule,
		"sample_text": sampleText,
	}

	var result RuleTestResult
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/test-rule", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ImportRules imports rules from JSON
func (s *AutoTransformService) ImportRules(ctx context.Context, rules []AutoTransformRule, overwrite bool) (*ImportResult, error) {
	if len(rules) == 0 {
		return nil, NewValidationError("no rules to import")
	}

	req := map[string]interface{}{
		"rules":     rules,
		"overwrite": overwrite,
	}

	var result ImportResult
	err := s.client.Request(ctx, http.MethodPost, "/auto-transform/import", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ExportRules exports all rules as JSON
func (s *AutoTransformService) ExportRules(ctx context.Context) ([]AutoTransformRule, error) {
	var result []AutoTransformRule
	err := s.client.Request(ctx, http.MethodGet, "/auto-transform/export", nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// validateRule validates an auto-transform rule
func (s *AutoTransformService) validateRule(rule *AutoTransformRule) error {
	if rule == nil {
		return NewValidationError("rule is required")
	}

	if rule.RuleName == "" {
		return NewValidationError("rule name is required")
	}

	if rule.TriggerType == "" {
		return NewValidationError("trigger type is required")
	}

	if rule.TransformationType == "" {
		return NewValidationError("transformation type is required")
	}

	if rule.TransformationIntensity < 0 || rule.TransformationIntensity > 3 {
		return ErrInvalidIntensity
	}

	return nil
}

// validateMessageContext validates a message context
func (s *AutoTransformService) validateMessageContext(ctx *MessageContext) error {
	if ctx == nil {
		return NewValidationError("message context is required")
	}

	if ctx.Message == "" {
		return NewValidationError("message is required")
	}

	if ctx.UserID == "" {
		return NewValidationError("user ID is required")
	}

	if ctx.Platform == "" {
		return NewValidationError("platform is required")
	}

	return nil
}

// Helper types for auto-transform operations

// RuleFilters represents filters for listing rules
type RuleFilters struct {
	Enabled     *bool       `json:"enabled,omitempty"`
	TriggerType TriggerType `json:"trigger_type,omitempty"`
	Platform    Platform    `json:"platform,omitempty"`
}

// HistoryFilters represents filters for history queries
type HistoryFilters struct {
	UserID    string `json:"user_id,omitempty"`
	RuleID    string `json:"rule_id,omitempty"`
	StartDate string `json:"start_date,omitempty"`
	EndDate   string `json:"end_date,omitempty"`
	Limit     int    `json:"limit,omitempty"`
	Offset    int    `json:"offset,omitempty"`
}

// AutoTransformResponse represents auto-transform response
type AutoTransformResponse struct {
	Success         bool                   `json:"success"`
	OriginalText    string                 `json:"original_text"`
	TransformedText string                 `json:"transformed_text"`
	RuleApplied     *AutoTransformRule     `json:"rule_applied,omitempty"`
	Confidence      float64                `json:"confidence"`
	ProcessingTime  int                    `json:"processing_time_ms"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// AutoTransformHistory represents auto-transform history entry
type AutoTransformHistory struct {
	ID              string                 `json:"id"`
	UserID          string                 `json:"user_id"`
	RuleID          string                 `json:"rule_id"`
	RuleName        string                 `json:"rule_name"`
	OriginalText    string                 `json:"original_text"`
	TransformedText string                 `json:"transformed_text"`
	Platform        Platform               `json:"platform"`
	Applied         bool                   `json:"applied"`
	Confidence      float64                `json:"confidence"`
	CreatedAt       string                 `json:"created_at"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// AutoTransformStatistics represents auto-transform statistics
type AutoTransformStatistics struct {
	Period                string                 `json:"period"`
	TotalTransformations  int                    `json:"total_transformations"`
	SuccessfulTransforms  int                    `json:"successful_transforms"`
	FailedTransforms      int                    `json:"failed_transforms"`
	AverageConfidence     float64                `json:"average_confidence"`
	AverageProcessingTime int                    `json:"average_processing_time_ms"`
	TopRules              []RuleStatistic        `json:"top_rules"`
	TransformationTypes   map[string]int         `json:"transformation_types"`
	PlatformBreakdown     map[string]int         `json:"platform_breakdown"`
	Metadata              map[string]interface{} `json:"metadata,omitempty"`
}

// RuleStatistic represents statistics for a single rule
type RuleStatistic struct {
	RuleID      string  `json:"rule_id"`
	RuleName    string  `json:"rule_name"`
	UsageCount  int     `json:"usage_count"`
	SuccessRate float64 `json:"success_rate"`
}

// RuleTestResult represents rule test result
type RuleTestResult struct {
	WouldTrigger    bool                   `json:"would_trigger"`
	TransformedText string                 `json:"transformed_text,omitempty"`
	Confidence      float64                `json:"confidence"`
	Reason          string                 `json:"reason"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// ImportResult represents import operation result
type ImportResult struct {
	Success       bool     `json:"success"`
	ImportedCount int      `json:"imported_count"`
	SkippedCount  int      `json:"skipped_count"`
	FailedCount   int      `json:"failed_count"`
	Errors        []string `json:"errors,omitempty"`
}