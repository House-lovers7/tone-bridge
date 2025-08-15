package models

import (
	"time"

	"github.com/google/uuid"
)

type User struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	Email        string     `json:"email" db:"email"`
	Name         string     `json:"name" db:"name"`
	Password     string     `json:"-" db:"password"` // Password hash, never exposed in JSON
	Role         string     `json:"role" db:"role"`
	Organization string     `json:"organization,omitempty" db:"organization"`
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`
}

type RegisterRequest struct {
	Email        string `json:"email" validate:"required,email"`
	Password     string `json:"password" validate:"required,min=8"`
	Name         string `json:"name" validate:"required"`
	Organization string `json:"organization,omitempty"`
}

type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required"`
}

type LoginResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	User         *User  `json:"user"`
}

type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}