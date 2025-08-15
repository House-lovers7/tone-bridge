package models

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type Transformation struct {
	ID                 uuid.UUID       `json:"id" db:"id"`
	UserID             uuid.UUID       `json:"user_id" db:"user_id"`
	OriginalText       string          `json:"original_text" db:"original_text"`
	TransformedText    string          `json:"transformed_text" db:"transformed_text"`
	TransformationType string          `json:"transformation_type" db:"transformation_type"`
	SourceTone         string          `json:"source_tone,omitempty" db:"source_tone"`
	TargetTone         string          `json:"target_tone,omitempty" db:"target_tone"`
	Metadata           json.RawMessage `json:"metadata,omitempty" db:"metadata"`
	CreatedAt          time.Time       `json:"created_at" db:"created_at"`
}

type TransformRequest struct {
	Text               string            `json:"text" validate:"required"`
	TransformationType string            `json:"transformation_type" validate:"required,oneof=tone structure summarize terminology"`
	TargetTone         string            `json:"target_tone,omitempty"`
	IntensityLevel     int               `json:"intensity_level,omitempty" validate:"min=1,max=3"`
	Options            map[string]string `json:"options,omitempty"`
}

type TransformResponse struct {
	OriginalText    string                 `json:"original_text"`
	TransformedText string                 `json:"transformed_text"`
	Suggestions     []string               `json:"suggestions,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

type AnalyzeRequest struct {
	Text string `json:"text" validate:"required"`
}

type AnalyzeResponse struct {
	Tone         string                 `json:"tone"`
	Clarity      float64                `json:"clarity"`
	Structure    map[string]interface{} `json:"structure"`
	Suggestions  []string               `json:"suggestions"`
	Priority     string                 `json:"priority"`
	TermsFound   []Term                 `json:"terms_found,omitempty"`
}