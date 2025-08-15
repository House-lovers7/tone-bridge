# テスト戦略書

## 1. 概要

本ドキュメントでは、ToneBridgeプロジェクトの包括的なテスト戦略を定義します。品質保証、テスト自動化、継続的テストの実現により、高品質なソフトウェアデリバリーを実現します。

## 2. テスト方針

### 2.1 基本原則

- **シフトレフト**: 開発初期段階からテストを実施
- **テストピラミッド**: 単体テスト > 統合テスト > E2Eテストの比率を維持
- **自動化優先**: 手動テストを最小限に抑え、自動化を推進
- **継続的テスト**: CI/CDパイプラインにテストを統合
- **リスクベース**: リスクの高い機能を優先的にテスト

### 2.2 品質目標

| メトリクス | 目標値 |
|-----------|--------|
| コードカバレッジ | 80%以上 |
| 単体テストカバレッジ | 90%以上 |
| 統合テストカバレッジ | 70%以上 |
| E2Eテストカバレッジ | 60%以上 |
| バグ検出率 | 95%以上 |
| テスト自動化率 | 85%以上 |

## 3. テストレベル

### 3.1 単体テスト (Unit Testing)

#### 対象
- 個別の関数、メソッド、クラス
- ビジネスロジック
- ユーティリティ関数
- データ変換処理

#### 実装例

**Golang (API Gateway)**
```go
package handlers

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

func TestTransformHandler(t *testing.T) {
    tests := []struct {
        name           string
        input          TransformRequest
        expectedStatus int
        expectedError  bool
    }{
        {
            name: "Valid tone transformation",
            input: TransformRequest{
                Text:             "これは不適切です",
                TransformationType: "tone",
                TargetTone:       "warm",
                IntensityLevel:   2,
            },
            expectedStatus: 200,
            expectedError:  false,
        },
        {
            name: "Invalid intensity level",
            input: TransformRequest{
                Text:             "テストテキスト",
                TransformationType: "tone",
                TargetTone:       "warm",
                IntensityLevel:   0, // Invalid
            },
            expectedStatus: 400,
            expectedError:  true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mockService := new(MockTransformService)
            handler := NewTransformHandler(mockService)
            
            if !tt.expectedError {
                mockService.On("Transform", mock.Anything).Return(
                    &TransformResponse{
                        TransformedText: "これは改善の余地があります",
                    }, nil,
                )
            }
            
            // Execute
            resp, err := handler.Handle(tt.input)
            
            // Assert
            if tt.expectedError {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
                assert.Equal(t, tt.expectedStatus, resp.StatusCode)
            }
            
            mockService.AssertExpectations(t)
        })
    }
}
```

**Python (LLM Service)**
```python
import pytest
from unittest.mock import Mock, patch
from app.services.transform_service import TransformService
from app.models.transform import TransformRequest, TransformResponse

class TestTransformService:
    @pytest.fixture
    def service(self):
        return TransformService()
    
    @pytest.fixture
    def mock_llm_provider(self):
        with patch('app.services.transform_service.LLMProvider') as mock:
            yield mock
    
    def test_tone_transformation_success(self, service, mock_llm_provider):
        # Arrange
        request = TransformRequest(
            text="これは不適切です",
            transformation_type="tone",
            target_tone="warm",
            intensity_level=2
        )
        
        mock_llm_provider.return_value.generate.return_value = "これは改善の余地があります"
        
        # Act
        response = service.transform(request)
        
        # Assert
        assert isinstance(response, TransformResponse)
        assert response.transformed_text == "これは改善の余地があります"
        assert response.transformation_type == "tone"
        assert response.confidence_score > 0.8
    
    @pytest.mark.parametrize("intensity_level,expected_prompt_modifier", [
        (1, "subtle"),
        (2, "moderate"),
        (3, "strong"),
    ])
    def test_intensity_levels(self, service, intensity_level, expected_prompt_modifier):
        # Test that different intensity levels produce different prompts
        prompt = service._build_prompt(
            text="test",
            transformation_type="tone",
            target_tone="warm",
            intensity_level=intensity_level
        )
        
        assert expected_prompt_modifier in prompt.lower()
    
    def test_caching(self, service):
        # Arrange
        request = TransformRequest(
            text="キャッシュテスト",
            transformation_type="tone",
            target_tone="warm",
            intensity_level=2
        )
        
        # Act - First call
        response1 = service.transform(request)
        
        # Act - Second call (should hit cache)
        response2 = service.transform(request)
        
        # Assert
        assert response1.transformed_text == response2.transformed_text
        assert response2.cache_hit == True
```

### 3.2 統合テスト (Integration Testing)

#### 対象
- サービス間通信
- データベース連携
- 外部API連携
- メッセージキュー

#### 実装例

```go
package integration

import (
    "testing"
    "database/sql"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/wait"
)

func TestDatabaseIntegration(t *testing.T) {
    // PostgreSQLコンテナを起動
    ctx := context.Background()
    req := testcontainers.ContainerRequest{
        Image:        "postgres:16",
        ExposedPorts: []string{"5432/tcp"},
        WaitingFor:   wait.ForListeningPort("5432/tcp"),
        Env: map[string]string{
            "POSTGRES_DB":       "testdb",
            "POSTGRES_USER":     "test",
            "POSTGRES_PASSWORD": "test",
        },
    }
    
    postgres, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: req,
        Started:          true,
    })
    assert.NoError(t, err)
    defer postgres.Terminate(ctx)
    
    // データベース接続
    host, _ := postgres.Host(ctx)
    port, _ := postgres.MappedPort(ctx, "5432")
    dsn := fmt.Sprintf("postgres://test:test@%s:%s/testdb", host, port.Port())
    
    db, err := sql.Open("postgres", dsn)
    assert.NoError(t, err)
    defer db.Close()
    
    // マイグレーション実行
    err = RunMigrations(db)
    assert.NoError(t, err)
    
    // テストケース実行
    t.Run("Create and retrieve transformation", func(t *testing.T) {
        repo := NewTransformationRepository(db)
        
        // Create
        transformation := &Transformation{
            UserID:          uuid.New(),
            OriginalText:    "テストテキスト",
            TransformedText: "変換後テキスト",
        }
        
        err := repo.Create(transformation)
        assert.NoError(t, err)
        
        // Retrieve
        retrieved, err := repo.GetByID(transformation.ID)
        assert.NoError(t, err)
        assert.Equal(t, transformation.OriginalText, retrieved.OriginalText)
    })
}
```

### 3.3 E2Eテスト (End-to-End Testing)

#### 対象
- ユーザーシナリオ全体
- クリティカルパス
- クロスブラウザテスト
- パフォーマンステスト

#### 実装例

```typescript
// e2e/transform.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Text Transformation Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8082');
    
    // ログイン
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL('/dashboard');
  });
  
  test('Should transform text with tone adjustment', async ({ page }) => {
    // Navigate to transform page
    await page.click('[data-testid="transform-menu"]');
    
    // Input text
    await page.fill('[data-testid="input-text"]', 'これは絶対にダメです！');
    
    // Select transformation options
    await page.selectOption('[data-testid="transformation-type"]', 'tone');
    await page.selectOption('[data-testid="target-tone"]', 'warm');
    await page.fill('[data-testid="intensity"]', '2');
    
    // Submit
    await page.click('[data-testid="transform-button"]');
    
    // Wait for result
    await expect(page.locator('[data-testid="result-text"]')).toBeVisible();
    
    // Verify transformation
    const resultText = await page.textContent('[data-testid="result-text"]');
    expect(resultText).not.toContain('絶対にダメ');
    expect(resultText).toContain('改善');
    
    // Verify history is updated
    await page.click('[data-testid="history-tab"]');
    await expect(page.locator('[data-testid="history-item"]').first()).toContainText('これは絶対にダメです');
  });
  
  test('Should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/transform', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    // Try transformation
    await page.fill('[data-testid="input-text"]', 'テストテキスト');
    await page.click('[data-testid="transform-button"]');
    
    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('エラーが発生しました');
  });
});
```

## 4. テスト種別

### 4.1 機能テスト

```yaml
# test-cases/functional.yaml
test_suite: Functional Tests
test_cases:
  - id: FT-001
    name: User Registration
    priority: High
    steps:
      - action: Navigate to registration page
        expected: Registration form displayed
      - action: Enter valid email and password
        expected: No validation errors
      - action: Submit form
        expected: User created successfully
    
  - id: FT-002
    name: Text Transformation
    priority: Critical
    steps:
      - action: Login as valid user
        expected: Dashboard displayed
      - action: Enter text for transformation
        expected: Text accepted
      - action: Select transformation type
        expected: Options available
      - action: Submit transformation
        expected: Transformed text displayed
```

### 4.2 パフォーマンステスト

```javascript
// performance/k6-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Spike
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.1'],    // Error rate under 10%
  },
};

export default function () {
  const payload = JSON.stringify({
    text: 'これはパフォーマンステスト用のテキストです',
    transformation_type: 'tone',
    target_tone: 'warm',
    intensity_level: 2,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.API_TOKEN}`,
    },
  };

  const response = http.post(
    'http://localhost:8082/api/v1/transform',
    payload,
    params
  );

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has transformed text': (r) => JSON.parse(r.body).transformed_text !== undefined,
  });

  sleep(1);
}
```

### 4.3 セキュリティテスト

```python
# security/test_security.py
import pytest
from app.security import SecurityScanner

class TestSecurityVulnerabilities:
    def test_sql_injection_prevention(self, client):
        """SQLインジェクション攻撃の防御テスト"""
        malicious_input = "'; DROP TABLE users; --"
        response = client.post('/api/v1/transform', json={
            'text': malicious_input,
            'transformation_type': 'tone'
        })
        
        # Should sanitize input, not execute SQL
        assert response.status_code in [200, 400]
        
        # Verify database integrity
        assert self.verify_database_intact()
    
    def test_xss_prevention(self, client):
        """XSS攻撃の防御テスト"""
        xss_payload = "<script>alert('XSS')</script>"
        response = client.post('/api/v1/transform', json={
            'text': xss_payload,
            'transformation_type': 'tone'
        })
        
        # Response should escape HTML
        assert '<script>' not in response.json.get('transformed_text', '')
    
    def test_rate_limiting(self, client):
        """レート制限のテスト"""
        for i in range(101):  # Exceed rate limit of 100/min
            response = client.get('/api/v1/health')
            
            if i >= 100:
                assert response.status_code == 429
                assert 'X-RateLimit-Remaining' in response.headers
    
    def test_jwt_token_validation(self, client):
        """JWT トークン検証のテスト"""
        # Invalid token
        response = client.get('/api/v1/protected', headers={
            'Authorization': 'Bearer invalid.token.here'
        })
        assert response.status_code == 401
        
        # Expired token
        expired_token = self.generate_expired_token()
        response = client.get('/api/v1/protected', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        assert response.status_code == 401
```

## 5. テスト自動化

### 5.1 CI/CDパイプライン

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, llm-service, auth-service]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Go
        if: matrix.service == 'api-gateway'
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Setup Python
        if: matrix.service == 'llm-service'
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd services/${{ matrix.service }}
          make install
      
      - name: Run unit tests
        run: |
          cd services/${{ matrix.service }}
          make test-unit
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./services/${{ matrix.service }}/coverage.xml
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start dependencies
        run: |
          docker-compose -f docker-compose.test.yml up -d postgres redis
          sleep 10
      
      - name: Run integration tests
        run: |
          make test-integration
      
      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v
  
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start all services
        run: |
          docker-compose up -d
          ./scripts/wait-for-services.sh
      
      - name: Setup Playwright
        run: |
          npm ci
          npx playwright install
      
      - name: Run E2E tests
        run: |
          npm run test:e2e
      
      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-artifacts
          path: |
            test-results/
            screenshots/
            videos/
```

### 5.2 テスト実行スクリプト

```bash
#!/bin/bash
# scripts/run-tests.sh

set -e

echo "🧪 Running ToneBridge Test Suite"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run tests
run_test_suite() {
    local suite=$1
    local command=$2
    
    echo -e "${YELLOW}Running $suite...${NC}"
    
    if eval $command; then
        echo -e "${GREEN}✓ $suite passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $suite failed${NC}"
        return 1
    fi
}

# Unit Tests
run_test_suite "Unit Tests (Go)" "cd services/api-gateway && go test ./... -v -cover"
run_test_suite "Unit Tests (Python)" "cd services/llm && pytest tests/unit -v --cov"

# Integration Tests
docker-compose -f docker-compose.test.yml up -d
sleep 10
run_test_suite "Integration Tests" "go test ./tests/integration -v"
docker-compose -f docker-compose.test.yml down

# E2E Tests
if [ "$RUN_E2E" = "true" ]; then
    docker-compose up -d
    ./scripts/wait-for-services.sh
    run_test_suite "E2E Tests" "npm run test:e2e"
    docker-compose down
fi

# Performance Tests
if [ "$RUN_PERF" = "true" ]; then
    run_test_suite "Performance Tests" "k6 run performance/k6-load-test.js"
fi

# Security Tests
if [ "$RUN_SECURITY" = "true" ]; then
    run_test_suite "Security Tests" "python tests/security/run_security_tests.py"
fi

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}All tests completed successfully!${NC}"
```

## 6. テストデータ管理

### 6.1 テストデータ生成

```go
package testdata

import (
    "github.com/brianvoe/gofakeit/v6"
)

type TestDataGenerator struct {
    faker *gofakeit.Faker
}

func NewTestDataGenerator() *TestDataGenerator {
    return &TestDataGenerator{
        faker: gofakeit.New(0),
    }
}

func (g *TestDataGenerator) GenerateUser() *User {
    return &User{
        ID:       uuid.New(),
        Email:    g.faker.Email(),
        Name:     g.faker.Name(),
        Role:     "member",
        OrgID:    uuid.New(),
        CreatedAt: time.Now(),
    }
}

func (g *TestDataGenerator) GenerateTransformRequest() *TransformRequest {
    tones := []string{"warm", "professional", "casual", "formal"}
    types := []string{"tone", "structure", "summarize", "terminology"}
    
    return &TransformRequest{
        Text:               g.faker.Paragraph(3, 5, 10, " "),
        TransformationType: types[g.faker.Number(0, len(types)-1)],
        TargetTone:        tones[g.faker.Number(0, len(tones)-1)],
        IntensityLevel:    g.faker.Number(1, 3),
    }
}

// Seed data for consistent testing
func SeedTestDatabase(db *sql.DB) error {
    generator := NewTestDataGenerator()
    
    // Create test organization
    org := &Organization{
        ID:   uuid.MustParse("00000000-0000-0000-0000-000000000001"),
        Name: "Test Organization",
        Plan: "enterprise",
    }
    
    // Create test users
    users := []*User{
        {
            ID:    uuid.MustParse("00000000-0000-0000-0000-000000000002"),
            Email: "admin@test.com",
            Role:  "admin",
            OrgID: org.ID,
        },
        {
            ID:    uuid.MustParse("00000000-0000-0000-0000-000000000003"),
            Email: "user@test.com",
            Role:  "member",
            OrgID: org.ID,
        },
    }
    
    // Insert data
    if err := insertOrganization(db, org); err != nil {
        return err
    }
    
    for _, user := range users {
        if err := insertUser(db, user); err != nil {
            return err
        }
    }
    
    return nil
}
```

## 7. テストレポート

### 7.1 カバレッジレポート

```html
<!-- coverage-report-template.html -->
<!DOCTYPE html>
<html>
<head>
    <title>ToneBridge Test Coverage Report</title>
    <style>
        .coverage-high { background-color: #4CAF50; }
        .coverage-medium { background-color: #FFC107; }
        .coverage-low { background-color: #F44336; }
    </style>
</head>
<body>
    <h1>Test Coverage Report</h1>
    <div class="summary">
        <h2>Overall Coverage: {{ overall_coverage }}%</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Line Coverage</th>
                <th>Branch Coverage</th>
                <th>Function Coverage</th>
            </tr>
            {% for component in components %}
            <tr>
                <td>{{ component.name }}</td>
                <td class="coverage-{{ component.line_coverage_class }}">
                    {{ component.line_coverage }}%
                </td>
                <td class="coverage-{{ component.branch_coverage_class }}">
                    {{ component.branch_coverage }}%
                </td>
                <td class="coverage-{{ component.function_coverage_class }}">
                    {{ component.function_coverage }}%
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
```

### 7.2 テスト実行レポート

```json
{
  "test_run": {
    "id": "run-2024-01-15-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "duration": "15m 32s",
    "environment": "staging",
    "summary": {
      "total": 524,
      "passed": 518,
      "failed": 4,
      "skipped": 2,
      "pass_rate": "98.85%"
    },
    "suites": [
      {
        "name": "Unit Tests",
        "tests": 350,
        "passed": 348,
        "failed": 2,
        "duration": "2m 15s"
      },
      {
        "name": "Integration Tests",
        "tests": 124,
        "passed": 122,
        "failed": 2,
        "duration": "8m 45s"
      },
      {
        "name": "E2E Tests",
        "tests": 50,
        "passed": 48,
        "failed": 0,
        "skipped": 2,
        "duration": "4m 32s"
      }
    ],
    "failures": [
      {
        "test": "TestTransformWithInvalidToken",
        "suite": "Unit Tests",
        "error": "Expected 401, got 500",
        "file": "auth_test.go:45"
      }
    ]
  }
}
```

## 8. 継続的改善

### 8.1 メトリクス追跡

```sql
-- Test metrics tracking
CREATE TABLE test_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id VARCHAR(100),
    date DATE,
    total_tests INTEGER,
    passed INTEGER,
    failed INTEGER,
    skipped INTEGER,
    coverage_percentage DECIMAL(5,2),
    duration_seconds INTEGER,
    environment VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query for trend analysis
SELECT 
    date,
    AVG(coverage_percentage) as avg_coverage,
    AVG(passed::DECIMAL / total_tests * 100) as pass_rate,
    AVG(duration_seconds) as avg_duration
FROM test_metrics
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC;
```

### 8.2 改善アクションアイテム

| 課題 | アクション | 優先度 | 期限 |
|-----|-----------|--------|------|
| E2Eテストの実行時間が長い | Parallel実行の実装 | 高 | 2024 Q1 |
| フレーキーテストの存在 | テストの安定化 | 高 | 2024 Q1 |
| セキュリティテストの不足 | OWASP ZAPの導入 | 中 | 2024 Q2 |
| パフォーマンステストの自動化 | k6のCI統合 | 中 | 2024 Q2 |

## まとめ

ToneBridgeのテスト戦略は、品質を最優先に、自動化と継続的改善を通じて、信頼性の高いソフトウェアデリバリーを実現します。テストピラミッドの原則に従い、適切なレベルでのテストを実施し、早期のバグ検出と修正を可能にします。
