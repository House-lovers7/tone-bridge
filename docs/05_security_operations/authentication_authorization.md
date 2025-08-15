# 認証・認可仕様書

## 1. 概要

ToneBridgeの認証・認可システムは、セキュアなユーザー認証とリソースへのアクセス制御を提供します。JWT（JSON Web Token）ベースの認証と、ロールベースアクセス制御（RBAC）を採用しています。

## 2. 認証アーキテクチャ

### 2.1 認証フロー

```
┌──────────┐     ┌────────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────>│  Gateway   │────>│   Auth   │────>│    DB    │
│          │<────│            │<────│  Service │<────│          │
└──────────┘     └────────────┘     └──────────┘     └──────────┘
     │                  │                  │
     │  1. Login        │  2. Validate     │  3. Verify
     │  Request         │     Credentials  │     User
     │                  │                  │
     │  6. JWT Token    │  5. Generate     │  4. User
     │<─────────────────│<─────────────────│     Valid
```

### 2.2 JWT構成

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "org_id": "123e4567-e89b-12d3-a456-426614174000",
    "role": "member",
    "iat": 1704067200,
    "exp": 1704070800,
    "jti": "unique-token-id"
  }
}
```

## 3. 認証方式

### 3.1 パスワード認証

#### パスワード要件
- 最小8文字、最大128文字
- 大文字・小文字・数字・特殊文字のうち3種類以上を含む
- 一般的な弱いパスワードのブラックリストチェック
- パスワード履歴チェック（過去5回分）

#### ハッシュ化
```go
// bcryptを使用したパスワードハッシュ化
import "golang.org/x/crypto/bcrypt"

func HashPassword(password string) (string, error) {
    // コスト係数14を使用（2^14回のイテレーション）
    hashedPassword, err := bcrypt.GenerateFromPassword(
        []byte(password), 
        14,
    )
    return string(hashedPassword), err
}
```

### 3.2 APIキー認証

#### APIキー生成
```go
type APIKey struct {
    ID           uuid.UUID
    KeyHash      string
    Name         string
    Permissions  []string
    ExpiresAt    *time.Time
    LastUsedAt   *time.Time
}

func GenerateAPIKey() (string, error) {
    // 32バイトのランダムキー生成
    bytes := make([]byte, 32)
    if _, err := rand.Read(bytes); err != nil {
        return "", err
    }
    
    // Base64エンコード
    apiKey := base64.URLEncoding.EncodeToString(bytes)
    
    // プレフィックスを追加
    return fmt.Sprintf("tb_%s", apiKey), nil
}
```

### 3.3 OAuth 2.0（計画中）

将来的に以下のプロバイダーをサポート予定：
- Google
- GitHub
- Microsoft (Azure AD)
- Okta

## 4. 認可システム

### 4.1 ロールベースアクセス制御（RBAC）

#### ロール定義

| ロール | 説明 | 権限レベル |
|--------|------|-----------|
| `super_admin` | システム管理者 | すべての操作が可能 |
| `org_admin` | 組織管理者 | 組織内のすべての操作が可能 |
| `manager` | マネージャー | チームメンバーの管理、統計閲覧 |
| `member` | 一般メンバー | 自身のリソースの操作のみ |
| `guest` | ゲスト | 読み取り専用 |

#### 権限マトリックス

| リソース/操作 | super_admin | org_admin | manager | member | guest |
|--------------|-------------|-----------|---------|---------|--------|
| 変換実行 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 履歴閲覧（自分） | ✓ | ✓ | ✓ | ✓ | ✓ |
| 履歴閲覧（他人） | ✓ | ✓ | ✓ | - | - |
| 辞書編集 | ✓ | ✓ | ✓ | - | - |
| ユーザー管理 | ✓ | ✓ | ✓ | - | - |
| 組織設定変更 | ✓ | ✓ | - | - | - |
| 請求情報管理 | ✓ | ✓ | - | - | - |
| システム設定 | ✓ | - | - | - | - |

### 4.2 アクセス制御実装

```go
// ミドルウェアでの認可チェック
func RequireRole(allowedRoles ...string) fiber.Handler {
    return func(c *fiber.Ctx) error {
        user := c.Locals("user").(*models.User)
        
        for _, role := range allowedRoles {
            if user.Role == role {
                return c.Next()
            }
        }
        
        return c.Status(403).JSON(fiber.Map{
            "error": "Insufficient permissions",
        })
    }
}

// エンドポイントでの使用例
app.Post("/api/v1/admin/users", 
    AuthMiddleware(),
    RequireRole("super_admin", "org_admin"),
    handlers.CreateUser,
)
```

## 5. セッション管理

### 5.1 JWT管理

#### トークン寿命
- アクセストークン: 1時間
- リフレッシュトークン: 7日間
- Remember Me有効時: 30日間

#### トークンローテーション
```go
type TokenPair struct {
    AccessToken  string
    RefreshToken string
    ExpiresAt    int64
}

func RotateTokens(refreshToken string) (*TokenPair, error) {
    // リフレッシュトークンの検証
    claims, err := ValidateRefreshToken(refreshToken)
    if err != nil {
        return nil, err
    }
    
    // 既存のリフレッシュトークンを無効化
    InvalidateToken(refreshToken)
    
    // 新しいトークンペアを生成
    return GenerateTokenPair(claims.UserID)
}
```

### 5.2 セッション無効化

#### ログアウト処理
```go
func Logout(c *fiber.Ctx) error {
    token := ExtractToken(c)
    
    // トークンをブラックリストに追加
    err := AddToBlacklist(token, time.Hour)
    if err != nil {
        return err
    }
    
    // Redisからセッション削除
    err = DeleteSession(token)
    
    return c.JSON(fiber.Map{
        "message": "Successfully logged out",
    })
}
```

## 6. セキュリティ対策

### 6.1 ブルートフォース攻撃対策

```go
type LoginAttempt struct {
    IP       string
    Email    string
    Attempts int
    LastTry  time.Time
}

func CheckLoginAttempts(email, ip string) error {
    key := fmt.Sprintf("login_attempts:%s:%s", email, ip)
    
    attempts, err := redis.Get(key)
    if attempts > 5 {
        return errors.New("Too many login attempts. Please try again later.")
    }
    
    // 失敗時はカウントを増やす
    redis.Incr(key)
    redis.Expire(key, 15*time.Minute)
    
    return nil
}
```

### 6.2 CSRF対策

```go
func GenerateCSRFToken(sessionID string) string {
    data := fmt.Sprintf("%s:%d", sessionID, time.Now().Unix())
    hash := sha256.Sum256([]byte(data))
    return hex.EncodeToString(hash[:])
}

func ValidateCSRFToken(token, sessionID string) bool {
    // Double Submit Cookie パターン
    expectedToken := GenerateCSRFToken(sessionID)
    return subtle.ConstantTimeCompare(
        []byte(token), 
        []byte(expectedToken),
    ) == 1
}
```

### 6.3 セキュリティヘッダー

```go
func SecurityHeaders() fiber.Handler {
    return func(c *fiber.Ctx) error {
        c.Set("X-Content-Type-Options", "nosniff")
        c.Set("X-Frame-Options", "DENY")
        c.Set("X-XSS-Protection", "1; mode=block")
        c.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        c.Set("Content-Security-Policy", "default-src 'self'")
        return c.Next()
    }
}
```

## 7. 監査ログ

### 7.1 記録対象イベント

- ログイン成功/失敗
- パスワード変更
- 権限変更
- APIキー生成/削除
- セキュリティ設定変更

### 7.2 ログフォーマット

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "login_success",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "metadata": {
    "auth_method": "password",
    "mfa_used": false
  }
}
```

## 8. Multi-Factor Authentication (MFA)

### 8.1 TOTP実装

```go
import "github.com/pquerna/otp/totp"

func GenerateTOTPSecret(email string) (*otp.Key, error) {
    key, err := totp.Generate(totp.GenerateOpts{
        Issuer:      "ToneBridge",
        AccountName: email,
        Algorithm:   otp.AlgorithmSHA256,
    })
    return key, err
}

func VerifyTOTP(secret, code string) bool {
    return totp.Validate(code, secret)
}
```

### 8.2 バックアップコード

- 10個の8文字英数字コード生成
- 各コードは1回のみ使用可能
- 暗号化してデータベースに保存

## 9. 権限昇格の防止

### 9.1 最小権限の原則

```go
func GetUserPermissions(userID string) []string {
    // デフォルトは最小権限
    permissions := []string{"read:own", "write:own"}
    
    // ロールに基づいて権限を追加
    role := GetUserRole(userID)
    switch role {
    case "manager":
        permissions = append(permissions, "read:team", "write:team")
    case "org_admin":
        permissions = append(permissions, "read:org", "write:org", "admin:org")
    }
    
    return permissions
}
```

## 10. コンプライアンス

### 10.1 GDPR対応

- ユーザーデータの暗号化
- データポータビリティ（エクスポート機能）
- 忘れられる権利（完全削除機能）
- 明示的な同意取得

### 10.2 SOC2準拠

- アクセスログの90日以上保存
- 定期的なセキュリティ監査
- インシデント対応手順の文書化
- 従業員のセキュリティトレーニング

## 11. ベストプラクティス

### 11.1 開発者向けガイドライン

1. **認証情報の取り扱い**
   - 認証情報をログに出力しない
   - エラーメッセージで詳細な情報を漏らさない
   - タイミング攻撃を防ぐため、一定時間で応答

2. **トークン管理**
   - トークンをLocalStorageではなくhttpOnlyクッキーに保存
   - XSS攻撃を防ぐためサニタイゼーション徹底
   - 定期的なトークンローテーション

3. **パスワード管理**
   - パスワードリセットリンクは1回限り有効
   - リセットトークンの有効期限は30分
   - パスワード変更時は全セッション無効化

### 11.2 運用ガイドライン

1. **定期レビュー**
   - 月次でアクセスログのレビュー
   - 四半期ごとの権限棚卸し
   - 年次セキュリティ監査

2. **インシデント対応**
   - 不正アクセス検知時の自動アラート
   - 該当アカウントの即時停止
   - 影響範囲の調査と報告

## まとめ

ToneBridgeの認証・認可システムは、業界標準のセキュリティプラクティスに従い、ユーザーデータの保護とシステムの安全性を確保しています。継続的な改善により、新たな脅威にも対応していきます。
