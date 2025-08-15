# API仕様書

## 概要

ToneBridge APIは、エンジニアと非エンジニア間のコミュニケーションギャップを解消するためのRESTful APIです。本仕様書では、各エンドポイントの詳細、リクエスト/レスポンス形式、認証方法について説明します。

## ベースURL

```
開発環境: http://localhost:8082/api/v1
本番環境: https://api.tonebridge.io/v1
```

## 認証

### JWT認証

すべてのAPIエンドポイント（認証関連とプレビューを除く）はJWT認証が必要です。

```http
Authorization: Bearer <jwt_token>
```

### APIキー認証（SDK用）

SDKクライアント向けの代替認証方法。

```http
X-API-Key: <api_key>
```

## エンドポイント一覧

### 認証関連

#### POST /auth/register
新規ユーザー登録

**Request:**
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "name": "山田太郎",
  "organization": "株式会社Example"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1704067200
  }
}
```

#### POST /auth/login
ユーザーログイン

**Request:**
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1704067200
  }
}
```

#### POST /auth/refresh
トークンリフレッシュ

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1704067200
  }
}
```

### 変換関連

#### POST /transform
テキスト変換

**Request:**
```json
{
  "text": "バグを修正したPRをマージしてください。CIが通っているので問題ないはずです。",
  "transformation_type": "tone",
  "target_tone": "warm",
  "intensity_level": 2,
  "options": {
    "preserve_technical_terms": true,
    "add_context": true
  }
}
```

**Parameters:**
- `text` (string, required): 変換対象のテキスト（最大10,000文字）
- `transformation_type` (string, required): 変換タイプ
  - `tone`: 文体変換
  - `structure`: 構造化
  - `summarize`: 要約
  - `terminology`: 専門用語変換
- `target_tone` (string, optional): 目標トーン（toneタイプの場合必須）
  - `warm`: 温かみのある（配慮型）
  - `professional`: プロフェッショナル
  - `casual`: カジュアル
  - `technical`: 技術的
  - `executive`: エグゼクティブ向け
- `intensity_level` (integer, optional): 変換強度（1-3、デフォルト: 2）
  - `1`: 軽微な調整
  - `2`: 標準的な変換
  - `3`: 大幅な変換
- `options` (object, optional): 追加オプション

**Response:**
```json
{
  "success": true,
  "data": {
    "original_text": "バグを修正したPRをマージしてください。CIが通っているので問題ないはずです。",
    "transformed_text": "バグ修正のプルリクエストをご確認いただけますでしょうか。自動テストも全て通過していますので、お手すきの際にマージしていただければ幸いです。",
    "suggestions": [
      "締め切りがある場合は明記すると良いでしょう",
      "修正内容の簡単な説明を追加すると理解しやすくなります"
    ],
    "metadata": {
      "processing_time_ms": 234,
      "confidence_score": 0.92,
      "model_used": "gpt-4-turbo"
    }
  }
}
```

#### POST /analyze
テキスト分析

**Request:**
```json
{
  "text": "至急！本番環境でメモリリークが発生しています。すぐに対応が必要です。"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tone": "urgent",
    "clarity": 0.85,
    "priority": "critical",
    "structure": {
      "has_action_item": true,
      "has_deadline": false,
      "is_structured": true,
      "paragraph_count": 1,
      "sentence_count": 2
    },
    "suggestions": [
      "影響範囲を明記すると良いでしょう",
      "対応期限を具体的に示すことを推奨します",
      "エラーの詳細や発生条件を追加してください"
    ],
    "terms_found": [
      {
        "term": "メモリリーク",
        "category": "technical",
        "difficulty_level": "high",
        "suggested_explanation": "メモリが解放されずに蓄積される問題"
      }
    ]
  }
}
```

#### GET /history
変換履歴取得

**Query Parameters:**
- `page` (integer, optional): ページ番号（デフォルト: 1）
- `limit` (integer, optional): 1ページあたりの件数（デフォルト: 20、最大: 100）
- `transformation_type` (string, optional): フィルタリング用の変換タイプ
- `from_date` (string, optional): 開始日（ISO 8601形式）
- `to_date` (string, optional): 終了日（ISO 8601形式）

**Response:**
```json
{
  "success": true,
  "data": {
    "transformations": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "original_text": "バグを修正しました",
        "transformed_text": "バグの修正が完了いたしました",
        "transformation_type": "tone",
        "target_tone": "professional",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_pages": 5,
      "total_items": 97
    }
  }
}
```

### 辞書管理

#### GET /dictionaries
辞書エントリ一覧取得

**Query Parameters:**
- `category` (string, optional): カテゴリーフィルター（technical, business, general）
- `search` (string, optional): 検索キーワード

**Response:**
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "technical_term": "PR",
        "business_term": "プルリクエスト",
        "explanation": "コードレビューのためのマージ前の変更提案",
        "category": "technical",
        "examples": [
          "PRを作成してレビューを依頼する",
          "このPRはまだレビュー中です"
        ]
      }
    ]
  }
}
```

#### POST /dictionaries
辞書エントリ作成

**Request:**
```json
{
  "technical_term": "CI/CD",
  "business_term": "継続的インテグレーション/デリバリー",
  "explanation": "コードの自動テストとデプロイメントのプロセス",
  "category": "technical",
  "examples": [
    "CI/CDパイプラインが正常に動作しています",
    "CI/CDの設定を更新しました"
  ]
}
```

#### PUT /dictionaries/:id
辞書エントリ更新

#### DELETE /dictionaries/:id
辞書エントリ削除

### プレビューモード（認証不要）

#### GET /preview/info
プレビューモード情報取得

**Response:**
```json
{
  "success": true,
  "preview_mode": {
    "enabled": true,
    "limitations": {
      "max_characters": 500,
      "rate_limit_per_minute": 3,
      "rate_limit_per_day": 10,
      "available_transformations": ["tone"]
    }
  },
  "signup_url": "/api/v1/auth/register",
  "try_now": {
    "sample_texts": [
      "このタスクを今すぐやってください。期限は明日です。",
      "バグがあるので修正が必要です。優先度は高いです。"
    ]
  }
}
```

#### POST /preview/transform
プレビュー版テキスト変換

**Request:**
```json
{
  "text": "今すぐ対応してください",
  "target_tone": "warm",
  "intensity_level": 2
}
```

**Response:**
```json
{
  "success": true,
  "preview_mode": true,
  "limitations": {
    "max_characters": 500,
    "rate_limit": "3 requests per minute",
    "daily_limit": "10 requests per day"
  },
  "data": {
    "original_text": "今すぐ対応してください",
    "transformed_text": "お手数ですが、早めにご対応いただけますでしょうか",
    "suggestions": [
      "期限を明記するとより親切です"
    ]
  },
  "message": "This is a preview. Sign up for unlimited access!"
}
```

### WebSocket接続

#### WSS /ws
リアルタイム変換用WebSocket接続

**接続時の認証:**
```javascript
const ws = new WebSocket('wss://api.tonebridge.io/ws', {
  headers: {
    'Authorization': 'Bearer <jwt_token>'
  }
});
```

**メッセージフォーマット:**
```json
{
  "type": "transform",
  "payload": {
    "text": "リアルタイムで変換するテキスト",
    "transformation_type": "tone",
    "target_tone": "warm",
    "intensity_level": 2
  }
}
```

**レスポンス:**
```json
{
  "type": "transform_result",
  "payload": {
    "transformed_text": "変換されたテキスト",
    "processing_time_ms": 45
  }
}
```

## エラー処理

### エラーレスポンス形式

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please wait 30 seconds.",
    "details": {
      "retry_after": 30,
      "limit": 100,
      "remaining": 0
    }
  }
}
```

### エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|---------------|------|
| `UNAUTHORIZED` | 401 | 認証が必要 |
| `FORBIDDEN` | 403 | アクセス権限なし |
| `NOT_FOUND` | 404 | リソースが見つからない |
| `VALIDATION_ERROR` | 400 | リクエストパラメータが不正 |
| `RATE_LIMIT_EXCEEDED` | 429 | レート制限超過 |
| `INTERNAL_ERROR` | 500 | サーバー内部エラー |
| `SERVICE_UNAVAILABLE` | 503 | サービス一時利用不可 |

## レート制限

### 制限値

| プラン | 1分あたり | 1時間あたり | 1日あたり |
|--------|-----------|-------------|-----------|
| プレビュー | 3 | 50 | 10 |
| 無料 | 10 | 100 | 500 |
| スタンダード | 60 | 1,000 | 10,000 |
| プロ | 300 | 5,000 | 50,000 |
| エンタープライズ | 無制限 | 無制限 | 無制限 |

### レスポンスヘッダー

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704067200
```

## バージョニング

APIバージョンはURLパスに含まれます（例：`/api/v1/`）。新バージョンがリリースされても、既存バージョンは最低6ヶ月間サポートされます。

### 非推奨通知

非推奨となるエンドポイントやパラメータは、レスポンスヘッダーで通知されます：

```http
X-Deprecated: true
X-Sunset-Date: 2024-12-31
```

## SDKサポート

公式SDKは以下の言語で提供されています：

- JavaScript/TypeScript: `npm install @tonebridge/sdk`
- Python: `pip install tonebridge`
- Go: `go get github.com/tonebridge/go-sdk`

各SDKの詳細な使用方法については、[SDK_GUIDE.md](../SDK_GUIDE.md)を参照してください。