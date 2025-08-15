# 開発者ガイド

## 1. はじめに

本ガイドは、ToneBridgeプロジェクトの開発に参加する開発者向けのガイドラインとベストプラクティスを提供します。

## 2. 開発環境セットアップ

### 2.1 必要なツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Go | 1.21+ | API Gateway、マイクロサービス開発 |
| Python | 3.11+ | LLMサービス開発 |
| Node.js | 18+ | フロントエンド開発 |
| Docker | 20.10+ | コンテナ化 |
| PostgreSQL | 16+ | データベース |
| Redis | 7+ | キャッシング |

### 2.2 環境構築手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/tonebridge/tonebridge.git
cd tonebridge

# 2. 開発用環境変数の設定
cp .env.example .env.development
# .env.developmentを編集してAPIキー等を設定

# 3. 依存関係のインストール
make install-deps

# 4. データベースのセットアップ
make db-setup

# 5. 開発サーバーの起動
make dev
```

### 2.3 IDE設定

#### VS Code推奨拡張機能

```json
{
  "recommendations": [
    "golang.go",
    "ms-python.python",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "ms-vscode.makefile-tools",
    "redhat.vscode-yaml",
    "hashicorp.terraform"
  ]
}
```

#### VS Code設定

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[go]": {
    "editor.defaultFormatter": "golang.go"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "go.lintTool": "golangci-lint",
  "go.testFlags": ["-v"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

## 3. アーキテクチャ概要

### 3.1 システム構成

```
┌─────────────────┐
│   Frontend      │  React/Vue.js
├─────────────────┤
│  API Gateway    │  Golang (Fiber v2)
├─────────────────┤
│  Microservices  │
│  ├─ LLM Service │  Python (FastAPI)
│  ├─ Auth Service│  Golang
│  └─ Analytics   │  Golang
├─────────────────┤
│   Data Layer    │
│  ├─ PostgreSQL  │  Main DB + pgvector
│  └─ Redis       │  Cache
└─────────────────┘
```

### 3.2 主要コンポーネント

- **API Gateway**: すべてのリクエストのエントリーポイント
- **LLM Service**: AI変換処理を担当
- **Auth Service**: 認証・認可管理
- **Analytics Service**: 使用統計と分析

## 4. コーディング規約

### 4.1 Go言語規約

```go
// Package名は小文字、単数形
package handler

// インターフェース名は-erで終わる
type Transformer interface {
    Transform(ctx context.Context, req Request) (*Response, error)
}

// エラーハンドリング
func ProcessRequest(req *Request) (*Response, error) {
    if err := req.Validate(); err != nil {
        return nil, fmt.Errorf("validation failed: %w", err)
    }
    
    result, err := transform(req)
    if err != nil {
        return nil, fmt.Errorf("transform failed: %w", err)
    }
    
    return result, nil
}

// Context使用
func HandleWithContext(ctx context.Context) error {
    // タイムアウト設定
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()
    
    select {
    case <-ctx.Done():
        return ctx.Err()
    case result := <-process():
        return handleResult(result)
    }
}
```

### 4.2 Python規約

```python
# Type hints使用
from typing import Optional, List, Dict
from pydantic import BaseModel

class TransformRequest(BaseModel):
    """変換リクエストモデル"""
    text: str
    transformation_type: str
    target_tone: Optional[str] = None
    intensity_level: int = 2
    
    def validate_intensity(self) -> bool:
        """強度レベルの検証"""
        return 1 <= self.intensity_level <= 3

# Async/await使用
async def transform_text(
    request: TransformRequest,
    llm_provider: LLMProvider
) -> TransformResponse:
    """
    テキスト変換処理
    
    Args:
        request: 変換リクエスト
        llm_provider: LLMプロバイダー
        
    Returns:
        TransformResponse: 変換結果
        
    Raises:
        ValidationError: バリデーションエラー
        TransformError: 変換エラー
    """
    if not request.validate_intensity():
        raise ValidationError("Invalid intensity level")
    
    try:
        result = await llm_provider.generate(
            prompt=build_prompt(request),
            temperature=0.7
        )
        return TransformResponse(
            transformed_text=result,
            original_text=request.text
        )
    except Exception as e:
        logger.error(f"Transform failed: {e}")
        raise TransformError(f"Failed to transform text: {e}")

# ロギング設定
import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

### 4.3 TypeScript/JavaScript規約

```typescript
// インターフェース定義
interface TransformRequest {
  text: string;
  transformationType: TransformationType;
  targetTone?: ToneType;
  intensityLevel: IntensityLevel;
}

// Enum使用
enum TransformationType {
  TONE = 'tone',
  STRUCTURE = 'structure',
  SUMMARIZE = 'summarize',
  TERMINOLOGY = 'terminology'
}

// 型ガード
function isValidRequest(req: unknown): req is TransformRequest {
  return (
    typeof req === 'object' &&
    req !== null &&
    'text' in req &&
    'transformationType' in req
  );
}

// Async/Await使用
async function transformText(
  request: TransformRequest
): Promise<TransformResponse> {
  try {
    const response = await api.post('/transform', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new APIError(
        error.response?.data?.message || 'Transform failed',
        error.response?.status
      );
    }
    throw error;
  }
}

// React Component
const TransformForm: React.FC<TransformFormProps> = ({ 
  onSubmit,
  initialValues 
}) => {
  const [formData, setFormData] = useState<TransformRequest>(
    initialValues || defaultValues
  );
  
  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Submit failed:', error);
    }
  }, [formData, onSubmit]);
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
};
```

## 5. API開発ガイドライン

### 5.1 RESTful API設計

```yaml
# API設計原則
principles:
  - リソース指向URL
  - 適切なHTTPメソッド使用
  - ステートレス
  - 一貫性のあるレスポンス形式

# URLパターン
patterns:
  collection: /api/v1/{resources}
  item: /api/v1/{resources}/{id}
  action: /api/v1/{resources}/{id}/{action}

# HTTPメソッド
methods:
  GET: リソース取得
  POST: リソース作成
  PUT: リソース完全更新
  PATCH: リソース部分更新
  DELETE: リソース削除
```

### 5.2 エンドポイント実装例

```go
// handlers/transform.go
package handlers

import (
    "github.com/gofiber/fiber/v2"
    "github.com/tonebridge/api/services"
)

type TransformHandler struct {
    service services.TransformService
    logger  logging.Logger
}

// POST /api/v1/transform
func (h *TransformHandler) Transform(c *fiber.Ctx) error {
    // リクエスト解析
    var req TransformRequest
    if err := c.BodyParser(&req); err != nil {
        return c.Status(400).JSON(ErrorResponse{
            Error: "Invalid request body",
            Code:  "INVALID_REQUEST",
        })
    }
    
    // バリデーション
    if err := req.Validate(); err != nil {
        return c.Status(400).JSON(ErrorResponse{
            Error: err.Error(),
            Code:  "VALIDATION_ERROR",
        })
    }
    
    // ユーザーコンテキスト取得
    user := c.Locals("user").(*User)
    
    // 変換処理
    result, err := h.service.Transform(c.Context(), user, &req)
    if err != nil {
        h.logger.Error("Transform failed", 
            zap.Error(err),
            zap.String("user_id", user.ID),
        )
        return c.Status(500).JSON(ErrorResponse{
            Error: "Transform failed",
            Code:  "TRANSFORM_ERROR",
        })
    }
    
    // レスポンス
    return c.JSON(TransformResponse{
        Success: true,
        Data:    result,
    })
}

// ミドルウェア適用
func SetupRoutes(app *fiber.App, handler *TransformHandler) {
    api := app.Group("/api/v1")
    
    // 認証ミドルウェア
    api.Use(middleware.Authenticate())
    
    // レート制限
    api.Use(middleware.RateLimit(100, time.Minute))
    
    // ルート設定
    api.Post("/transform", handler.Transform)
}
```

### 5.3 エラーハンドリング

```go
// errors/errors.go
package errors

type AppError struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Status  int    `json:"-"`
}

func (e *AppError) Error() string {
    return e.Message
}

var (
    ErrNotFound = &AppError{
        Code:    "NOT_FOUND",
        Message: "Resource not found",
        Status:  404,
    }
    
    ErrUnauthorized = &AppError{
        Code:    "UNAUTHORIZED",
        Message: "Unauthorized access",
        Status:  401,
    }
    
    ErrRateLimited = &AppError{
        Code:    "RATE_LIMITED",
        Message: "Too many requests",
        Status:  429,
    }
)

// エラーハンドラー
func ErrorHandler(c *fiber.Ctx, err error) error {
    if appErr, ok := err.(*AppError); ok {
        return c.Status(appErr.Status).JSON(fiber.Map{
            "error": appErr.Message,
            "code":  appErr.Code,
        })
    }
    
    // デフォルトエラー
    return c.Status(500).JSON(fiber.Map{
        "error": "Internal server error",
        "code":  "INTERNAL_ERROR",
    })
}
```

## 6. データベース開発

### 6.1 マイグレーション

```sql
-- migrations/001_create_users.up.sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    organization_id UUID REFERENCES organizations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);

-- Trigger for updated_at
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### 6.2 データアクセス層

```go
// repository/user_repository.go
package repository

import (
    "context"
    "database/sql"
    "github.com/google/uuid"
)

type UserRepository struct {
    db *sql.DB
}

func (r *UserRepository) Create(ctx context.Context, user *User) error {
    query := `
        INSERT INTO users (email, password_hash, name, role, organization_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
    `
    
    err := r.db.QueryRowContext(
        ctx, query,
        user.Email,
        user.PasswordHash,
        user.Name,
        user.Role,
        user.OrganizationID,
    ).Scan(&user.ID, &user.CreatedAt, &user.UpdatedAt)
    
    if err != nil {
        return fmt.Errorf("failed to create user: %w", err)
    }
    
    return nil
}

func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*User, error) {
    query := `
        SELECT id, email, password_hash, name, role, organization_id, 
               created_at, updated_at
        FROM users
        WHERE email = $1
    `
    
    var user User
    err := r.db.QueryRowContext(ctx, query, email).Scan(
        &user.ID,
        &user.Email,
        &user.PasswordHash,
        &user.Name,
        &user.Role,
        &user.OrganizationID,
        &user.CreatedAt,
        &user.UpdatedAt,
    )
    
    if err == sql.ErrNoRows {
        return nil, ErrNotFound
    }
    if err != nil {
        return nil, fmt.Errorf("failed to get user: %w", err)
    }
    
    return &user, nil
}

// トランザクション使用例
func (r *UserRepository) UpdateWithTransaction(
    ctx context.Context,
    userID uuid.UUID,
    updateFn func(*User) error,
) error {
    tx, err := r.db.BeginTx(ctx, nil)
    if err != nil {
        return err
    }
    defer tx.Rollback()
    
    // SELECT FOR UPDATE
    query := `
        SELECT * FROM users 
        WHERE id = $1 
        FOR UPDATE
    `
    
    var user User
    err = tx.QueryRowContext(ctx, query, userID).Scan(&user)
    if err != nil {
        return err
    }
    
    // 更新処理
    if err := updateFn(&user); err != nil {
        return err
    }
    
    // UPDATE
    updateQuery := `
        UPDATE users 
        SET name = $1, role = $2, updated_at = NOW()
        WHERE id = $3
    `
    
    _, err = tx.ExecContext(ctx, updateQuery, user.Name, user.Role, user.ID)
    if err != nil {
        return err
    }
    
    return tx.Commit()
}
```

## 7. テスト開発

### 7.1 単体テスト

```go
// handlers/transform_test.go
package handlers_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

type MockTransformService struct {
    mock.Mock
}

func (m *MockTransformService) Transform(ctx context.Context, user *User, req *TransformRequest) (*TransformResult, error) {
    args := m.Called(ctx, user, req)
    if result := args.Get(0); result != nil {
        return result.(*TransformResult), args.Error(1)
    }
    return nil, args.Error(1)
}

func TestTransformHandler_Success(t *testing.T) {
    // Setup
    app := fiber.New()
    mockService := new(MockTransformService)
    handler := NewTransformHandler(mockService)
    
    // Mock expectations
    expectedResult := &TransformResult{
        TransformedText: "変換されたテキスト",
    }
    mockService.On("Transform", mock.Anything, mock.Anything, mock.Anything).
        Return(expectedResult, nil)
    
    // Setup route
    app.Post("/transform", handler.Transform)
    
    // Create request
    reqBody := `{
        "text": "元のテキスト",
        "transformation_type": "tone",
        "target_tone": "warm",
        "intensity_level": 2
    }`
    
    req := httptest.NewRequest("POST", "/transform", strings.NewReader(reqBody))
    req.Header.Set("Content-Type", "application/json")
    
    // Execute
    resp, err := app.Test(req)
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)
    
    mockService.AssertExpectations(t)
}
```

### 7.2 統合テスト

```go
// integration/api_test.go
package integration_test

import (
    "testing"
    "github.com/testcontainers/testcontainers-go"
)

func TestAPIIntegration(t *testing.T) {
    // Start containers
    ctx := context.Background()
    
    // PostgreSQL
    postgresReq := testcontainers.ContainerRequest{
        Image:        "postgres:16",
        ExposedPorts: []string{"5432/tcp"},
        Env: map[string]string{
            "POSTGRES_PASSWORD": "test",
        },
    }
    
    postgres, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: postgresReq,
        Started:          true,
    })
    require.NoError(t, err)
    defer postgres.Terminate(ctx)
    
    // Redis
    redisReq := testcontainers.ContainerRequest{
        Image:        "redis:7-alpine",
        ExposedPorts: []string{"6379/tcp"},
    }
    
    redis, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: redisReq,
        Started:          true,
    })
    require.NoError(t, err)
    defer redis.Terminate(ctx)
    
    // Get connection strings
    postgresHost, _ := postgres.Host(ctx)
    postgresPort, _ := postgres.MappedPort(ctx, "5432")
    
    redisHost, _ := redis.Host(ctx)
    redisPort, _ := redis.MappedPort(ctx, "6379")
    
    // Setup application
    config := &Config{
        DatabaseURL: fmt.Sprintf("postgres://postgres:test@%s:%s/postgres", postgresHost, postgresPort.Port()),
        RedisURL:    fmt.Sprintf("redis://%s:%s", redisHost, redisPort.Port()),
    }
    
    app := SetupApp(config)
    
    // Run tests
    t.Run("Transform API", func(t *testing.T) {
        // Create user
        user := createTestUser(t, app)
        
        // Get token
        token := loginAndGetToken(t, app, user)
        
        // Test transform
        req := httptest.NewRequest("POST", "/api/v1/transform", strings.NewReader(`{
            "text": "テストテキスト",
            "transformation_type": "tone"
        }`))
        req.Header.Set("Authorization", "Bearer "+token)
        
        resp, err := app.Test(req)
        require.NoError(t, err)
        assert.Equal(t, 200, resp.StatusCode)
    })
}
```

## 8. デバッグとトラブルシューティング

### 8.1 ログ分析

```bash
# ログレベル設定
export LOG_LEVEL=debug

# 構造化ログの確認
docker-compose logs -f api-gateway | jq '.'

# 特定のエラー検索
docker-compose logs | grep -i error | tail -20

# トレースID追跡
docker-compose logs | grep "trace_id=abc123"
```

### 8.2 デバッグツール

```go
// デバッグ用ミドルウェア
func DebugMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        if os.Getenv("DEBUG") == "true" {
            log.Printf("Request: %s %s", c.Method(), c.Path())
            log.Printf("Headers: %v", c.GetReqHeaders())
            
            if body := c.Body(); len(body) > 0 {
                log.Printf("Body: %s", string(body))
            }
        }
        
        return c.Next()
    }
}

// pprof有効化
import _ "net/http/pprof"

func EnableProfiling() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
}
```

### 8.3 パフォーマンス分析

```bash
# CPU プロファイリング
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# メモリプロファイリング
go tool pprof http://localhost:6060/debug/pprof/heap

# ゴルーチンリーク検出
go tool pprof http://localhost:6060/debug/pprof/goroutine

# トレース取得
curl http://localhost:6060/debug/pprof/trace?seconds=5 > trace.out
go tool trace trace.out
```

## 9. CI/CD

### 9.1 GitHub Actions設定

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: golangci-lint
        uses: golangci/golangci-lint-action@v3
        with:
          version: latest
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Python Lint
        run: |
          pip install flake8 black mypy
          flake8 services/llm
          black --check services/llm
          mypy services/llm

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: make test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.txt

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker build -t tonebridge/api-gateway:${{ github.sha }} ./services/api-gateway
          docker build -t tonebridge/llm-service:${{ github.sha }} ./services/llm
```

### 9.2 ローカル開発フロー

```bash
# 1. フィーチャーブランチ作成
git checkout -b feature/new-feature

# 2. 開発とテスト
make dev
make test

# 3. コミット前チェック
make pre-commit

# 4. コミット
git add .
git commit -m "feat: add new feature"

# 5. プッシュとPR作成
git push origin feature/new-feature
gh pr create --title "Add new feature" --body "Description of changes"
```

## 10. ベストプラクティス

### 10.1 セキュリティ

- 環境変数でシークレット管理
- SQLインジェクション対策（プリペアドステートメント）
- XSS対策（出力エスケープ）
- CSRF対策（トークン検証）
- レート制限実装
- 入力値検証

### 10.2 パフォーマンス

- データベースインデックス最適化
- N+1問題の回避
- 適切なキャッシング戦略
- 非同期処理の活用
- バッチ処理の実装
- コネクションプーリング

### 10.3 保守性

- 明確なコード構造
- 適切なログ出力
- 包括的なテスト
- ドキュメント更新
- コードレビュー
- 技術的負債の管理

## 11. トラブルシューティング

### 11.1 よくある問題

#### データベース接続エラー
```bash
# 接続確認
psql -h localhost -U tonebridge -d tonebridge

# 権限確認
SELECT * FROM pg_roles WHERE rolname = 'tonebridge';

# 接続数確認
SELECT count(*) FROM pg_stat_activity;
```

#### メモリリーク
```go
// goroutineリーク検出
func DetectGoroutineLeak() {
    before := runtime.NumGoroutine()
    
    // 処理実行
    runYourCode()
    
    time.Sleep(100 * time.Millisecond)
    after := runtime.NumGoroutine()
    
    if after > before {
        log.Printf("Possible goroutine leak: before=%d, after=%d", before, after)
    }
}
```

#### パフォーマンス問題
```bash
# スロークエリ特定
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# インデックス使用状況
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

## 12. リソース

### 12.1 ドキュメント
- [API Reference](./API_REFERENCE.md)
- [Architecture Guide](./docs/02_architecture/system_architecture.md)
- [Database Schema](./docs/03_data_design/table_definitions.md)

### 12.2 ツール
- [Postman Collection](./postman/ToneBridge.postman_collection.json)
- [OpenAPI Specification](./openapi/spec.yaml)
- [Database Migrations](./migrations/)

### 12.3 外部リンク
- [Go Documentation](https://go.dev/doc/)
- [Python Documentation](https://docs.python.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

## まとめ

本ガイドは、ToneBridge開発の基本的なガイドラインを提供しています。チーム全体で一貫した開発アプローチを維持し、高品質なソフトウェアを提供することを目指します。