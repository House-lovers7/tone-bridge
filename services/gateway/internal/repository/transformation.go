package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/google/uuid"
	"github.com/tonebridge/gateway/internal/models"
)

type TransformationRepository struct {
	db *sql.DB
}

func NewTransformationRepository(db *sql.DB) *TransformationRepository {
	return &TransformationRepository{db: db}
}

func (r *TransformationRepository) Create(ctx context.Context, transform *models.Transformation) error {
	query := `
		INSERT INTO transformations (
			id, user_id, original_text, transformed_text, 
			transformation_type, source_tone, target_tone, metadata, created_at
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
		RETURNING created_at
	`
	
	transform.ID = uuid.New()
	
	var metadata []byte
	if transform.Metadata != nil {
		metadata = transform.Metadata
	} else {
		metadata = []byte("{}")
	}
	
	err := r.db.QueryRowContext(
		ctx, query,
		transform.ID, transform.UserID, transform.OriginalText, transform.TransformedText,
		transform.TransformationType, transform.SourceTone, transform.TargetTone, metadata,
	).Scan(&transform.CreatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create transformation: %w", err)
	}
	
	return nil
}

func (r *TransformationRepository) GetByID(ctx context.Context, id uuid.UUID) (*models.Transformation, error) {
	query := `
		SELECT id, user_id, original_text, transformed_text, 
			   transformation_type, source_tone, target_tone, metadata, created_at
		FROM transformations
		WHERE id = $1
	`
	
	transform := &models.Transformation{}
	var metadata []byte
	
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&transform.ID, &transform.UserID, &transform.OriginalText, &transform.TransformedText,
		&transform.TransformationType, &transform.SourceTone, &transform.TargetTone,
		&metadata, &transform.CreatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("transformation not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get transformation: %w", err)
	}
	
	if len(metadata) > 0 {
		transform.Metadata = json.RawMessage(metadata)
	}
	
	return transform, nil
}

func (r *TransformationRepository) GetUserHistory(ctx context.Context, userID uuid.UUID, limit, offset int) ([]*models.Transformation, error) {
	query := `
		SELECT id, user_id, original_text, transformed_text, 
			   transformation_type, source_tone, target_tone, metadata, created_at
		FROM transformations
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`
	
	rows, err := r.db.QueryContext(ctx, query, userID, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to get transformation history: %w", err)
	}
	defer rows.Close()
	
	var transformations []*models.Transformation
	
	for rows.Next() {
		transform := &models.Transformation{}
		var metadata []byte
		
		err := rows.Scan(
			&transform.ID, &transform.UserID, &transform.OriginalText, &transform.TransformedText,
			&transform.TransformationType, &transform.SourceTone, &transform.TargetTone,
			&metadata, &transform.CreatedAt,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan transformation: %w", err)
		}
		
		if len(metadata) > 0 {
			transform.Metadata = json.RawMessage(metadata)
		}
		
		transformations = append(transformations, transform)
	}
	
	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating transformations: %w", err)
	}
	
	return transformations, nil
}

func (r *TransformationRepository) GetStatsByUserID(ctx context.Context, userID uuid.UUID) (map[string]interface{}, error) {
	query := `
		SELECT 
			COUNT(*) as total_transformations,
			COUNT(DISTINCT DATE(created_at)) as active_days,
			MAX(created_at) as last_transformation
		FROM transformations
		WHERE user_id = $1
	`
	
	var totalTransformations int
	var activeDays int
	var lastTransformation sql.NullTime
	
	err := r.db.QueryRowContext(ctx, query, userID).Scan(
		&totalTransformations,
		&activeDays,
		&lastTransformation,
	)
	
	if err != nil {
		return nil, fmt.Errorf("failed to get user stats: %w", err)
	}
	
	stats := map[string]interface{}{
		"total_transformations": totalTransformations,
		"active_days":          activeDays,
	}
	
	if lastTransformation.Valid {
		stats["last_transformation"] = lastTransformation.Time
	}
	
	// Get transformation type breakdown
	typeQuery := `
		SELECT transformation_type, COUNT(*) as count
		FROM transformations
		WHERE user_id = $1
		GROUP BY transformation_type
	`
	
	rows, err := r.db.QueryContext(ctx, typeQuery, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get transformation type stats: %w", err)
	}
	defer rows.Close()
	
	typeBreakdown := make(map[string]int)
	for rows.Next() {
		var transformationType string
		var count int
		if err := rows.Scan(&transformationType, &count); err != nil {
			return nil, fmt.Errorf("failed to scan type stats: %w", err)
		}
		typeBreakdown[transformationType] = count
	}
	
	stats["type_breakdown"] = typeBreakdown
	
	return stats, nil
}