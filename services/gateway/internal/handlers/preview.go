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

type PreviewHandler struct {
	transformService *services.TransformationService
	logger          *zap.SugaredLogger
	validator       *validator.Validate
}

func NewPreviewHandler(transformService *services.TransformationService, logger *zap.SugaredLogger) *PreviewHandler {
	return &PreviewHandler{
		transformService: transformService,
		logger:          logger,
		validator:       validator.New(),
	}
}

// PreviewTransformRequest is a limited version of TransformRequest for preview mode
type PreviewTransformRequest struct {
	Text       string `json:"text" validate:"required,max=500"`
	TargetTone string `json:"target_tone" validate:"required,oneof=professional casual formal technical warm"`
	IntensityLevel int `json:"intensity_level" validate:"min=1,max=3"`
}

// PreviewTransform handles text transformation in preview mode (no auth required)
func (h *PreviewHandler) PreviewTransform(c *fiber.Ctx) error {
	// Get client IP for rate limiting
	clientIP := c.IP()
	
	// Check text length limit for preview (500 characters)
	var req PreviewTransformRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	// Validate request
	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	// Check text length
	if len(req.Text) > 500 {
		return utils.SendError(c, fiber.StatusBadRequest, "Text exceeds 500 character limit for preview mode")
	}

	// Create a temporary user ID for preview
	previewUserID := uuid.New()
	
	// Create transform request
	transformReq := &models.TransformRequest{
		Text:               req.Text,
		TransformationType: "tone",
		TargetTone:        req.TargetTone,
		IntensityLevel:    req.IntensityLevel,
		Options: map[string]string{
			"intensity": string(rune(req.IntensityLevel + '0')), // Also keep in options for backward compatibility
			"preview":   "true",
		},
	}

	// Log preview usage
	h.logger.Infow("Preview transformation request",
		"ip", clientIP,
		"text_length", len(req.Text),
		"target_tone", req.TargetTone,
	)

	// Call transformation service
	response, err := h.transformService.TransformText(c.Context(), previewUserID, transformReq)
	if err != nil {
		h.logger.Errorw("Preview transformation failed", "error", err, "ip", clientIP)
		return utils.SendError(c, fiber.StatusInternalServerError, "Transformation failed: "+err.Error())
	}

	// Add preview mode indicator to response
	return c.JSON(fiber.Map{
		"success": true,
		"preview_mode": true,
		"limitations": fiber.Map{
			"max_characters": 500,
			"rate_limit": "3 requests per minute",
			"daily_limit": "10 requests per day",
		},
		"data": response,
		"message": "This is a preview. Sign up for unlimited access!",
	})
}

// PreviewAnalyze handles text analysis in preview mode (no auth required)  
func (h *PreviewHandler) PreviewAnalyze(c *fiber.Ctx) error {
	clientIP := c.IP()
	
	var req models.AnalyzeRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	// Check text length
	if len(req.Text) > 500 {
		return utils.SendError(c, fiber.StatusBadRequest, "Text exceeds 500 character limit for preview mode")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	// Create a temporary user ID for preview
	previewUserID := uuid.New()
	
	// Log preview usage
	h.logger.Infow("Preview analysis request",
		"ip", clientIP,
		"text_length", len(req.Text),
	)

	response, err := h.transformService.AnalyzeText(c.Context(), previewUserID, &req)
	if err != nil {
		h.logger.Errorw("Preview analysis failed", "error", err, "ip", clientIP)
		return utils.SendError(c, fiber.StatusInternalServerError, "Analysis failed: "+err.Error())
	}

	return c.JSON(fiber.Map{
		"success": true,
		"preview_mode": true,
		"limitations": fiber.Map{
			"max_characters": 500,
			"rate_limit": "3 requests per minute",
			"daily_limit": "10 requests per day",
		},
		"data": response,
		"message": "This is a preview analysis. Sign up for full features!",
	})
}

// GetPreviewInfo returns information about preview mode limitations
func (h *PreviewHandler) GetPreviewInfo(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"preview_mode": fiber.Map{
			"enabled": true,
			"features": []string{
				"Text transformation (tone adjustment)",
				"Text analysis",
				"Basic suggestions",
			},
			"limitations": fiber.Map{
				"max_text_length": 500,
				"rate_limit": fiber.Map{
					"per_minute": 3,
					"per_day": 10,
				},
				"available_tones": []string{
					"professional",
					"casual", 
					"formal",
					"technical",
					"warm",
				},
				"intensity_levels": fiber.Map{
					"min": 1,
					"max": 3,
					"description": "1=subtle, 2=moderate, 3=strong",
				},
			},
			"upgrade_benefits": []string{
				"Unlimited text length",
				"No rate limits",
				"Advanced transformation options",
				"Custom dictionaries",
				"History tracking",
				"Priority support",
			},
		},
		"try_now": fiber.Map{
			"endpoint": "/api/v1/preview/transform",
			"method": "POST",
			"example_request": fiber.Map{
				"text": "I need this done ASAP!",
				"target_tone": "professional",
				"intensity_level": 2,
			},
		},
		"signup_url": "/api/v1/auth/register",
	})
}