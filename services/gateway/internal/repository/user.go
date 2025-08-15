package repository

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/google/uuid"
	"github.com/tonebridge/gateway/internal/models"
)

type UserRepository struct {
	db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) Create(ctx context.Context, user *models.User) error {
	query := `
		INSERT INTO users (id, email, name, role, organization, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
		RETURNING created_at, updated_at
	`
	
	err := r.db.QueryRowContext(
		ctx, query,
		user.ID, user.Email, user.Name, user.Role, user.Organization,
	).Scan(&user.CreatedAt, &user.UpdatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}
	
	return nil
}

func (r *UserRepository) GetByID(ctx context.Context, id uuid.UUID) (*models.User, error) {
	query := `
		SELECT id, email, name, role, organization, created_at, updated_at
		FROM users
		WHERE id = $1
	`
	
	user := &models.User{}
	err := r.db.QueryRowContext(ctx, query, id).Scan(
		&user.ID, &user.Email, &user.Name, &user.Role,
		&user.Organization, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	return user, nil
}

func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*models.User, error) {
	query := `
		SELECT id, email, name, role, organization, created_at, updated_at
		FROM users
		WHERE email = $1
	`
	
	user := &models.User{}
	err := r.db.QueryRowContext(ctx, query, email).Scan(
		&user.ID, &user.Email, &user.Name, &user.Role,
		&user.Organization, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	return user, nil
}

func (r *UserRepository) Update(ctx context.Context, id uuid.UUID, updates map[string]interface{}) (*models.User, error) {
	// Build dynamic update query
	query := "UPDATE users SET updated_at = NOW()"
	args := []interface{}{}
	argCount := 1
	
	for key, value := range updates {
		if key == "name" || key == "organization" {
			query += fmt.Sprintf(", %s = $%d", key, argCount)
			args = append(args, value)
			argCount++
		}
	}
	
	query += fmt.Sprintf(" WHERE id = $%d RETURNING id, email, name, role, organization, created_at, updated_at", argCount)
	args = append(args, id)
	
	user := &models.User{}
	err := r.db.QueryRowContext(ctx, query, args...).Scan(
		&user.ID, &user.Email, &user.Name, &user.Role,
		&user.Organization, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err != nil {
		return nil, fmt.Errorf("failed to update user: %w", err)
	}
	
	return user, nil
}

func (r *UserRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := "DELETE FROM users WHERE id = $1"
	
	result, err := r.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}
	
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}
	
	if rowsAffected == 0 {
		return fmt.Errorf("user not found")
	}
	
	return nil
}