package handlers

import (
	"github.com/gofiber/fiber/v2"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"go.uber.org/zap"

	"github.com/tonebridge/gateway/internal/models"
	"github.com/tonebridge/gateway/internal/services"
	"github.com/tonebridge/gateway/pkg/utils"
)

type AuthHandler struct {
	authService *services.AuthService
	logger      *zap.SugaredLogger
	validator   *validator.Validate
}

func NewAuthHandler(authService *services.AuthService, logger *zap.SugaredLogger) *AuthHandler {
	return &AuthHandler{
		authService: authService,
		logger:      logger,
		validator:   validator.New(),
	}
}

func (h *AuthHandler) Register(c *fiber.Ctx) error {
	var req models.RegisterRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	user, err := h.authService.Register(c.Context(), &req)
	if err != nil {
		h.logger.Errorw("Registration failed", "error", err, "email", req.Email)
		return utils.SendError(c, fiber.StatusBadRequest, err.Error())
	}

	tokens, err := h.authService.GenerateTokens(user)
	if err != nil {
		h.logger.Errorw("Token generation failed", "error", err, "user_id", user.ID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to generate tokens")
	}

	return c.Status(fiber.StatusCreated).JSON(models.LoginResponse{
		AccessToken:  tokens.AccessToken,
		RefreshToken: tokens.RefreshToken,
		User:         user,
	})
}

func (h *AuthHandler) Login(c *fiber.Ctx) error {
	var req models.LoginRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	user, err := h.authService.Login(c.Context(), &req)
	if err != nil {
		h.logger.Errorw("Login failed", "error", err, "email", req.Email)
		return utils.SendError(c, fiber.StatusUnauthorized, "Invalid credentials")
	}

	tokens, err := h.authService.GenerateTokens(user)
	if err != nil {
		h.logger.Errorw("Token generation failed", "error", err, "user_id", user.ID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to generate tokens")
	}

	return c.JSON(models.LoginResponse{
		AccessToken:  tokens.AccessToken,
		RefreshToken: tokens.RefreshToken,
		User:         user,
	})
}

func (h *AuthHandler) RefreshToken(c *fiber.Ctx) error {
	var req models.RefreshTokenRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	tokens, err := h.authService.RefreshTokens(c.Context(), req.RefreshToken)
	if err != nil {
		h.logger.Errorw("Token refresh failed", "error", err)
		return utils.SendError(c, fiber.StatusUnauthorized, "Invalid refresh token")
	}

	return c.JSON(fiber.Map{
		"access_token":  tokens.AccessToken,
		"refresh_token": tokens.RefreshToken,
	})
}

func (h *AuthHandler) GetProfile(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	
	uid, err := uuid.Parse(userID)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid user ID")
	}

	user, err := h.authService.GetUser(c.Context(), uid)
	if err != nil {
		h.logger.Errorw("Failed to get user profile", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusNotFound, "User not found")
	}

	return utils.SendSuccess(c, user)
}

func (h *AuthHandler) UpdateProfile(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	
	var updates map[string]interface{}
	if err := c.BodyParser(&updates); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	uid, err := uuid.Parse(userID)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid user ID")
	}

	user, err := h.authService.UpdateUser(c.Context(), uid, updates)
	if err != nil {
		h.logger.Errorw("Failed to update user profile", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to update profile")
	}

	return utils.SendSuccess(c, user)
}