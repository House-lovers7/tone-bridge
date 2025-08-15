package tonebridge

import "time"

// TransformationType represents the type of transformation
type TransformationType string

const (
	// TransformationSoften softens harsh language
	TransformationSoften TransformationType = "soften"
	// TransformationClarify clarifies confusing text
	TransformationClarify TransformationType = "clarify"
	// TransformationStructure structures unorganized text
	TransformationStructure TransformationType = "structure"
	// TransformationSummarize summarizes long text
	TransformationSummarize TransformationType = "summarize"
	// TransformationTerminology converts technical terminology
	TransformationTerminology TransformationType = "terminology"
	// TransformationRequirementStructuring structures requirements
	TransformationRequirementStructuring TransformationType = "requirement_structuring"
	// TransformationBackgroundCompletion completes background information
	TransformationBackgroundCompletion TransformationType = "background_completion"
	// TransformationCustom applies custom transformation
	TransformationCustom TransformationType = "custom"
)

// Priority represents priority levels
type Priority string

const (
	// PriorityCritical represents critical priority
	PriorityCritical Priority = "critical"
	// PriorityHigh represents high priority
	PriorityHigh Priority = "high"
	// PriorityMedium represents medium priority
	PriorityMedium Priority = "medium"
	// PriorityLow represents low priority
	PriorityLow Priority = "low"
)

// AnalysisType represents the type of analysis
type AnalysisType string

const (
	// AnalysisTone analyzes tone
	AnalysisTone AnalysisType = "tone"
	// AnalysisClarity analyzes clarity
	AnalysisClarity AnalysisType = "clarity"
	// AnalysisPriority analyzes priority
	AnalysisPriority AnalysisType = "priority"
	// AnalysisSentiment analyzes sentiment
	AnalysisSentiment AnalysisType = "sentiment"
	// AnalysisStructure analyzes structure
	AnalysisStructure AnalysisType = "structure"
	// AnalysisCompleteness analyzes completeness
	AnalysisCompleteness AnalysisType = "completeness"
)

// TriggerType represents auto-transform trigger types
type TriggerType string

const (
	// TriggerKeyword triggers on keywords
	TriggerKeyword TriggerType = "keyword"
	// TriggerSentiment triggers on sentiment
	TriggerSentiment TriggerType = "sentiment"
	// TriggerRecipient triggers on recipient
	TriggerRecipient TriggerType = "recipient"
	// TriggerChannel triggers on channel
	TriggerChannel TriggerType = "channel"
	// TriggerTime triggers on time
	TriggerTime TriggerType = "time"
	// TriggerPattern triggers on pattern
	TriggerPattern TriggerType = "pattern"
)

// Platform represents supported platforms
type Platform string

const (
	// PlatformSlack represents Slack platform
	PlatformSlack Platform = "slack"
	// PlatformTeams represents Microsoft Teams platform
	PlatformTeams Platform = "teams"
	// PlatformDiscord represents Discord platform
	PlatformDiscord Platform = "discord"
	// PlatformOutlook represents Outlook platform
	PlatformOutlook Platform = "outlook"
	// PlatformWeb represents Web platform
	PlatformWeb Platform = "web"
)

// TransformOptions represents options for text transformation
type TransformOptions struct {
	PreserveFormatting  bool   `json:"preserve_formatting,omitempty"`
	IncludeSignature    bool   `json:"include_signature,omitempty"`
	TargetAudience      string `json:"target_audience,omitempty"`
	CustomInstructions  string `json:"custom_instructions,omitempty"`
	Language            string `json:"language,omitempty"`
}

// TransformRequest represents a transform request
type TransformRequest struct {
	Text               string                 `json:"text"`
	TransformationType TransformationType     `json:"transformation_type"`
	Intensity          int                    `json:"intensity,omitempty"`
	Options            *TransformOptions      `json:"options,omitempty"`
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
}

// TransformResponse represents a transform response
type TransformResponse struct {
	Success   bool                   `json:"success"`
	Data      TransformData         `json:"data"`
}

// TransformData contains transformation result data
type TransformData struct {
	OriginalText       string                 `json:"original_text"`
	TransformedText    string                 `json:"transformed_text"`
	TransformationType string                 `json:"transformation_type"`
	Intensity          int                    `json:"intensity"`
	Suggestions        []string               `json:"suggestions,omitempty"`
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
	ProcessingTimeMs   int                    `json:"processing_time_ms,omitempty"`
}

// AnalyzeRequest represents an analyze request
type AnalyzeRequest struct {
	Text               string                 `json:"text"`
	AnalysisTypes      []AnalysisType         `json:"analysis_types,omitempty"`
	IncludeSuggestions bool                   `json:"include_suggestions,omitempty"`
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
}

// AnalyzeResponse represents an analyze response
type AnalyzeResponse struct {
	Success bool         `json:"success"`
	Data    AnalyzeData  `json:"data"`
}

// AnalyzeData contains analysis result data
type AnalyzeData struct {
	Text             string                 `json:"text"`
	Tone             string                 `json:"tone"`
	ClarityScore     float64                `json:"clarity_score"`
	Priority         Priority               `json:"priority"`
	PriorityQuadrant string                 `json:"priority_quadrant,omitempty"`
	Sentiment        *SentimentData         `json:"sentiment,omitempty"`
	Suggestions      []string               `json:"suggestions,omitempty"`
	Improvements     []string               `json:"improvements,omitempty"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// SentimentData contains sentiment analysis data
type SentimentData struct {
	Polarity     float64 `json:"polarity"`
	Subjectivity float64 `json:"subjectivity"`
}

// AutoTransformConfig represents auto-transform configuration
type AutoTransformConfig struct {
	Enabled                    bool               `json:"enabled"`
	DefaultTransformationType  TransformationType `json:"default_transformation_type"`
	DefaultIntensity           int                `json:"default_intensity"`
	MinMessageLength           int                `json:"min_message_length"`
	MaxProcessingDelayMs       int                `json:"max_processing_delay_ms"`
	RequireConfirmation        bool               `json:"require_confirmation"`
	ShowPreview                bool               `json:"show_preview"`
	PreserveOriginal           bool               `json:"preserve_original"`
}

// AutoTransformRule represents an auto-transform rule
type AutoTransformRule struct {
	ID                       string                 `json:"id,omitempty"`
	RuleName                 string                 `json:"rule_name"`
	Description              string                 `json:"description,omitempty"`
	Enabled                  bool                   `json:"enabled"`
	Priority                 int                    `json:"priority"`
	TriggerType              TriggerType            `json:"trigger_type"`
	TriggerValue             map[string]interface{} `json:"trigger_value"`
	TransformationType       TransformationType     `json:"transformation_type"`
	TransformationIntensity  int                    `json:"transformation_intensity"`
	TransformationOptions    map[string]interface{} `json:"transformation_options,omitempty"`
	Platforms                []string               `json:"platforms,omitempty"`
	Channels                 []string               `json:"channels,omitempty"`
	UserRoles                []string               `json:"user_roles,omitempty"`
}

// MessageContext represents message context for auto-transform
type MessageContext struct {
	Message      string                 `json:"message"`
	UserID       string                 `json:"user_id"`
	TenantID     string                 `json:"tenant_id"`
	Platform     Platform               `json:"platform"`
	ChannelID    string                 `json:"channel_id,omitempty"`
	RecipientIDs []string               `json:"recipient_ids,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// TransformationResult represents transformation evaluation result
type TransformationResult struct {
	ShouldTransform         bool                   `json:"should_transform"`
	RuleID                  string                 `json:"rule_id,omitempty"`
	RuleName                string                 `json:"rule_name,omitempty"`
	TransformationType      TransformationType     `json:"transformation_type"`
	TransformationIntensity int                    `json:"transformation_intensity"`
	TransformationOptions   map[string]interface{} `json:"transformation_options,omitempty"`
	Confidence              float64                `json:"confidence"`
	Reason                  string                 `json:"reason,omitempty"`
}

// BatchTransformRequest represents a batch transform request
type BatchTransformRequest struct {
	Items        []TransformRequest `json:"items"`
	Parallel     bool               `json:"parallel,omitempty"`
	StopOnError  bool               `json:"stop_on_error,omitempty"`
}

// BatchTransformResponse represents a batch transform response
type BatchTransformResponse struct {
	Success               bool                `json:"success"`
	Results               []TransformResponse `json:"results"`
	FailedCount           int                 `json:"failed_count"`
	TotalProcessingTimeMs int                 `json:"total_processing_time_ms"`
}

// TransformationHistory represents transformation history
type TransformationHistory struct {
	ID                 string                 `json:"id"`
	UserID             string                 `json:"user_id"`
	OriginalText       string                 `json:"original_text"`
	TransformedText    string                 `json:"transformed_text"`
	TransformationType string                 `json:"transformation_type"`
	Intensity          int                    `json:"intensity"`
	CreatedAt          time.Time              `json:"created_at"`
	Metadata           map[string]interface{} `json:"metadata,omitempty"`
}

// Dictionary represents a custom dictionary
type Dictionary struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Description string            `json:"description,omitempty"`
	Entries     []DictionaryEntry `json:"entries"`
	IsActive    bool              `json:"is_active"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
}

// DictionaryEntry represents a dictionary entry
type DictionaryEntry struct {
	Original      string `json:"original"`
	Replacement   string `json:"replacement"`
	Context       string `json:"context,omitempty"`
	CaseSensitive bool   `json:"case_sensitive,omitempty"`
}

// WebSocketMessage represents a WebSocket message
type WebSocketMessage struct {
	Type      string                 `json:"type"`
	Data      interface{}            `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	ID        string                 `json:"id"`
}

// AutoTransformTemplate represents an auto-transform template
type AutoTransformTemplate struct {
	ID           string                 `json:"id"`
	TemplateName string                 `json:"template_name"`
	Category     string                 `json:"category"`
	Description  string                 `json:"description"`
	RuleConfig   map[string]interface{} `json:"rule_config"`
	IsSystem     bool                   `json:"is_system"`
}

// PriorityScore represents priority scoring result
type PriorityScore struct {
	Score      float64 `json:"score"`
	Quadrant   string  `json:"quadrant"`
	Urgency    float64 `json:"urgency"`
	Importance float64 `json:"importance"`
	Reasoning  string  `json:"reasoning"`
}

// TonePreset represents a tone preset
type TonePreset struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Settings    map[string]interface{} `json:"settings"`
}