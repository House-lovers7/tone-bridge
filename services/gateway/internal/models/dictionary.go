package models

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type Dictionary struct {
	ID           uuid.UUID       `json:"id" db:"id"`
	Organization string          `json:"organization,omitempty" db:"organization"`
	Term         string          `json:"term" db:"term"`
	Definition   string          `json:"definition,omitempty" db:"definition"`
	Category     string          `json:"category,omitempty" db:"category"`
	Alternatives json.RawMessage `json:"alternatives,omitempty" db:"alternatives"`
	CreatedAt    time.Time       `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time       `json:"updated_at" db:"updated_at"`
}

type Term struct {
	Term         string   `json:"term"`
	Definition   string   `json:"definition"`
	Category     string   `json:"category,omitempty"`
	Alternatives []string `json:"alternatives,omitempty"`
}

type CreateDictionaryRequest struct {
	Term         string   `json:"term" validate:"required"`
	Definition   string   `json:"definition" validate:"required"`
	Category     string   `json:"category,omitempty"`
	Alternatives []string `json:"alternatives,omitempty"`
}