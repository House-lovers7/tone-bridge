# API リファレンスガイド

## 1. 概要

ToneBridge API は RESTful API として設計されており、JSON形式でデータをやり取りします。

### ベースURL
```
Production: https://api.tonebridge.io/api/v1
Staging: https://staging-api.tonebridge.io/api/v1
Development: http://localhost:8082/api/v1
```

### 認証方式
- Bearer Token (JWT)
- API Key (特定のエンドポイント)

### レスポンス形式
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### エラーレスポンス
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## 2. 認証 API

### 2.1 ユーザー登録

**エンドポイント:** `POST /auth/register`

**リクエスト:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "山田太郎",
  "organization_name": "株式会社Example"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "山田太郎",
      "role": "member",
      "organization_id": "660e8400-e29b-41d4-a716-446655440001"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "expires_at": "2024-01-15T11:30:00Z"
    }
  }
}
```

**エラーコード:**
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| USER_EXISTS | ユーザーが既に存在 | 409 |
| INVALID_EMAIL | メールアドレス形式が不正 | 400 |
| WEAK_PASSWORD | パスワードが要件を満たさない | 400 |

### 2.2 ログイン

**エンドポイント:** `POST /auth/login`

**リクエスト:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "山田太郎",
      "role": "member",
      "organization_id": "660e8400-e29b-41d4-a716-446655440001"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
      "expires_at": "2024-01-15T11:30:00Z"
    }
  }
}
```

### 2.3 トークンリフレッシュ

**エンドポイント:** `POST /auth/refresh`

**リクエスト:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2024-01-15T11:30:00Z"
  }
}
```

### 2.4 ログアウト

**エンドポイント:** `POST /auth/logout`

**ヘッダー:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "message": "Successfully logged out"
  }
}
```

## 3. 変換 API

### 3.1 テキスト変換

**エンドポイント:** `POST /transform`

**ヘッダー:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

**リクエスト:**
```json
{
  "text": "このプロジェクトは絶対に失敗する！何を考えているんだ！",
  "transformation_type": "tone",
  "target_tone": "warm",
  "intensity_level": 2,
  "options": {
    "preserve_technical_terms": true,
    "maintain_formality": false
  }
}
```

**パラメータ説明:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| text | string | ✓ | 変換対象のテキスト（最大10,000文字） |
| transformation_type | string | ✓ | 変換タイプ: `tone`, `structure`, `summarize`, `terminology` |
| target_tone | string | ○ | 目標トーン（tone変換時必須）: `warm`, `professional`, `casual`, `formal` |
| intensity_level | integer | ○ | 変換強度（1-3、デフォルト: 2） |
| options | object | ✗ | 追加オプション |

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "transformation_id": "trans_xyz789",
    "original_text": "このプロジェクトは絶対に失敗する！何を考えているんだ！",
    "transformed_text": "このプロジェクトには改善の余地があるかもしれません。一緒に検討してみましょう。",
    "transformation_type": "tone",
    "target_tone": "warm",
    "intensity_level": 2,
    "confidence_score": 0.92,
    "processing_time_ms": 1250,
    "model_used": "gpt-4-turbo",
    "cached": false,
    "metadata": {
      "original_sentiment": "negative",
      "transformed_sentiment": "neutral",
      "tone_shift": "aggressive_to_collaborative"
    }
  }
}
```

### 3.2 バッチ変換

**エンドポイント:** `POST /transform/batch`

**リクエスト:**
```json
{
  "transformations": [
    {
      "text": "テキスト1",
      "transformation_type": "tone",
      "target_tone": "warm"
    },
    {
      "text": "テキスト2",
      "transformation_type": "summarize"
    }
  ]
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "transformations": [
      {
        "index": 0,
        "success": true,
        "transformation_id": "trans_001",
        "transformed_text": "変換後テキスト1"
      },
      {
        "index": 1,
        "success": true,
        "transformation_id": "trans_002",
        "transformed_text": "要約されたテキスト2"
      }
    ],
    "total": 2,
    "successful": 2,
    "failed": 0
  }
}
```

### 3.3 変換履歴取得

**エンドポイント:** `GET /transform/history`

**クエリパラメータ:**
```
?page=1&limit=20&from=2024-01-01&to=2024-01-31&type=tone
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "transformations": [
      {
        "transformation_id": "trans_xyz789",
        "original_text": "元のテキスト",
        "transformed_text": "変換後のテキスト",
        "transformation_type": "tone",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

## 4. 分析 API

### 4.1 テキスト分析

**エンドポイント:** `POST /analyze`

**リクエスト:**
```json
{
  "text": "分析対象のテキスト",
  "analysis_types": ["tone", "structure", "complexity"]
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "analysis_id": "analysis_abc123",
    "tone_analysis": {
      "primary_tone": "assertive",
      "secondary_tones": ["urgent", "critical"],
      "sentiment": "negative",
      "confidence": 0.88
    },
    "structure_analysis": {
      "paragraph_count": 3,
      "sentence_count": 12,
      "average_sentence_length": 15.5,
      "structure_score": 7.2
    },
    "complexity_analysis": {
      "readability_score": 65,
      "technical_term_count": 8,
      "jargon_density": 0.12,
      "suggested_simplifications": 3
    }
  }
}
```

### 4.2 対比分析

**エンドポイント:** `POST /analyze/compare`

**リクエスト:**
```json
{
  "original_text": "元のテキスト",
  "transformed_text": "変換後のテキスト"
}
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_xyz456",
    "tone_shift": {
      "from": "aggressive",
      "to": "collaborative",
      "shift_magnitude": 0.75
    },
    "sentiment_change": {
      "from": -0.8,
      "to": 0.3,
      "improvement": 1.1
    },
    "readability_change": {
      "from": 45,
      "to": 72,
      "improvement_percentage": 60
    },
    "preserved_information": 0.95,
    "semantic_similarity": 0.88
  }
}
```

## 5. 辞書 API

### 5.1 辞書一覧取得

**エンドポイント:** `GET /dictionaries`

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "dictionaries": [
      {
        "id": "dict_001",
        "name": "技術用語辞書",
        "description": "IT関連の専門用語",
        "entry_count": 1250,
        "language": "ja",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 5.2 辞書作成

**エンドポイント:** `POST /dictionaries`

**リクエスト:**
```json
{
  "name": "社内用語辞書",
  "description": "自社特有の用語集",
  "language": "ja",
  "entries": [
    {
      "term": "KPI",
      "definition": "重要業績評価指標",
      "alternatives": ["主要指標", "パフォーマンス指標"],
      "context": "ビジネス"
    }
  ]
}
```

### 5.3 辞書エントリ追加

**エンドポイント:** `POST /dictionaries/{dictionary_id}/entries`

**リクエスト:**
```json
{
  "entries": [
    {
      "term": "デプロイ",
      "definition": "本番環境への展開",
      "alternatives": ["リリース", "展開"],
      "context": "開発"
    }
  ]
}
```

## 6. 組織管理 API

### 6.1 組織情報取得

**エンドポイント:** `GET /organization`

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "org_123",
      "name": "株式会社Example",
      "plan": "enterprise",
      "member_count": 25,
      "usage": {
        "transformations_this_month": 15420,
        "transformations_limit": 50000,
        "storage_used_gb": 2.5,
        "storage_limit_gb": 100
      },
      "settings": {
        "default_tone": "professional",
        "auto_save": true,
        "team_sharing": true
      }
    }
  }
}
```

### 6.2 メンバー管理

**エンドポイント:** `GET /organization/members`

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "id": "user_001",
        "email": "admin@example.com",
        "name": "管理者",
        "role": "admin",
        "joined_at": "2024-01-01T00:00:00Z",
        "last_active": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 6.3 メンバー招待

**エンドポイント:** `POST /organization/invite`

**リクエスト:**
```json
{
  "email": "newuser@example.com",
  "role": "member",
  "message": "チームに参加してください"
}
```

## 7. 統計 API

### 7.1 使用統計取得

**エンドポイント:** `GET /analytics/usage`

**クエリパラメータ:**
```
?period=month&from=2024-01-01&to=2024-01-31
```

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-01-31T23:59:59Z"
    },
    "usage": {
      "total_transformations": 5420,
      "by_type": {
        "tone": 3200,
        "structure": 1100,
        "summarize": 820,
        "terminology": 300
      },
      "by_day": [
        {
          "date": "2024-01-15",
          "count": 245
        }
      ],
      "average_processing_time_ms": 1850,
      "cache_hit_rate": 0.35,
      "error_rate": 0.002
    }
  }
}
```

### 7.2 品質メトリクス

**エンドポイント:** `GET /analytics/quality`

**レスポンス:**
```json
{
  "success": true,
  "data": {
    "quality_metrics": {
      "average_confidence_score": 0.89,
      "user_satisfaction_rate": 0.94,
      "transformation_accuracy": 0.91,
      "tone_consistency": 0.88,
      "information_preservation": 0.96
    },
    "feedback_summary": {
      "total_feedback": 1250,
      "positive": 1175,
      "neutral": 50,
      "negative": 25
    }
  }
}
```

## 8. Webhook API

### 8.1 Webhook登録

**エンドポイント:** `POST /webhooks`

**リクエスト:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["transformation.completed", "transformation.failed"],
  "secret": "webhook_secret_key",
  "active": true
}
```

### 8.2 Webhookイベント

**イベントペイロード例:**
```json
{
  "event": "transformation.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "transformation_id": "trans_xyz789",
    "user_id": "user_123",
    "organization_id": "org_456",
    "transformation_type": "tone",
    "success": true
  },
  "signature": "sha256=abcdef..."
}
```

**イベントタイプ:**
- `transformation.completed`
- `transformation.failed`
- `user.registered`
- `user.upgraded`
- `quota.exceeded`
- `dictionary.updated`

## 9. エラーコード一覧

### 認証関連
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| UNAUTHORIZED | 認証が必要 | 401 |
| INVALID_TOKEN | トークンが無効 | 401 |
| TOKEN_EXPIRED | トークンの有効期限切れ | 401 |
| INSUFFICIENT_PERMISSIONS | 権限不足 | 403 |

### リクエスト関連
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| INVALID_REQUEST | リクエスト形式が不正 | 400 |
| VALIDATION_ERROR | バリデーションエラー | 400 |
| MISSING_PARAMETER | 必須パラメータ不足 | 400 |
| INVALID_PARAMETER | パラメータ値が不正 | 400 |

### リソース関連
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| NOT_FOUND | リソースが見つからない | 404 |
| ALREADY_EXISTS | リソースが既に存在 | 409 |
| CONFLICT | リソースの競合 | 409 |

### レート制限
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| RATE_LIMITED | レート制限超過 | 429 |
| QUOTA_EXCEEDED | 使用量制限超過 | 429 |

### サーバーエラー
| コード | 説明 | HTTPステータス |
|--------|------|---------------|
| INTERNAL_ERROR | 内部エラー | 500 |
| SERVICE_UNAVAILABLE | サービス利用不可 | 503 |
| TIMEOUT | タイムアウト | 504 |

## 10. レート制限

### 制限値

| プラン | リクエスト/分 | リクエスト/日 | 同時接続数 |
|--------|-------------|--------------|-----------|
| Free | 10 | 100 | 1 |
| Starter | 60 | 5,000 | 5 |
| Professional | 300 | 50,000 | 20 |
| Enterprise | 1,000 | 無制限 | 100 |

### レート制限ヘッダー

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642435200
X-RateLimit-Reset-After: 30
```

## 11. SDK サンプル

### JavaScript/TypeScript

```typescript
import { ToneBridgeClient } from '@tonebridge/sdk';

const client = new ToneBridgeClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.tonebridge.io'
});

// テキスト変換
const result = await client.transform({
  text: '変換したいテキスト',
  transformationType: 'tone',
  targetTone: 'warm',
  intensityLevel: 2
});

console.log(result.transformedText);
```

### Python

```python
from tonebridge import ToneBridgeClient

client = ToneBridgeClient(
    api_key='your-api-key',
    base_url='https://api.tonebridge.io'
)

# テキスト変換
result = client.transform(
    text='変換したいテキスト',
    transformation_type='tone',
    target_tone='warm',
    intensity_level=2
)

print(result.transformed_text)
```

### Go

```go
import "github.com/tonebridge/go-sdk"

client := tonebridge.NewClient(
    tonebridge.WithAPIKey("your-api-key"),
    tonebridge.WithBaseURL("https://api.tonebridge.io"),
)

result, err := client.Transform(ctx, &tonebridge.TransformRequest{
    Text:               "変換したいテキスト",
    TransformationType: "tone",
    TargetTone:        "warm",
    IntensityLevel:    2,
})

if err != nil {
    log.Fatal(err)
}

fmt.Println(result.TransformedText)
```

## 12. 変更履歴

### v1.2.0 (2024-01-15)
- バッチ変換APIを追加
- Webhook機能を追加
- 辞書管理APIを拡張

### v1.1.0 (2023-12-01)
- 分析APIを追加
- レート制限を調整
- エラーレスポンスを改善

### v1.0.0 (2023-10-01)
- 初回リリース
- 基本的な変換API
- 認証システム

## サポート

APIに関する質問やサポートが必要な場合：

- **ドキュメント**: https://docs.tonebridge.io
- **サポート**: api-support@tonebridge.io
- **ステータスページ**: https://status.tonebridge.io
- **コミュニティ**: https://community.tonebridge.io