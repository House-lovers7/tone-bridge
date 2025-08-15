package handlers

import (
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"go.uber.org/zap"

	"github.com/tonebridge/gateway/internal/models"
	"github.com/tonebridge/gateway/internal/services"
	"github.com/tonebridge/gateway/pkg/utils"
)

type TransformHandler struct {
	transformService *services.TransformationService
	logger          *zap.SugaredLogger
	validator       *validator.Validate
}

func NewTransformHandler(transformService *services.TransformationService, logger *zap.SugaredLogger) *TransformHandler {
	return &TransformHandler{
		transformService: transformService,
		logger:          logger,
		validator:       validator.New(),
	}
}

func (h *TransformHandler) TransformMessage(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	
	var req models.TransformRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	uid, err := uuid.Parse(userID)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid user ID")
	}

	response, err := h.transformService.TransformText(c.Context(), uid, &req)
	if err != nil {
		h.logger.Errorw("Transformation failed", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Transformation failed: "+err.Error())
	}

	return utils.SendSuccess(c, response)
}

func (h *TransformHandler) AnalyzeMessage(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	
	var req models.AnalyzeRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	uid, err := uuid.Parse(userID)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid user ID")
	}

	response, err := h.transformService.AnalyzeText(c.Context(), uid, &req)
	if err != nil {
		h.logger.Errorw("Analysis failed", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Analysis failed: "+err.Error())
	}

	return utils.SendSuccess(c, response)
}

func (h *TransformHandler) GetHistory(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	
	limitStr := c.Query("limit", "20")
	limit, _ := strconv.Atoi(limitStr)
	offsetStr := c.Query("offset", "0")
	offset, _ := strconv.Atoi(offsetStr)
	
	uid, err := uuid.Parse(userID)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid user ID")
	}

	history, err := h.transformService.GetUserHistory(c.Context(), uid, limit, offset)
	if err != nil {
		h.logger.Errorw("Failed to get history", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to retrieve history")
	}

	return utils.SendSuccess(c, history)
}

func (h *TransformHandler) GetDictionaries(c *fiber.Ctx) error {
	organization := c.Query("organization", "")
	category := c.Query("category", "")
	
	dictionaries, err := h.transformService.GetDictionaries(c.Context(), organization, category)
	if err != nil {
		h.logger.Errorw("Failed to get dictionaries", "error", err)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to retrieve dictionaries")
	}

	return utils.SendSuccess(c, dictionaries)
}

func (h *TransformHandler) CreateDictionary(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(string)
	role := c.Locals("role").(string)
	
	// Only admins can create dictionaries
	if role != "admin" {
		return utils.SendError(c, fiber.StatusForbidden, "Insufficient permissions")
	}
	
	var req models.CreateDictionaryRequest
	if err := c.BodyParser(&req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	if err := h.validator.Struct(req); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Validation failed: "+err.Error())
	}

	dictionary, err := h.transformService.CreateDictionary(c.Context(), &req)
	if err != nil {
		h.logger.Errorw("Failed to create dictionary", "error", err, "user_id", userID)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to create dictionary entry")
	}

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"data":    dictionary,
	})
}

func (h *TransformHandler) UpdateDictionary(c *fiber.Ctx) error {
	role := c.Locals("role").(string)
	
	// Only admins can update dictionaries
	if role != "admin" {
		return utils.SendError(c, fiber.StatusForbidden, "Insufficient permissions")
	}
	
	id := c.Params("id")
	uid, err := uuid.Parse(id)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid dictionary ID")
	}
	
	var updates map[string]interface{}
	if err := c.BodyParser(&updates); err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid request body")
	}

	dictionary, err := h.transformService.UpdateDictionary(c.Context(), uid, updates)
	if err != nil {
		h.logger.Errorw("Failed to update dictionary", "error", err, "id", id)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to update dictionary entry")
	}

	return utils.SendSuccess(c, dictionary)
}

func (h *TransformHandler) DeleteDictionary(c *fiber.Ctx) error {
	role := c.Locals("role").(string)
	
	// Only admins can delete dictionaries
	if role != "admin" {
		return utils.SendError(c, fiber.StatusForbidden, "Insufficient permissions")
	}
	
	id := c.Params("id")
	uid, err := uuid.Parse(id)
	if err != nil {
		return utils.SendError(c, fiber.StatusBadRequest, "Invalid dictionary ID")
	}

	if err := h.transformService.DeleteDictionary(c.Context(), uid); err != nil {
		h.logger.Errorw("Failed to delete dictionary", "error", err, "id", id)
		return utils.SendError(c, fiber.StatusInternalServerError, "Failed to delete dictionary entry")
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Dictionary entry deleted successfully",
	})
}