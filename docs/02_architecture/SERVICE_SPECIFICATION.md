# サービス仕様書

## 概要

ToneBridgeシステムを構成する各サービスの詳細仕様とエンドポイント、データフローを定義します。

---

## サービス一覧

### 1. API Gateway Service

**概要**: すべてのクライアントリクエストのエントリーポイント

**技術スタック**:
- 言語: Go 1.21+
- フレームワーク: Fiber v2
- ポート: 8082 (外部), 8080 (内部)

**責務**:
- リクエストルーティング
- 認証・認可
- レート制限
- キャッシング（L2: Redis）
- エラーハンドリング
- ロギング・メトリクス収集

**主要エンドポイント**:

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /health | ヘルスチェック | 不要 |
| GET | /ready | レディネスチェック | 不要 |
| POST | /api/v1/auth/register | ユーザー登録 | 不要 |
| POST | /api/v1/auth/login | ログイン | 不要 |
| POST | /api/v1/auth/refresh | トークンリフレッシュ | 不要 |
| GET | /api/v1/preview/info | プレビュー情報 | 不要 |
| POST | /api/v1/preview/transform | プレビュー変換 | 不要 |
| POST | /api/v1/transform | メッセージ変換 | JWT |
| POST | /api/v1/analyze | メッセージ分析 | JWT |
| GET | /api/v1/history | 変換履歴 | JWT |
| GET | /api/v1/dictionaries | 辞書一覧 | JWT |
| POST | /api/v1/dictionaries | 辞書作成 | JWT |
| PUT | /api/v1/dictionaries/:id | 辞書更新 | JWT |
| DELETE | /api/v1/dictionaries/:id | 辞書削除 | JWT |
| GET | /api/v1/profile | プロフィール取得 | JWT |
| PUT | /api/v1/profile | プロフィール更新 | JWT |

**設定ファイル**:
```go
// services/gateway/internal/config/config.go
type Config struct {
    Port           string   // デフォルト: "8080"
    DatabaseURL    string   // PostgreSQL接続文字列
    RedisAddr      string   // Redis接続アドレス
    LLMServiceURL  string   // LLMサービスURL
    JWTSecret      string   // JWT署名キー
    AllowedOrigins []string // CORS許可オリジン
    LogLevel       string   // ログレベル
    Environment    string   // 実行環境
}
```

---

### 2. LLM Service

**概要**: AI駆動のテキスト変換処理を実行

**技術スタック**:
- 言語: Python 3.11+
- フレームワーク: FastAPI
- ライブラリ: LangChain, OpenAI, Anthropic
- ポート: 8003 (外部), 8000 (内部)

**責務**:
- テキスト変換処理
- プロンプト管理
- LLMプロバイダー統合
- 変換結果のキャッシング

**変換タイプ**:

| タイプ | 説明 | プロンプト例 |
|--------|------|------------|
| soften | 柔らかい表現への変換 | "Please rephrase this message in a softer, more diplomatic tone" |
| clarify | 明確化・曖昧さの除去 | "Please clarify and remove ambiguity from this message" |
| structure | 構造化・整理 | "Please structure this message with clear points and organization" |
| summarize | 要約 | "Please summarize the key points of this message" |
| terminology | 専門用語の翻訳 | "Please translate technical terms to business-friendly language" |
| requirements | 要件整理 | "Please extract and organize requirements from this message" |
| background | 背景情報の補完 | "Please add relevant context and background information" |

**内部API**:

```python
# services/llm/app/api/transform.py
@router.post("/transform")
async def transform_message(request: TransformRequest):
    """
    テキスト変換エンドポイント
    
    Parameters:
    - text: 変換対象テキスト
    - transformation_type: 変換タイプ
    - intensity_level: 変換強度 (1-3)
    - options: 追加オプション
    """
    
@router.post("/analyze")
async def analyze_message(request: AnalyzeRequest):
    """
    テキスト分析エンドポイント
    
    Parameters:
    - text: 分析対象テキスト
    - analysis_type: 分析タイプ
    """
```

---

### 3. WebSocket Server

**概要**: リアルタイム双方向通信を提供

**技術スタック**:
- 言語: TypeScript/Node.js 18+
- フレームワーク: Socket.IO 4.x
- ポート: 3001

**責務**:
- WebSocket接続管理
- リアルタイムメッセージ配信
- チャンネル管理
- イベントブロードキャスト

**イベント一覧**:

| イベント名 | 方向 | 説明 | ペイロード |
|-----------|------|------|------------|
| connection | Server←Client | 接続確立 | - |
| disconnect | Server←Client | 接続切断 | - |
| join_channel | Server←Client | チャンネル参加 | `{channel_id: string}` |
| leave_channel | Server←Client | チャンネル退出 | `{channel_id: string}` |
| transform | Server←Client | 変換リクエスト | `{text: string, type: string}` |
| transform_result | Server→Client | 変換結果 | `{original: string, transformed: string}` |
| analyze | Server←Client | 分析リクエスト | `{text: string}` |
| analyze_result | Server→Client | 分析結果 | `{text: string, analysis: object}` |
| error | Server→Client | エラー通知 | `{code: string, message: string}` |

**クライアント接続例**:
```javascript
const socket = io('ws://localhost:3001', {
    auth: {
        token: 'JWT_TOKEN'
    }
});

socket.on('connect', () => {
    console.log('Connected');
    socket.emit('join_channel', { channel_id: 'team-123' });
});

socket.on('transform_result', (data) => {
    console.log('Transformed:', data);
});
```

---

### 4. ML Training Service

**概要**: カスタムモデルのトレーニングとファインチューニング

**技術スタック**:
- 言語: Python 3.11+
- フレームワーク: FastAPI
- ライブラリ: PyTorch, Transformers

**責務**:
- モデルトレーニング
- ファインチューニング
- 評価メトリクス計算
- モデル管理

**エンドポイント**:

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /train | トレーニングジョブ開始 |
| GET | /jobs/:id | ジョブステータス取得 |
| GET | /models | モデル一覧 |
| POST | /evaluate | モデル評価 |
| POST | /deploy | モデルデプロイ |

---

### 5. Auto-Transform Service

**概要**: ルールベースの自動変換処理

**技術スタック**:
- 言語: Python 3.11+
- フレームワーク: FastAPI

**責務**:
- 自動変換ルール管理
- パターンマッチング
- バッチ処理
- スケジューリング

**ルールエンジン仕様**:

```python
class TransformRule:
    """
    自動変換ルール定義
    """
    id: str
    name: str
    description: str
    pattern: str  # 正規表現パターン
    transformation_type: str
    priority: int
    conditions: List[Condition]
    actions: List[Action]
    enabled: bool
```

---

## データフロー

### 1. 同期変換フロー

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Cache
    participant LLM
    participant DB

    Client->>Gateway: POST /api/v1/transform
    Gateway->>Gateway: JWT検証
    Gateway->>Cache: キャッシュ確認
    alt キャッシュヒット
        Cache-->>Gateway: キャッシュ結果
        Gateway-->>Client: 200 OK (cached)
    else キャッシュミス
        Gateway->>LLM: 変換リクエスト
        LLM->>LLM: 変換処理
        LLM-->>Gateway: 変換結果
        Gateway->>Cache: キャッシュ保存
        Gateway->>DB: 履歴保存
        Gateway-->>Client: 200 OK
    end
```

### 2. リアルタイム変換フロー

```mermaid
sequenceDiagram
    participant Client
    participant WebSocket
    participant Redis
    participant Gateway
    participant LLM

    Client->>WebSocket: connect()
    WebSocket->>WebSocket: 認証確認
    Client->>WebSocket: emit('transform')
    WebSocket->>Gateway: HTTP POST /transform
    Gateway->>LLM: 変換処理
    LLM-->>Gateway: 結果
    Gateway-->>WebSocket: 結果
    WebSocket->>Redis: Pub/Sub配信
    WebSocket-->>Client: emit('transform_result')
    Note over Redis: 他の接続クライアントにも配信
```

### 3. バッチ処理フロー

```mermaid
flowchart LR
    A[スケジューラー] -->|定期実行| B[Auto-Transform]
    B --> C{ルール評価}
    C -->|マッチ| D[変換キュー]
    C -->|非マッチ| E[スキップ]
    D --> F[LLM Service]
    F --> G[結果保存]
    G --> H[通知送信]
```

---

## サービス間通信

### 通信プロトコル

| サービス間 | プロトコル | 形式 | 認証 |
|-----------|-----------|------|------|
| Client → Gateway | HTTP/HTTPS | JSON | JWT/API Key |
| Gateway → LLM | HTTP | JSON | Internal Token |
| Gateway → Database | PostgreSQL | Binary | User/Pass |
| Gateway → Redis | Redis Protocol | Binary | Password |
| WebSocket → Redis | Redis Pub/Sub | Binary | Password |
| Services → Services | HTTP | JSON | Service Token |

### サービスディスカバリー

**開発環境**:
- Docker Composeのサービス名を使用
- 例: `http://llm:8000`, `redis:6379`

**本番環境**:
- Kubernetes Service
- Service Mesh (Istio)
- 環境変数による設定

---

## エラーハンドリング

### エラーコード体系

| コード範囲 | カテゴリ | 例 |
|-----------|---------|-----|
| 1000-1999 | 認証・認可 | 1001: Invalid Token |
| 2000-2999 | 検証エラー | 2001: Invalid Input |
| 3000-3999 | ビジネスロジック | 3001: Quota Exceeded |
| 4000-4999 | 外部サービス | 4001: LLM Service Error |
| 5000-5999 | システムエラー | 5001: Database Error |

### エラーレスポンス形式

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {
            "field": "specific_field",
            "reason": "validation_failed"
        }
    },
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req_abc123",
        "trace_id": "trace_xyz789"
    }
}
```

---

## セキュリティ

### 認証方式

| 方式 | 用途 | 有効期限 |
|------|------|---------|
| JWT | ユーザー認証 | 1時間 |
| Refresh Token | トークン更新 | 7日 |
| API Key | SDK/統合 | 無期限 |
| Service Token | サービス間通信 | 1時間 |

### レート制限

| エンドポイント | 制限 | ウィンドウ |
|---------------|------|-----------|
| /api/v1/preview/* | 3 req | 1分 |
| /api/v1/preview/* | 10 req | 1日 |
| /api/v1/transform | 100 req | 1分 |
| /api/v1/analyze | 50 req | 1分 |
| その他 | 1000 req | 1分 |

---

## モニタリング・ロギング

### メトリクス

**収集メトリクス**:
- リクエスト数
- レスポンス時間
- エラー率
- キャッシュヒット率
- 同時接続数
- CPU/メモリ使用率

**ダッシュボード**:
- Prometheus + Grafana（計画中）
- カスタムダッシュボード

### ログ形式

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "gateway",
    "trace_id": "trace_xyz789",
    "span_id": "span_123",
    "user_id": "user_456",
    "message": "Request processed",
    "duration_ms": 45,
    "status_code": 200
}
```

---

## デプロイメント

### コンテナイメージ

| サービス | イメージ | サイズ |
|---------|---------|--------|
| Gateway | tonebridge/gateway:latest | ~50MB |
| LLM | tonebridge/llm:latest | ~2GB |
| WebSocket | tonebridge/websocket:latest | ~150MB |
| ML Training | tonebridge/ml-training:latest | ~3GB |

### 環境変数

**必須環境変数**:
```bash
# Database
DATABASE_URL=postgres://user:pass@host:port/db
REDIS_ADDR=redis:6379

# Security
JWT_SECRET=your-secret-key

# Services
LLM_SERVICE_URL=http://llm:8000

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 参考資料

- [API リファレンス](../API_REFERENCE.md)
- [アーキテクチャ概要](../ARCHITECTURE.md)
- [実装ステータス](../IMPLEMENTATION_STATUS.md)
- [開発者ガイド](../DEVELOPER_GUIDE.md)