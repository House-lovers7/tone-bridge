package tonebridge

import (
	"context"
	"fmt"
	"net/http"
)

// AnalyzeService handles text analysis operations
type AnalyzeService struct {
	client *Client
}

// Analyze performs text analysis
func (s *AnalyzeService) Analyze(ctx context.Context, req *AnalyzeRequest) (*AnalyzeResponse, error) {
	if err := s.validateAnalyzeRequest(req); err != nil {
		return nil, err
	}

	var result AnalyzeResponse
	err := s.client.Request(ctx, http.MethodPost, "/analyze", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeTone analyzes the tone of text
func (s *AnalyzeService) AnalyzeTone(ctx context.Context, text string) (*ToneAnalysisResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result ToneAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/tone", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeClarity analyzes the clarity of text
func (s *AnalyzeService) AnalyzeClarity(ctx context.Context, text string) (*ClarityAnalysisResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result ClarityAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/clarity", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzePriority analyzes the priority of text using Eisenhower Matrix
func (s *AnalyzeService) AnalyzePriority(ctx context.Context, text string) (*PriorityScore, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result PriorityScore
	err := s.client.Request(ctx, http.MethodPost, "/analyze/priority", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeSentiment analyzes the sentiment of text
func (s *AnalyzeService) AnalyzeSentiment(ctx context.Context, text string) (*SentimentAnalysisResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result SentimentAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/sentiment", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeStructure analyzes the structure of text
func (s *AnalyzeService) AnalyzeStructure(ctx context.Context, text string) (*StructureAnalysisResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result StructureAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/structure", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeCompleteness analyzes the completeness of text
func (s *AnalyzeService) AnalyzeCompleteness(ctx context.Context, text string, requiredElements []string) (*CompletenessAnalysisResult, error) {
	req := map[string]interface{}{
		"text": text,
	}
	if len(requiredElements) > 0 {
		req["required_elements"] = requiredElements
	}

	var result CompletenessAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/completeness", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ComprehensiveAnalysis performs a comprehensive analysis of text
func (s *AnalyzeService) ComprehensiveAnalysis(ctx context.Context, text string) (*ComprehensiveAnalysisResult, error) {
	req := &AnalyzeRequest{
		Text: text,
		AnalysisTypes: []AnalysisType{
			AnalysisTone,
			AnalysisClarity,
			AnalysisPriority,
			AnalysisSentiment,
			AnalysisStructure,
			AnalysisCompleteness,
		},
		IncludeSuggestions: true,
	}

	resp, err := s.Analyze(ctx, req)
	if err != nil {
		return nil, err
	}

	// Convert to comprehensive result
	result := &ComprehensiveAnalysisResult{
		Text:         resp.Data.Text,
		Tone:         resp.Data.Tone,
		ClarityScore: resp.Data.ClarityScore,
		Priority:     resp.Data.Priority,
		Sentiment:    resp.Data.Sentiment,
		Suggestions:  resp.Data.Suggestions,
		Improvements: resp.Data.Improvements,
		Metadata:     resp.Data.Metadata,
	}

	return result, nil
}

// GetSuggestions gets improvement suggestions for text
func (s *AnalyzeService) GetSuggestions(ctx context.Context, text string, suggestionTypes []string) (*SuggestionsResult, error) {
	req := map[string]interface{}{
		"text": text,
	}
	if len(suggestionTypes) > 0 {
		req["suggestion_types"] = suggestionTypes
	}

	var result SuggestionsResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/suggestions", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ValidateGrammar validates grammar and spelling
func (s *AnalyzeService) ValidateGrammar(ctx context.Context, text string) (*GrammarValidationResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result GrammarValidationResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/grammar", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// ExtractKeyPoints extracts key points from text
func (s *AnalyzeService) ExtractKeyPoints(ctx context.Context, text string, maxPoints int) (*KeyPointsResult, error) {
	req := map[string]interface{}{
		"text": text,
	}
	if maxPoints > 0 {
		req["max_points"] = maxPoints
	}

	var result KeyPointsResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/key-points", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeAudience analyzes text for target audience appropriateness
func (s *AnalyzeService) AnalyzeAudience(ctx context.Context, text string, targetAudience string) (*AudienceAnalysisResult, error) {
	req := map[string]interface{}{
		"text":            text,
		"target_audience": targetAudience,
	}

	var result AudienceAnalysisResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/audience", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// CompareTone compares tone between two texts
func (s *AnalyzeService) CompareTone(ctx context.Context, text1, text2 string) (*ToneComparisonResult, error) {
	req := map[string]interface{}{
		"text1": text1,
		"text2": text2,
	}

	var result ToneComparisonResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/compare-tone", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// AnalyzeReadability analyzes text readability metrics
func (s *AnalyzeService) AnalyzeReadability(ctx context.Context, text string) (*ReadabilityResult, error) {
	req := map[string]interface{}{
		"text": text,
	}

	var result ReadabilityResult
	err := s.client.Request(ctx, http.MethodPost, "/analyze/readability", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// BatchAnalyze performs batch analysis
func (s *AnalyzeService) BatchAnalyze(ctx context.Context, texts []string, analysisTypes []AnalysisType) (*BatchAnalyzeResponse, error) {
	if len(texts) == 0 {
		return nil, NewValidationError("no texts to analyze")
	}

	items := make([]AnalyzeRequest, len(texts))
	for i, text := range texts {
		items[i] = AnalyzeRequest{
			Text:               text,
			AnalysisTypes:      analysisTypes,
			IncludeSuggestions: true,
		}
	}

	req := map[string]interface{}{
		"items": items,
	}

	var result BatchAnalyzeResponse
	err := s.client.Request(ctx, http.MethodPost, "/analyze/batch", req, &result)
	if err != nil {
		return nil, err
	}

	return &result, nil
}

// GetAnalysisHistory gets analysis history
func (s *AnalyzeService) GetAnalysisHistory(ctx context.Context, limit, offset int) ([]AnalysisHistory, error) {
	endpoint := fmt.Sprintf("/analyze/history?limit=%d&offset=%d", limit, offset)

	var result []AnalysisHistory
	err := s.client.Request(ctx, http.MethodGet, endpoint, nil, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// validateAnalyzeRequest validates an analyze request
func (s *AnalyzeService) validateAnalyzeRequest(req *AnalyzeRequest) error {
	if req.Text == "" {
		return ErrTextRequired
	}

	if len(req.Text) > MaxTextLength {
		return ErrTextTooLong
	}

	return nil
}

// Analysis result types

// ToneAnalysisResult represents tone analysis result
type ToneAnalysisResult struct {
	Tone        string                 `json:"tone"`
	Confidence  float64                `json:"confidence"`
	SubTones    []string               `json:"sub_tones,omitempty"`
	Suggestions []string               `json:"suggestions,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// ClarityAnalysisResult represents clarity analysis result
type ClarityAnalysisResult struct {
	ClarityScore float64                `json:"clarity_score"`
	Issues       []ClarityIssue         `json:"issues,omitempty"`
	Suggestions  []string               `json:"suggestions,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// ClarityIssue represents a clarity issue
type ClarityIssue struct {
	Type        string `json:"type"`
	Description string `json:"description"`
	Location    string `json:"location,omitempty"`
	Severity    string `json:"severity"`
}

// SentimentAnalysisResult represents sentiment analysis result
type SentimentAnalysisResult struct {
	Sentiment    string                 `json:"sentiment"`
	Polarity     float64                `json:"polarity"`
	Subjectivity float64                `json:"subjectivity"`
	Emotions     map[string]float64     `json:"emotions,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// StructureAnalysisResult represents structure analysis result
type StructureAnalysisResult struct {
	IsWellStructured bool                   `json:"is_well_structured"`
	Score            float64                `json:"score"`
	Elements         []StructureElement     `json:"elements"`
	Issues           []string               `json:"issues,omitempty"`
	Suggestions      []string               `json:"suggestions,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// StructureElement represents a structure element
type StructureElement struct {
	Type     string `json:"type"`
	Position int    `json:"position"`
	Content  string `json:"content"`
}

// CompletenessAnalysisResult represents completeness analysis result
type CompletenessAnalysisResult struct {
	IsComplete       bool                   `json:"is_complete"`
	Score            float64                `json:"score"`
	PresentElements  []string               `json:"present_elements"`
	MissingElements  []string               `json:"missing_elements,omitempty"`
	Suggestions      []string               `json:"suggestions,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// ComprehensiveAnalysisResult represents comprehensive analysis result
type ComprehensiveAnalysisResult struct {
	Text         string                 `json:"text"`
	Tone         string                 `json:"tone"`
	ClarityScore float64                `json:"clarity_score"`
	Priority     Priority               `json:"priority"`
	Sentiment    *SentimentData         `json:"sentiment,omitempty"`
	Suggestions  []string               `json:"suggestions,omitempty"`
	Improvements []string               `json:"improvements,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// SuggestionsResult represents suggestions result
type SuggestionsResult struct {
	Suggestions []Suggestion           `json:"suggestions"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Suggestion represents an improvement suggestion
type Suggestion struct {
	Type        string `json:"type"`
	Description string `json:"description"`
	Example     string `json:"example,omitempty"`
	Impact      string `json:"impact"`
	Priority    int    `json:"priority"`
}

// GrammarValidationResult represents grammar validation result
type GrammarValidationResult struct {
	IsValid     bool                   `json:"is_valid"`
	Errors      []GrammarError         `json:"errors,omitempty"`
	Warnings    []GrammarWarning       `json:"warnings,omitempty"`
	Score       float64                `json:"score"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// GrammarError represents a grammar error
type GrammarError struct {
	Type        string `json:"type"`
	Message     string `json:"message"`
	Position    int    `json:"position"`
	Length      int    `json:"length"`
	Suggestion  string `json:"suggestion,omitempty"`
}

// GrammarWarning represents a grammar warning
type GrammarWarning struct {
	Type    string `json:"type"`
	Message string `json:"message"`
	Hint    string `json:"hint,omitempty"`
}

// KeyPointsResult represents key points extraction result
type KeyPointsResult struct {
	KeyPoints []KeyPoint             `json:"key_points"`
	Summary   string                 `json:"summary,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// KeyPoint represents a key point
type KeyPoint struct {
	Point      string  `json:"point"`
	Importance float64 `json:"importance"`
	Category   string  `json:"category,omitempty"`
}

// AudienceAnalysisResult represents audience analysis result
type AudienceAnalysisResult struct {
	IsAppropriate       bool                   `json:"is_appropriate"`
	Score               float64                `json:"score"`
	TargetAudience      string                 `json:"target_audience"`
	CurrentTone         string                 `json:"current_tone"`
	RecommendedTone     string                 `json:"recommended_tone"`
	AdjustmentsNeeded   []string               `json:"adjustments_needed,omitempty"`
	Metadata            map[string]interface{} `json:"metadata,omitempty"`
}

// ToneComparisonResult represents tone comparison result
type ToneComparisonResult struct {
	Text1Tone    string                 `json:"text1_tone"`
	Text2Tone    string                 `json:"text2_tone"`
	Similarity   float64                `json:"similarity"`
	Differences  []string               `json:"differences"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// ReadabilityResult represents readability analysis result
type ReadabilityResult struct {
	FleschScore         float64                `json:"flesch_score"`
	FleschKincaidGrade  float64                `json:"flesch_kincaid_grade"`
	GunningFogIndex     float64                `json:"gunning_fog_index"`
	ReadingLevel        string                 `json:"reading_level"`
	EstimatedReadTime   int                    `json:"estimated_read_time_seconds"`
	WordCount           int                    `json:"word_count"`
	SentenceCount       int                    `json:"sentence_count"`
	AverageSentenceLen  float64                `json:"average_sentence_length"`
	Metadata            map[string]interface{} `json:"metadata,omitempty"`
}

// BatchAnalyzeResponse represents batch analysis response
type BatchAnalyzeResponse struct {
	Success               bool               `json:"success"`
	Results               []AnalyzeResponse  `json:"results"`
	FailedCount           int                `json:"failed_count"`
	TotalProcessingTimeMs int                `json:"total_processing_time_ms"`
}

// AnalysisHistory represents analysis history entry
type AnalysisHistory struct {
	ID            string                 `json:"id"`
	Text          string                 `json:"text"`
	AnalysisTypes []string               `json:"analysis_types"`
	Results       map[string]interface{} `json:"results"`
	CreatedAt     string                 `json:"created_at"`
	UserID        string                 `json:"user_id"`
}