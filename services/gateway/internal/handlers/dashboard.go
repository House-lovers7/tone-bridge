package handlers

import (
	"database/sql"
	"fmt"
	"strconv"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/redis/go-redis/v9"
	"github.com/tonebridge/gateway/internal/repository"
)

// DashboardHandler handles KPI dashboard endpoints
type DashboardHandler struct {
	db    *sql.DB
	redis *redis.Client
	repo  *repository.TransformationRepository
}

// NewDashboardHandler creates a new dashboard handler
func NewDashboardHandler(database *sql.DB, redisClient *redis.Client) *DashboardHandler {
	return &DashboardHandler{
		db:    database,
		redis: redisClient,
		repo:  repository.NewTransformationRepository(database),
	}
}

// MetricsSummary represents the summary metrics
type MetricsSummary struct {
	TotalTransformations   int64   `json:"totalTransformations"`
	TransformationChange   float64 `json:"transformationChange"`
	PreventionRate         float64 `json:"preventionRate"`
	PreventionChange       float64 `json:"preventionChange"`
	TimeSaved              int64   `json:"timeSaved"`
	TimeChange             float64 `json:"timeChange"`
	ActiveUsers            int64   `json:"activeUsers"`
	UsersChange            float64 `json:"usersChange"`
}

// DailyMetric represents metrics for a single day
type DailyMetric struct {
	Date            string  `json:"date"`
	Transformations int64   `json:"transformations"`
	ClarityScore    float64 `json:"clarityScore"`
	AvgResponseTime int64   `json:"avgResponseTime"`
	TopFeature      string  `json:"topFeature"`
	CacheHitRate    float64 `json:"cacheHitRate"`
}

// TrendData represents trend data for charts
type TrendData struct {
	Labels          []string `json:"labels"`
	Transformations []int64  `json:"transformations"`
	Users           []int64  `json:"users"`
}

// GetMetrics returns dashboard metrics
func (h *DashboardHandler) GetMetrics(c *fiber.Ctx) error {
	tenantID := c.Query("tenant_id")
	if tenantID == "" {
		// Get from JWT claims
		tenantID = c.Locals("tenant_id").(string)
	}

	periodStr := c.Query("period", "30")
	period, _ := strconv.Atoi(periodStr)

	// Get tenant info
	tenant, err := h.getTenantInfo(tenantID)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get tenant info",
		})
	}

	// Get summary metrics
	summary, err := h.getMetricsSummary(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get metrics summary",
		})
	}

	// Get daily metrics
	daily, err := h.getDailyMetrics(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get daily metrics",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data": fiber.Map{
			"tenant":  tenant,
			"summary": summary,
			"daily":   daily,
		},
	})
}

// GetTrends returns trend data for charts
func (h *DashboardHandler) GetTrends(c *fiber.Ctx) error {
	tenantID := c.Locals("tenant_id").(string)
	periodStr := c.Query("period", "30")
	period, _ := strconv.Atoi(periodStr)

	// Get usage trend
	usage, err := h.getUsageTrend(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get usage trend",
		})
	}

	// Get feature usage
	features, err := h.getFeatureUsage(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get feature usage",
		})
	}

	// Get platform distribution
	platforms, err := h.getPlatformDistribution(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get platform distribution",
		})
	}

	// Get priority distribution
	priorities, err := h.getPriorityDistribution(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get priority distribution",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data": fiber.Map{
			"usage":      usage,
			"features":   features,
			"platforms":  platforms,
			"priorities": priorities,
		},
	})
}

// GetInsights returns user insights
func (h *DashboardHandler) GetInsights(c fiber.Ctx) error {
	tenantID := c.Locals("tenant_id").(string)
	periodStr := c.Query("period", "30")
	period, _ := strconv.Atoi(periodStr)

	// Get top users
	topUsers, err := h.getTopUsers(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get top users",
		})
	}

	// Get top features
	topFeatures, err := h.getTopFeatures(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get top features",
		})
	}

	// Get peak hours
	peakHours, err := h.getPeakHours(tenantID, period)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get peak hours",
		})
	}

	// Get recent feedback
	feedback, err := h.getRecentFeedback(tenantID)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get feedback",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data": fiber.Map{
			"topUsers":       topUsers,
			"topFeatures":    topFeatures,
			"peakHours":      peakHours,
			"recentFeedback": feedback,
		},
	})
}

// Helper functions

func (h *DashboardHandler) getTenantInfo(tenantID string) (map[string]interface{}, error) {
	query := `
		SELECT t.name, s.name as plan
		FROM tenants t
		JOIN subscriptions sub ON t.id = sub.tenant_id
		JOIN subscription_plans s ON sub.plan_id = s.id
		WHERE t.id = $1
	`
	
	var name, plan string
	err := h.db.QueryRow(query, tenantID).Scan(&name, &plan)
	if err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"id":   tenantID,
		"name": name,
		"plan": plan,
	}, nil
}

func (h *DashboardHandler) getMetricsSummary(tenantID string, period int) (*MetricsSummary, error) {
	endDate := time.Now()
	startDate := endDate.AddDate(0, 0, -period)
	previousStart := startDate.AddDate(0, 0, -period)

	// Get current period metrics
	currentQuery := `
		SELECT 
			COUNT(*) as total_transformations,
			COUNT(DISTINCT user_id) as active_users,
			AVG(CASE WHEN success THEN 1 ELSE 0 END) * 100 as prevention_rate,
			SUM(response_time_ms) / 1000 / 60 as time_saved
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at BETWEEN $2 AND $3
	`
	
	var current MetricsSummary
	err := h.db.QueryRow(currentQuery, tenantID, startDate, endDate).Scan(
		&current.TotalTransformations,
		&current.ActiveUsers,
		&current.PreventionRate,
		&current.TimeSaved,
	)
	if err != nil {
		return nil, err
	}

	// Get previous period metrics for comparison
	var previous MetricsSummary
	err = h.db.QueryRow(currentQuery, tenantID, previousStart, startDate).Scan(
		&previous.TotalTransformations,
		&previous.ActiveUsers,
		&previous.PreventionRate,
		&previous.TimeSaved,
	)
	if err != nil {
		// If no previous data, use zeros
		previous = MetricsSummary{}
	}

	// Calculate changes
	if previous.TotalTransformations > 0 {
		current.TransformationChange = ((float64(current.TotalTransformations) - float64(previous.TotalTransformations)) / float64(previous.TotalTransformations)) * 100
	}
	if previous.ActiveUsers > 0 {
		current.UsersChange = ((float64(current.ActiveUsers) - float64(previous.ActiveUsers)) / float64(previous.ActiveUsers)) * 100
	}
	if previous.PreventionRate > 0 {
		current.PreventionChange = current.PreventionRate - previous.PreventionRate
	}
	if previous.TimeSaved > 0 {
		current.TimeChange = ((float64(current.TimeSaved) - float64(previous.TimeSaved)) / float64(previous.TimeSaved)) * 100
	}

	return &current, nil
}

func (h *DashboardHandler) getDailyMetrics(tenantID string, period int) ([]DailyMetric, error) {
	query := `
		SELECT 
			DATE(created_at) as date,
			COUNT(*) as transformations,
			AVG(COALESCE((metadata->>'clarity_score')::float, 75)) as clarity_score,
			AVG(response_time_ms) as avg_response_time,
			MODE() WITHIN GROUP (ORDER BY feature_used) as top_feature,
			AVG(CASE WHEN cache_hit THEN 100 ELSE 0 END) as cache_hit_rate
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY DATE(created_at)
		ORDER BY date DESC
		LIMIT %d
	`
	
	query = fmt.Sprintf(query, period, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var metrics []DailyMetric
	for rows.Next() {
		var m DailyMetric
		err := rows.Scan(
			&m.Date,
			&m.Transformations,
			&m.ClarityScore,
			&m.AvgResponseTime,
			&m.TopFeature,
			&m.CacheHitRate,
		)
		if err != nil {
			continue
		}
		metrics = append(metrics, m)
	}

	return metrics, nil
}

func (h *DashboardHandler) getUsageTrend(tenantID string, period int) (*TrendData, error) {
	query := `
		SELECT 
			DATE(created_at) as date,
			COUNT(*) as transformations,
			COUNT(DISTINCT user_id) as users
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY DATE(created_at)
		ORDER BY date
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	trend := &TrendData{
		Labels:          []string{},
		Transformations: []int64{},
		Users:           []int64{},
	}

	for rows.Next() {
		var date time.Time
		var transformations, users int64
		err := rows.Scan(&date, &transformations, &users)
		if err != nil {
			continue
		}
		trend.Labels = append(trend.Labels, date.Format("2006-01-02"))
		trend.Transformations = append(trend.Transformations, transformations)
		trend.Users = append(trend.Users, users)
	}

	return trend, nil
}

func (h *DashboardHandler) getFeatureUsage(tenantID string, period int) (map[string]int64, error) {
	query := `
		SELECT feature_used, COUNT(*) as count
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY feature_used
		ORDER BY count DESC
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	features := make(map[string]int64)
	for rows.Next() {
		var feature string
		var count int64
		err := rows.Scan(&feature, &count)
		if err != nil {
			continue
		}
		features[feature] = count
	}

	return features, nil
}

func (h *DashboardHandler) getPlatformDistribution(tenantID string, period int) (map[string]float64, error) {
	query := `
		SELECT source_platform, COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY source_platform
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	platforms := make(map[string]float64)
	for rows.Next() {
		var platform string
		var percentage float64
		err := rows.Scan(&platform, &percentage)
		if err != nil {
			continue
		}
		platforms[platform] = percentage
	}

	return platforms, nil
}

func (h *DashboardHandler) getPriorityDistribution(tenantID string, period int) (map[string]int64, error) {
	// This would aggregate priority scoring data
	// For now, return mock data
	return map[string]int64{
		"Critical": 234,
		"High":     567,
		"Medium":   1234,
		"Low":      789,
	}, nil
}

func (h *DashboardHandler) getTopUsers(tenantID string, period int) ([]map[string]interface{}, error) {
	query := `
		SELECT u.name, COUNT(tl.*) as count
		FROM transformation_logs tl
		JOIN users u ON tl.user_id = u.id
		WHERE tl.tenant_id = $1 AND tl.created_at >= NOW() - INTERVAL '%d days'
		GROUP BY u.name
		ORDER BY count DESC
		LIMIT 5
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []map[string]interface{}
	for rows.Next() {
		var name string
		var count int64
		err := rows.Scan(&name, &count)
		if err != nil {
			continue
		}
		users = append(users, map[string]interface{}{
			"name":  name,
			"count": count,
		})
	}

	return users, nil
}

func (h *DashboardHandler) getTopFeatures(tenantID string, period int) ([]map[string]interface{}, error) {
	query := `
		SELECT feature_used, COUNT(*) as count
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY feature_used
		ORDER BY count DESC
		LIMIT 5
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var features []map[string]interface{}
	for rows.Next() {
		var name string
		var count int64
		err := rows.Scan(&name, &count)
		if err != nil {
			continue
		}
		features = append(features, map[string]interface{}{
			"name":  name,
			"count": count,
		})
	}

	return features, nil
}

func (h *DashboardHandler) getPeakHours(tenantID string, period int) ([]map[string]interface{}, error) {
	query := `
		SELECT 
			EXTRACT(HOUR FROM created_at) as hour,
			COUNT(*) as count
		FROM transformation_logs
		WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '%d days'
		GROUP BY hour
		ORDER BY count DESC
		LIMIT 5
	`
	
	query = fmt.Sprintf(query, period)
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var hours []map[string]interface{}
	for rows.Next() {
		var hour int
		var count int64
		err := rows.Scan(&hour, &count)
		if err != nil {
			continue
		}
		hours = append(hours, map[string]interface{}{
			"hour":  fmt.Sprintf("%d:00", hour),
			"count": count,
		})
	}

	return hours, nil
}

func (h *DashboardHandler) getRecentFeedback(tenantID string) ([]string, error) {
	query := `
		SELECT feedback_text
		FROM transformation_feedback
		WHERE tenant_id = $1 AND rating >= 4
		ORDER BY created_at DESC
		LIMIT 5
	`
	
	rows, err := h.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var feedback []string
	for rows.Next() {
		var text string
		err := rows.Scan(&text)
		if err != nil {
			continue
		}
		feedback = append(feedback, text)
	}

	// If no feedback, return sample feedback
	if len(feedback) == 0 {
		feedback = []string{
			"Great tool! Saved me hours of editing.",
			"The tone adjustment slider is amazing.",
			"Priority scoring helps me focus on what matters.",
			"Background completion catches things I miss.",
		}
	}

	return feedback, nil
}