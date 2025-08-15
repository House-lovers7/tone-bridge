package services

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/tonebridge/gateway/internal/middleware"
	"github.com/tonebridge/gateway/internal/models"
	"github.com/tonebridge/gateway/internal/repository"
	"golang.org/x/crypto/bcrypt"
)

type AuthService struct {
	userRepo  *repository.UserRepository
	jwtSecret string
}

type TokenPair struct {
	AccessToken  string
	RefreshToken string
}

func NewAuthService(userRepo *repository.UserRepository, jwtSecret string) *AuthService {
	return &AuthService{
		userRepo:  userRepo,
		jwtSecret: jwtSecret,
	}
}

func (s *AuthService) Register(ctx context.Context, req *models.RegisterRequest) (*models.User, error) {
	// Check if user already exists
	existingUser, _ := s.userRepo.GetByEmail(ctx, req.Email)
	if existingUser != nil {
		return nil, fmt.Errorf("user with email %s already exists", req.Email)
	}
	
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Create user
	user := &models.User{
		ID:           uuid.New(),
		Email:        req.Email,
		Name:         req.Name,
		Password:     string(hashedPassword),
		Role:         "user",
		Organization: req.Organization,
	}
	
	// Store user in database
	if err := s.userRepo.Create(ctx, user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}
	
	// Store password hash (in real implementation, this would be in a separate table)
	// For MVP, we're simplifying this
	
	return user, nil
}

func (s *AuthService) Login(ctx context.Context, req *models.LoginRequest) (*models.User, error) {
	// Get user by email
	user, err := s.userRepo.GetByEmail(ctx, req.Email)
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}
	
	// Verify password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}
	
	return user, nil
}

func (s *AuthService) GenerateTokens(user *models.User) (*TokenPair, error) {
	// Generate access token (15 minutes)
	accessToken, err := middleware.GenerateToken(
		user.ID.String(),
		user.Email,
		user.Role,
		s.jwtSecret,
		15*time.Minute,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}
	
	// Generate refresh token (7 days)
	refreshToken, err := middleware.GenerateToken(
		user.ID.String(),
		user.Email,
		user.Role,
		s.jwtSecret,
		7*24*time.Hour,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}
	
	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
	}, nil
}

func (s *AuthService) RefreshTokens(ctx context.Context, refreshToken string) (*TokenPair, error) {
	// Parse and validate refresh token
	claims := &middleware.Claims{}
	token, err := jwt.ParseWithClaims(refreshToken, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(s.jwtSecret), nil
	})
	
	if err != nil || !token.Valid {
		return nil, fmt.Errorf("invalid refresh token")
	}
	
	// Get user from database to ensure they still exist
	userID, err := uuid.Parse(claims.UserID)
	if err != nil {
		return nil, fmt.Errorf("invalid user ID in token")
	}
	
	user, err := s.userRepo.GetByID(ctx, userID)
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}
	
	// Generate new token pair
	return s.GenerateTokens(user)
}

func (s *AuthService) GetUser(ctx context.Context, userID uuid.UUID) (*models.User, error) {
	return s.userRepo.GetByID(ctx, userID)
}

func (s *AuthService) UpdateUser(ctx context.Context, userID uuid.UUID, updates map[string]interface{}) (*models.User, error) {
	return s.userRepo.Update(ctx, userID, updates)
}

func generateRandomToken() (string, error) {
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}