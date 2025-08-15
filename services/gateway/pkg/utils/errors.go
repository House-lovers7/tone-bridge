package utils

import (
	"github.com/gofiber/fiber/v2"
)

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Code    string `json:"code,omitempty"`
}

func CustomErrorHandler(c *fiber.Ctx, err error) error {
	code := fiber.StatusInternalServerError
	message := "Internal server error"

	if e, ok := err.(*fiber.Error); ok {
		code = e.Code
		message = e.Message
	}

	return c.Status(code).JSON(ErrorResponse{
		Error:   err.Error(),
		Message: message,
	})
}

func SendError(c *fiber.Ctx, status int, message string) error {
	return c.Status(status).JSON(ErrorResponse{
		Error:   message,
		Message: message,
	})
}

func SendSuccess(c *fiber.Ctx, data interface{}) error {
	return c.JSON(fiber.Map{
		"success": true,
		"data":    data,
	})
}