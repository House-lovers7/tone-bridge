# コンポーネント設計書

## 1. 概要

本ドキュメントでは、ToneBridgeシステムを構成する各コンポーネントの詳細設計について説明します。各コンポーネントの責務、インターフェース、実装詳細、および相互作用を定義します。

## 2. コンポーネント一覧

| コンポーネント名 | 言語/技術 | 責務 | 依存関係 |
|---------------|----------|------|--------|
| API Gateway | Golang/Fiber | リクエストルーティング、認証 | Auth Service, LLM Service |
| LLM Service | Python/FastAPI | AI変換処理 | Redis, PostgreSQL |
| Auth Service | Golang | 認証・認可 | PostgreSQL, Redis |
| Analytics Service | Golang | 分析・統計 | PostgreSQL |
| Notification Service | Golang | 通知配信 | Redis, External APIs |
| Web Frontend | TypeScript/React | ユーザーインターフェース | API Gateway |
| Admin Dashboard | TypeScript/Vue | 管理画面 | API Gateway |

## 3. API Gateway コンポーネント

### 3.1 概要

API Gatewayは、すべての外部リクエストのエントリーポイントとして機能し、リクエストの検証、認証、ルーティング、レート制限を担当します。

### 3.2 アーキテクチャ

```go
package gateway

type APIGateway struct {
    app            *fiber.App
    authService    services.AuthService
    rateLimiter    middleware.RateLimiter
    circuitBreaker middleware.CircuitBreaker
    validator      validation.Validator
    logger         logging.Logger
    metrics        monitoring.MetricsCollector
}

type Config struct {
    Port            int
    MaxConnections  int
    ReadTimeout     time.Duration
    WriteTimeout    time.Duration
    RateLimitConfig RateLimitConfig
    AuthConfig      AuthConfig
}
```

### 3.3 主要機能

#### 3.3.1 リクエストルーティング

```go
func (g *APIGateway) SetupRoutes() {
    // Public routes
    public := g.app.Group("/api/v1")
    public.Post("/auth/register", g.handleRegister)
    public.Post("/auth/login", g.handleLogin)
    public.Get("/health", g.handleHealth)
    
    // Protected routes
    protected := g.app.Group("/api/v1")
    protected.Use(g.authMiddleware)
    protected.Use(g.rateLimitMiddleware)
    
    // Transform endpoints
    transform := protected.Group("/transform")
    transform.Post("/tone", g.handleToneTransform)
    transform.Post("/structure", g.handleStructureTransform)
    transform.Post("/summarize", g.handleSummarize)
    transform.Post("/terminology", g.handleTerminology)
    
    // WebSocket endpoint
    g.app.Get("/ws", websocket.New(g.handleWebSocket))
}
```

#### 3.3.2 認証ミドルウェア

```go
func (g *APIGateway) authMiddleware(c *fiber.Ctx) error {
    token := c.Get("Authorization")
    if token == "" {
        return c.Status(401).JSON(fiber.Map{
            "error": "Missing authorization token",
        })
    }
    
    // Verify JWT token
    claims, err := g.authService.VerifyToken(token)
    if err != nil {
        return c.Status(401).JSON(fiber.Map{
            "error": "Invalid token",
        })
    }
    
    // Store user context
    c.Locals("user", claims.User)
    c.Locals("org_id", claims.OrgID)
    
    return c.Next()
}
```

#### 3.3.3 レート制限

```go
type RateLimiter struct {
    redis      *redis.Client
    limits     map[string]RateLimit
    windowSize time.Duration
}

type RateLimit struct {
    MaxRequests int
    Window      time.Duration
    BurstSize   int
}

func (r *RateLimiter) Check(key string) (bool, error) {
    // Sliding window algorithm
    now := time.Now().Unix()
    windowStart := now - int64(r.windowSize.Seconds())
    
    pipe := r.redis.Pipeline()
    
    // Remove old entries
    pipe.ZRemRangeByScore(context.Background(), key, "0", fmt.Sprint(windowStart))
    
    // Count current requests
    pipe.ZCard(context.Background(), key)
    
    // Add current request
    pipe.ZAdd(context.Background(), key, redis.Z{
        Score:  float64(now),
        Member: fmt.Sprintf("%d-%s", now, uuid.New().String()),
    })
    
    // Set expiry
    pipe.Expire(context.Background(), key, r.windowSize)
    
    results, err := pipe.Exec(context.Background())
    if err != nil {
        return false, err
    }
    
    count := results[1].(*redis.IntCmd).Val()
    limit := r.limits[key].MaxRequests
    
    return count <= int64(limit), nil
}
```

### 3.4 エラーハンドリング

```go
func (g *APIGateway) errorHandler(c *fiber.Ctx, err error) error {
    code := fiber.StatusInternalServerError
    message := "Internal server error"
    
    var e *fiber.Error
    if errors.As(err, &e) {
        code = e.Code
        message = e.Message
    }
    
    // Log error
    g.logger.Error("Request failed",
        zap.Error(err),
        zap.String("path", c.Path()),
        zap.String("method", c.Method()),
        zap.String("trace_id", c.Get("X-Trace-ID")),
    )
    
    // Record metrics
    g.metrics.RecordError(c.Path(), code)
    
    return c.Status(code).JSON(fiber.Map{
        "error": message,
        "trace_id": c.Get("X-Trace-ID"),
    })
}
```

## 4. LLM Service コンポーネント

### 4.1 概要

LLM Serviceは、AI駆動のテキスト変換を担当する中核コンポーネントです。複数のLLMプロバイダーをサポートし、フォールバック機構を備えています。

### 4.2 アーキテクチャ

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from langchain import LLMChain, PromptTemplate
from pydantic import BaseModel

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

class LLMService:
    def __init__(self):
        self.providers = self._initialize_providers()
        self.chains = self._initialize_chains()
        self.cache = RedisCache()
        self.metrics = MetricsCollector()
    
    def _initialize_providers(self) -> Dict[str, LLMProvider]:
        return {
            "openai": OpenAIProvider(os.getenv("OPENAI_API_KEY")),
            "anthropic": AnthropicProvider(os.getenv("ANTHROPIC_API_KEY")),
            "google": GoogleProvider(os.getenv("GOOGLE_API_KEY"))
        }
    
    def _initialize_chains(self) -> Dict[str, LLMChain]:
        return {
            "tone": self._create_tone_chain(),
            "structure": self._create_structure_chain(),
            "summarize": self._create_summarize_chain(),
            "terminology": self._create_terminology_chain()
        }
```

### 4.3 変換チェーン実装

#### 4.3.1 トーン変換チェーン

```python
class ToneTransformationChain:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.prompt_template = PromptTemplate(
            input_variables=["text", "target_tone", "intensity"],
            template="""
            You are an expert in Japanese business communication.
            
            Transform the following text to have a {target_tone} tone.
            Intensity level: {intensity} (1=subtle, 2=moderate, 3=strong)
            
            Original text:
            {text}
            
            Rules:
            1. Preserve the core message and all important information
            2. Adjust formality and emotional tone appropriately
            3. Use natural Japanese expressions
            4. Maintain technical accuracy
            
            Transformed text:
            """
        )
    
    async def transform(self, text: str, target_tone: str, intensity: int) -> TransformResult:
        # Generate cache key
        cache_key = self._generate_cache_key(text, target_tone, intensity)
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached:
            return TransformResult.parse_raw(cached)
        
        # Prepare prompt
        prompt = self.prompt_template.format(
            text=text,
            target_tone=target_tone,
            intensity=intensity
        )
        
        # Generate transformation
        start_time = time.time()
        transformed_text = await self.llm.generate(prompt)
        processing_time = time.time() - start_time
        
        # Create result
        result = TransformResult(
            original_text=text,
            transformed_text=transformed_text,
            transformation_type="tone",
            target_tone=target_tone,
            intensity=intensity,
            processing_time_ms=int(processing_time * 1000),
            model_used=self.llm.get_model_info()["name"],
            confidence_score=self._calculate_confidence(text, transformed_text)
        )
        
        # Cache result
        await self.cache.set(cache_key, result.json(), expire=3600)
        
        # Record metrics
        self.metrics.record_transformation(
            transformation_type="tone",
            processing_time=processing_time,
            model=self.llm.get_model_info()["name"]
        )
        
        return result
```

#### 4.3.2 構造化チェーン

```python
class StructureTransformationChain:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.analyzer = TextStructureAnalyzer()
        
    async def transform(self, text: str, options: Dict) -> StructureResult:
        # Analyze current structure
        analysis = self.analyzer.analyze(text)
        
        # Determine transformation strategy
        if analysis.structure_score < 0.5:
            strategy = "complete_restructure"
        elif analysis.structure_score < 0.7:
            strategy = "moderate_improvement"
        else:
            strategy = "minor_adjustments"
        
        # Apply transformation
        prompt = self._build_structure_prompt(text, strategy, options)
        structured_text = await self.llm.generate(prompt)
        
        # Post-process
        structured_text = self._add_formatting(structured_text, options)
        
        return StructureResult(
            original_text=text,
            structured_text=structured_text,
            structure_score=self.analyzer.analyze(structured_text).structure_score,
            improvements=self._identify_improvements(text, structured_text)
        )
```

### 4.4 キャッシング戦略

```python
class CacheManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl_config = {
            "tone": 3600,        # 1 hour
            "structure": 7200,   # 2 hours
            "summarize": 1800,   # 30 minutes
            "terminology": 86400 # 24 hours
        }
    
    def generate_key(self, transformation_type: str, text: str, params: Dict) -> str:
        # Create deterministic cache key
        content = f"{transformation_type}:{text}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get_or_compute(self, key: str, compute_func, ttl: int):
        # Try to get from cache
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Compute result
        result = await compute_func()
        
        # Store in cache
        await self.redis.setex(key, ttl, json.dumps(result))
        
        return result
```

## 5. Auth Service コンポーネント

### 5.1 概要

認証・認可を管理し、JWT発行、セッション管理、権限制御を担当します。

### 5.2 実装

```go
package auth

type AuthService struct {
    db           *sql.DB
    redis        *redis.Client
    jwtSecret    []byte
    bcryptCost   int
    tokenExpiry  time.Duration
    refreshExpiry time.Duration
}

type User struct {
    ID           uuid.UUID
    Email        string
    PasswordHash string
    Role         string
    OrgID        uuid.UUID
    CreatedAt    time.Time
    UpdatedAt    time.Time
}

type TokenPair struct {
    AccessToken  string
    RefreshToken string
    ExpiresAt    int64
}

func (s *AuthService) Authenticate(email, password string) (*TokenPair, error) {
    // Fetch user from database
    user, err := s.getUserByEmail(email)
    if err != nil {
        return nil, ErrInvalidCredentials
    }
    
    // Verify password
    if err := bcrypt.CompareHashAndPassword(
        []byte(user.PasswordHash),
        []byte(password),
    ); err != nil {
        return nil, ErrInvalidCredentials
    }
    
    // Generate tokens
    return s.generateTokenPair(user)
}

func (s *AuthService) generateTokenPair(user *User) (*TokenPair, error) {
    // Create access token claims
    accessClaims := jwt.MapClaims{
        "sub":    user.ID.String(),
        "email":  user.Email,
        "role":   user.Role,
        "org_id": user.OrgID.String(),
        "exp":    time.Now().Add(s.tokenExpiry).Unix(),
        "iat":    time.Now().Unix(),
    }
    
    // Generate access token
    accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, accessClaims)
    accessTokenString, err := accessToken.SignedString(s.jwtSecret)
    if err != nil {
        return nil, err
    }
    
    // Create refresh token
    refreshClaims := jwt.MapClaims{
        "sub": user.ID.String(),
        "exp": time.Now().Add(s.refreshExpiry).Unix(),
        "iat": time.Now().Unix(),
    }
    
    refreshToken := jwt.NewWithClaims(jwt.SigningMethodHS256, refreshClaims)
    refreshTokenString, err := refreshToken.SignedString(s.jwtSecret)
    if err != nil {
        return nil, err
    }
    
    // Store session in Redis
    sessionKey := fmt.Sprintf("session:%s", user.ID.String())
    sessionData := map[string]interface{}{
        "user_id":       user.ID.String(),
        "access_token":  accessTokenString,
        "refresh_token": refreshTokenString,
        "created_at":    time.Now().Unix(),
    }
    
    err = s.redis.HSet(context.Background(), sessionKey, sessionData).Err()
    if err != nil {
        return nil, err
    }
    
    s.redis.Expire(context.Background(), sessionKey, s.refreshExpiry)
    
    return &TokenPair{
        AccessToken:  accessTokenString,
        RefreshToken: refreshTokenString,
        ExpiresAt:    time.Now().Add(s.tokenExpiry).Unix(),
    }, nil
}
```

### 5.3 権限管理

```go
type Permission string

const (
    PermissionRead   Permission = "read"
    PermissionWrite  Permission = "write"
    PermissionDelete Permission = "delete"
    PermissionAdmin  Permission = "admin"
)

type Role struct {
    Name        string
    Permissions []Permission
}

var RoleDefinitions = map[string]Role{
    "super_admin": {
        Name: "super_admin",
        Permissions: []Permission{
            PermissionRead, PermissionWrite, PermissionDelete, PermissionAdmin,
        },
    },
    "org_admin": {
        Name: "org_admin",
        Permissions: []Permission{
            PermissionRead, PermissionWrite, PermissionDelete,
        },
    },
    "member": {
        Name: "member",
        Permissions: []Permission{
            PermissionRead, PermissionWrite,
        },
    },
    "guest": {
        Name: "guest",
        Permissions: []Permission{
            PermissionRead,
        },
    },
}

func (s *AuthService) CheckPermission(userRole string, required Permission) bool {
    role, exists := RoleDefinitions[userRole]
    if !exists {
        return false
    }
    
    for _, perm := range role.Permissions {
        if perm == required {
            return true
        }
    }
    
    return false
}
```

## 6. Analytics Service コンポーネント

### 6.1 概要

使用状況の追跡、統計情報の集計、レポート生成を担当します。

### 6.2 実装

```go
package analytics

type AnalyticsService struct {
    db            *sql.DB
    clickhouse    *clickhouse.Conn
    aggregator    *Aggregator
    reportBuilder *ReportBuilder
}

type Event struct {
    ID        uuid.UUID
    Type      string
    UserID    uuid.UUID
    OrgID     uuid.UUID
    Metadata  map[string]interface{}
    Timestamp time.Time
}

func (s *AnalyticsService) TrackEvent(event Event) error {
    // Store in ClickHouse for real-time analytics
    query := `
        INSERT INTO events (id, type, user_id, org_id, metadata, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    `
    
    metadataJSON, _ := json.Marshal(event.Metadata)
    
    return s.clickhouse.Exec(context.Background(), query,
        event.ID,
        event.Type,
        event.UserID,
        event.OrgID,
        string(metadataJSON),
        event.Timestamp,
    )
}

func (s *AnalyticsService) GetUsageStats(orgID uuid.UUID, period string) (*UsageStats, error) {
    query := `
        SELECT
            toDate(timestamp) as date,
            type,
            count() as count,
            avg(JSONExtractFloat(metadata, 'processing_time')) as avg_time,
            quantile(0.95)(JSONExtractFloat(metadata, 'processing_time')) as p95_time
        FROM events
        WHERE org_id = ?
            AND timestamp >= now() - INTERVAL ? DAY
        GROUP BY date, type
        ORDER BY date DESC
    `
    
    days := s.parsePeriod(period)
    rows, err := s.clickhouse.Query(context.Background(), query, orgID, days)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    stats := &UsageStats{
        OrgID:  orgID,
        Period: period,
        Data:   make([]DailyStats, 0),
    }
    
    for rows.Next() {
        var daily DailyStats
        err := rows.Scan(&daily.Date, &daily.Type, &daily.Count, &daily.AvgTime, &daily.P95Time)
        if err != nil {
            return nil, err
        }
        stats.Data = append(stats.Data, daily)
    }
    
    return stats, nil
}
```

## 7. Notification Service コンポーネント

### 7.1 概要

各種通知（メール、Slack、Teams等）の配信を管理します。

### 7.2 実装

```go
package notification

type NotificationService struct {
    emailClient   EmailClient
    slackClient   SlackClient
    teamsClient   TeamsClient
    templateEngine *TemplateEngine
    queue         *MessageQueue
}

type Notification struct {
    ID         uuid.UUID
    Type       string
    Recipients []Recipient
    Template   string
    Data       map[string]interface{}
    Priority   Priority
    ScheduleAt *time.Time
}

type Recipient struct {
    UserID  uuid.UUID
    Channel string
    Address string
}

func (s *NotificationService) Send(notification Notification) error {
    // Queue for processing
    if notification.ScheduleAt != nil && notification.ScheduleAt.After(time.Now()) {
        return s.queue.ScheduleAt(notification, *notification.ScheduleAt)
    }
    
    // Process immediately
    return s.processNotification(notification)
}

func (s *NotificationService) processNotification(n Notification) error {
    // Render template
    content, err := s.templateEngine.Render(n.Template, n.Data)
    if err != nil {
        return err
    }
    
    // Send to each recipient
    var errors []error
    for _, recipient := range n.Recipients {
        err := s.sendToChannel(recipient, content)
        if err != nil {
            errors = append(errors, err)
        }
    }
    
    if len(errors) > 0 {
        return fmt.Errorf("failed to send to %d recipients", len(errors))
    }
    
    return nil
}

func (s *NotificationService) sendToChannel(recipient Recipient, content string) error {
    switch recipient.Channel {
    case "email":
        return s.emailClient.Send(recipient.Address, content)
    case "slack":
        return s.slackClient.Send(recipient.Address, content)
    case "teams":
        return s.teamsClient.Send(recipient.Address, content)
    default:
        return fmt.Errorf("unsupported channel: %s", recipient.Channel)
    }
}
```

## 8. Web Frontend コンポーネント

### 8.1 概要

ReactベースのSPAとして実装され、ユーザー向けのインターフェースを提供します。

### 8.2 アーキテクチャ

```typescript
// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Components
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Transform from './pages/Transform';
import History from './pages/History';
import Settings from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/transform" element={<Transform />} />
                <Route path="/history" element={<History />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </BrowserRouter>
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

### 8.3 状態管理

```typescript
// src/store/transformStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface TransformState {
  text: string;
  transformationType: string;
  targetTone: string;
  intensity: number;
  isLoading: boolean;
  result: TransformResult | null;
  history: TransformResult[];
  
  // Actions
  setText: (text: string) => void;
  setTransformationType: (type: string) => void;
  setTargetTone: (tone: string) => void;
  setIntensity: (intensity: number) => void;
  transform: () => Promise<void>;
  clearResult: () => void;
}

const useTransformStore = create<TransformState>()(
  devtools(
    persist(
      (set, get) => ({
        text: '',
        transformationType: 'tone',
        targetTone: 'warm',
        intensity: 2,
        isLoading: false,
        result: null,
        history: [],
        
        setText: (text) => set({ text }),
        setTransformationType: (type) => set({ transformationType: type }),
        setTargetTone: (tone) => set({ targetTone: tone }),
        setIntensity: (intensity) => set({ intensity }),
        
        transform: async () => {
          set({ isLoading: true });
          
          try {
            const response = await api.transform({
              text: get().text,
              transformation_type: get().transformationType,
              target_tone: get().targetTone,
              intensity: get().intensity,
            });
            
            set({
              result: response.data,
              history: [response.data, ...get().history].slice(0, 10),
              isLoading: false,
            });
          } catch (error) {
            set({ isLoading: false });
            throw error;
          }
        },
        
        clearResult: () => set({ result: null }),
      }),
      {
        name: 'transform-storage',
        partialize: (state) => ({ history: state.history }),
      }
    )
  )
);
```

### 8.4 API クライアント

```typescript
// src/services/api.ts
import axios, { AxiosInstance } from 'axios';
import { getAuthToken, refreshAuthToken } from '../utils/auth';

class APIClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1',
      timeout: 30000,
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const newToken = await refreshAuthToken();
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  // API methods
  async transform(data: TransformRequest): Promise<TransformResponse> {
    return this.client.post('/transform', data);
  }
  
  async getHistory(params?: HistoryParams): Promise<HistoryResponse> {
    return this.client.get('/history', { params });
  }
  
  async getAnalytics(period: string): Promise<AnalyticsResponse> {
    return this.client.get('/analytics', { params: { period } });
  }
}

export default new APIClient();
```

## 9. コンポーネント間通信

### 9.1 同期通信

```go
// HTTP/REST通信
type ServiceClient struct {
    baseURL string
    client  *http.Client
    timeout time.Duration
}

func (c *ServiceClient) Call(method, path string, body interface{}) (interface{}, error) {
    url := c.baseURL + path
    
    var reqBody io.Reader
    if body != nil {
        jsonBody, err := json.Marshal(body)
        if err != nil {
            return nil, err
        }
        reqBody = bytes.NewBuffer(jsonBody)
    }
    
    req, err := http.NewRequest(method, url, reqBody)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-Trace-ID", generateTraceID())
    
    ctx, cancel := context.WithTimeout(context.Background(), c.timeout)
    defer cancel()
    
    resp, err := c.client.Do(req.WithContext(ctx))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("service returned status %d", resp.StatusCode)
    }
    
    var result interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}
```

### 9.2 非同期通信

```go
// Message Queue通信
type MessageBus struct {
    redis      *redis.Client
    handlers   map[string]MessageHandler
    workerPool *WorkerPool
}

type Message struct {
    ID        string
    Type      string
    Payload   interface{}
    Timestamp time.Time
    TraceID   string
}

type MessageHandler func(context.Context, Message) error

func (mb *MessageBus) Publish(ctx context.Context, topic string, message Message) error {
    data, err := json.Marshal(message)
    if err != nil {
        return err
    }
    
    return mb.redis.Publish(ctx, topic, data).Err()
}

func (mb *MessageBus) Subscribe(topic string, handler MessageHandler) {
    mb.handlers[topic] = handler
    
    go func() {
        pubsub := mb.redis.Subscribe(context.Background(), topic)
        defer pubsub.Close()
        
        for msg := range pubsub.Channel() {
            var message Message
            if err := json.Unmarshal([]byte(msg.Payload), &message); err != nil {
                log.Printf("Failed to unmarshal message: %v", err)
                continue
            }
            
            mb.workerPool.Submit(func() {
                ctx := context.WithValue(context.Background(), "trace_id", message.TraceID)
                if err := handler(ctx, message); err != nil {
                    log.Printf("Handler error: %v", err)
                }
            })
        }
    }()
}
```

## 10. 監視とデバッグ

### 10.1 ヘルスチェック

```go
type HealthChecker struct {
    checks []HealthCheck
}

type HealthCheck struct {
    Name    string
    Check   func() error
    Timeout time.Duration
}

func (hc *HealthChecker) CheckAll() HealthStatus {
    status := HealthStatus{
        Status: "healthy",
        Checks: make([]CheckResult, 0),
    }
    
    for _, check := range hc.checks {
        result := CheckResult{
            Name:   check.Name,
            Status: "healthy",
        }
        
        ctx, cancel := context.WithTimeout(context.Background(), check.Timeout)
        defer cancel()
        
        done := make(chan error, 1)
        go func() {
            done <- check.Check()
        }()
        
        select {
        case err := <-done:
            if err != nil {
                result.Status = "unhealthy"
                result.Error = err.Error()
                status.Status = "unhealthy"
            }
        case <-ctx.Done():
            result.Status = "timeout"
            result.Error = "health check timed out"
            status.Status = "degraded"
        }
        
        status.Checks = append(status.Checks, result)
    }
    
    return status
}
```

### 10.2 メトリクス収集

```go
type MetricsCollector struct {
    prometheus *prometheus.Registry
    counters   map[string]prometheus.Counter
    histograms map[string]prometheus.Histogram
    gauges     map[string]prometheus.Gauge
}

func (mc *MetricsCollector) RecordRequest(path string, method string, status int, duration time.Duration) {
    mc.counters["requests_total"].Inc()
    mc.histograms["request_duration"].Observe(duration.Seconds())
    
    labels := prometheus.Labels{
        "path":   path,
        "method": method,
        "status": fmt.Sprint(status),
    }
    
    mc.counters["requests_by_endpoint"].With(labels).Inc()
}
```

## まとめ

ToneBridgeのコンポーネント設計は、マイクロサービスアーキテクチャの原則に従い、各コンポーネントが単一責任を持ち、疎結合で設計されています。これにより、独立したデプロイメント、スケーリング、保守が可能となり、システム全体の柔軟性と信頼性が向上します。
