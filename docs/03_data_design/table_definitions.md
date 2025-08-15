# テーブル定義書

## 1. 概要

ToneBridgeシステムのデータベーステーブル定義を記載します。PostgreSQL 16を使用し、マルチテナント対応、ベクトル検索機能を含む設計となっています。

## 2. テーブル一覧

| テーブル名 | 説明 | パーティション |
|-----------|------|----------------|
| `organizations` | 組織情報 | なし |
| `users` | ユーザー情報 | なし |
| `api_keys` | APIキー管理 | なし |
| `transformations` | 変換履歴 | 月次パーティション |
| `transformation_cache` | 変換結果キャッシュ | なし |
| `dictionaries` | 用語辞書 | なし |
| `analytics` | 分析データ | 日次パーティション |
| `embeddings` | ベクトル埋め込み | なし |
| `subscriptions` | サブスクリプション情報 | なし |
| `usage_tracking` | 使用量追跡 | 月次パーティション |
| `audit_logs` | 監査ログ | 月次パーティション |

## 3. テーブル定義詳細

### 3.1 organizations

組織（企業）情報を管理するテーブル。

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    settings JSONB DEFAULT '{}',
    usage_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- インデックス
CREATE INDEX idx_organizations_domain ON organizations(domain);
CREATE INDEX idx_organizations_plan ON organizations(plan);
CREATE INDEX idx_organizations_deleted_at ON organizations(deleted_at);
```

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | 組織ID |
| name | VARCHAR(255) | NO | - | 組織名 |
| domain | VARCHAR(255) | YES | - | メールドメイン |
| plan | VARCHAR(50) | NO | 'free' | プラン（free, standard, pro, enterprise） |
| settings | JSONB | YES | '{}' | 組織設定 |
| usage_limit | INTEGER | YES | 1000 | 月間使用量上限 |
| created_at | TIMESTAMP WITH TIME ZONE | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | NOW() | 更新日時 |
| deleted_at | TIMESTAMP WITH TIME ZONE | YES | - | 削除日時（論理削除） |

### 3.2 users

ユーザー情報を管理するテーブル。

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    preferences JSONB DEFAULT '{}',
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
```

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | ユーザーID |
| organization_id | UUID | YES | - | 所属組織ID |
| email | VARCHAR(255) | NO | - | メールアドレス |
| password_hash | VARCHAR(255) | NO | - | パスワードハッシュ |
| name | VARCHAR(255) | YES | - | ユーザー名 |
| role | VARCHAR(50) | YES | 'member' | ロール（admin, manager, member） |
| preferences | JSONB | YES | '{}' | ユーザー設定 |
| last_login_at | TIMESTAMP WITH TIME ZONE | YES | - | 最終ログイン日時 |
| created_at | TIMESTAMP WITH TIME ZONE | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | NOW() | 更新日時 |
| deleted_at | TIMESTAMP WITH TIME ZONE | YES | - | 削除日時（論理削除） |

### 3.3 api_keys

APIキー管理テーブル。

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    permissions JSONB DEFAULT '{}',
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);
```

### 3.4 transformations

テキスト変換履歴テーブル（パーティション対応）。

```sql
CREATE TABLE transformations (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    original_text TEXT NOT NULL,
    transformed_text TEXT NOT NULL,
    transformation_type VARCHAR(50) NOT NULL,
    target_tone VARCHAR(50),
    intensity_level INTEGER CHECK (intensity_level BETWEEN 1 AND 3),
    metadata JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 月次パーティションの作成例
CREATE TABLE transformations_2024_01 PARTITION OF transformations
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE transformations_2024_02 PARTITION OF transformations
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- インデックス
CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_organization_id ON transformations(organization_id);
CREATE INDEX idx_transformations_type ON transformations(transformation_type);
CREATE INDEX idx_transformations_created_at ON transformations(created_at);
```

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | 変換ID |
| user_id | UUID | YES | - | ユーザーID |
| organization_id | UUID | YES | - | 組織ID |
| original_text | TEXT | NO | - | 元のテキスト |
| transformed_text | TEXT | NO | - | 変換後のテキスト |
| transformation_type | VARCHAR(50) | NO | - | 変換タイプ |
| target_tone | VARCHAR(50) | YES | - | 目標トーン |
| intensity_level | INTEGER | YES | - | 変換強度（1-3） |
| metadata | JSONB | YES | '{}' | メタデータ |
| processing_time_ms | INTEGER | YES | - | 処理時間（ミリ秒） |
| model_used | VARCHAR(100) | YES | - | 使用モデル |
| created_at | TIMESTAMP WITH TIME ZONE | NO | NOW() | 作成日時 |

### 3.5 dictionaries

用語辞書テーブル。

```sql
CREATE TABLE dictionaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    technical_term VARCHAR(255) NOT NULL,
    business_term VARCHAR(255) NOT NULL,
    explanation TEXT,
    category VARCHAR(50) DEFAULT 'general',
    examples TEXT[],
    usage_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT unique_term_per_org UNIQUE (organization_id, technical_term)
);

-- インデックス
CREATE INDEX idx_dictionaries_organization_id ON dictionaries(organization_id);
CREATE INDEX idx_dictionaries_technical_term ON dictionaries(technical_term);
CREATE INDEX idx_dictionaries_category ON dictionaries(category);
-- 全文検索用インデックス
CREATE INDEX idx_dictionaries_search ON dictionaries 
    USING gin(to_tsvector('japanese', technical_term || ' ' || business_term || ' ' || COALESCE(explanation, '')));
```

### 3.6 analytics

分析データテーブル（パーティション対応）。

```sql
CREATE TABLE analytics (
    id UUID DEFAULT gen_random_uuid(),
    transformation_id UUID,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    tone_score FLOAT,
    clarity_score FLOAT,
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 日次パーティションの作成例
CREATE TABLE analytics_2024_01_15 PARTITION OF analytics
    FOR VALUES FROM ('2024-01-15') TO ('2024-01-16');

-- インデックス
CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_organization_id ON analytics(organization_id);
CREATE INDEX idx_analytics_event_type ON analytics(event_type);
CREATE INDEX idx_analytics_created_at ON analytics(created_at);
```

### 3.7 embeddings

ベクトル埋め込みテーブル（pgvector使用）。

```sql
-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_id UUID,
    text_hash VARCHAR(64) NOT NULL,
    embedding vector(1536) NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ベクトル検索用インデックス（IVFFlat）
CREATE INDEX embeddings_vector_idx ON embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ハッシュインデックス
CREATE INDEX idx_embeddings_text_hash ON embeddings(text_hash);
```

### 3.8 subscriptions

サブスクリプション情報テーブル。

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    trial_end TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_subscriptions_organization_id ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

### 3.9 usage_tracking

使用量追跡テーブル（パーティション対応）。

```sql
CREATE TABLE usage_tracking (
    id UUID DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    resource_type VARCHAR(100) NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    usage_date DATE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, usage_date)
) PARTITION BY RANGE (usage_date);

-- 月次パーティションの作成例
CREATE TABLE usage_tracking_2024_01 PARTITION OF usage_tracking
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- インデックス
CREATE INDEX idx_usage_tracking_organization_id ON usage_tracking(organization_id);
CREATE INDEX idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX idx_usage_tracking_resource_type ON usage_tracking(resource_type);
CREATE INDEX idx_usage_tracking_usage_date ON usage_tracking(usage_date);

-- 複合インデックス（集計クエリ用）
CREATE INDEX idx_usage_tracking_org_date ON usage_tracking(organization_id, usage_date);
```

### 3.10 audit_logs

監査ログテーブル（パーティション対応）。

```sql
CREATE TABLE audit_logs (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    organization_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 月次パーティションの作成例
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- インデックス
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## 4. パーティション管理

### 4.1 自動パーティション作成

```sql
-- パーティション自動作成関数
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
    table_name text;
BEGIN
    -- 今月と来月のパーティションを作成
    FOR i IN 0..1 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' month')::interval);
        end_date := start_date + '1 month'::interval;
        
        -- transformationsテーブル
        partition_name := 'transformations_' || to_char(start_date, 'YYYY_MM');
        IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF transformations FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date);
        END IF;
        
        -- usage_trackingテーブル
        partition_name := 'usage_tracking_' || to_char(start_date, 'YYYY_MM');
        IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF usage_tracking FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date);
        END IF;
        
        -- audit_logsテーブル
        partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
            EXECUTE format('CREATE TABLE %I PARTITION OF audit_logs FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 毎月1日に実行するジョブをスケジュール（pg_cronを使用）
SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT create_monthly_partitions();');
```

### 4.2 古いパーティションの削除

```sql
-- 古いパーティションを削除する関数
CREATE OR REPLACE FUNCTION drop_old_partitions(months_to_keep integer DEFAULT 12)
RETURNS void AS $$
DECLARE
    cutoff_date date;
    partition_name text;
BEGIN
    cutoff_date := date_trunc('month', CURRENT_DATE - (months_to_keep || ' months')::interval);
    
    -- 古いパーティションを削除
    FOR partition_name IN 
        SELECT tablename FROM pg_tables 
        WHERE tablename ~ '^(transformations|usage_tracking|audit_logs|analytics)_\d{4}_\d{2}$'
        AND tablename < 'transformations_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', partition_name);
        RAISE NOTICE 'Dropped partition: %', partition_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 毎月15日に実行するジョブをスケジュール
SELECT cron.schedule('drop-old-partitions', '0 2 15 * *', 'SELECT drop_old_partitions(12);');
```

## 5. インデックス戦略

### 5.1 主要インデックス

- **主キーインデックス**: 全テーブルに自動作成
- **外部キーインデックス**: リレーション検索の高速化
- **業務キーインデックス**: email、domain等の頻繁に検索される項目
- **部分インデックス**: 論理削除されていないレコード用
- **複合インデックス**: 複数カラムを使った検索の最適化

### 5.2 パフォーマンス最適化

```sql
-- 論理削除されていないレコード用の部分インデックス
CREATE INDEX idx_users_active ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_active ON organizations(domain) WHERE deleted_at IS NULL;

-- 複合インデックス（よく使われるクエリパターン用）
CREATE INDEX idx_transformations_user_type ON transformations(user_id, transformation_type, created_at);
CREATE INDEX idx_analytics_org_event ON analytics(organization_id, event_type, created_at);

-- BRIN インデックス（時系列データ用）
CREATE INDEX idx_transformations_created_brin ON transformations USING brin(created_at);
CREATE INDEX idx_analytics_created_brin ON analytics USING brin(created_at);
```

## 6. データ保持ポリシー

| テーブル | 保持期間 | アーカイブ戦略 |
|---------|---------|---------------|
| transformations | 12ヶ月 | S3へアーカイブ後削除 |
| analytics | 24ヶ月 | データウェアハウスへ移行 |
| audit_logs | 36ヶ月 | コンプライアンス要件により長期保存 |
| usage_tracking | 12ヶ月 | 月次集計後に詳細削除 |

## 7. バックアップ戦略

### 7.1 バックアップスケジュール

- **フルバックアップ**: 毎日午前2時
- **増分バックアップ**: 1時間ごと
- **トランザクションログ**: リアルタイム（ストリーミングレプリケーション）

### 7.2 リストア手順

```bash
# ポイントインタイムリカバリ
pg_restore -d tonebridge_db -t "2024-01-15 10:30:00" backup.dump

# 特定テーブルのリストア
pg_restore -d tonebridge_db -t users -t organizations backup.dump
```

## 8. セキュリティ考慮事項

### 8.1 アクセス制御

```sql
-- 読み取り専用ロール
CREATE ROLE readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- アプリケーションロール
CREATE ROLE app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT DELETE ON transformations, analytics TO app_user;

-- 管理者ロール
CREATE ROLE admin_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_user;
```

### 8.2 データ暗号化

- **保存時暗号化**: Transparent Data Encryption (TDE) 使用
- **転送時暗号化**: SSL/TLS必須
- **機密データ**: pgcrypto拡張を使用した暗号化

```sql
-- pgcrypto拡張の有効化
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- パスワードハッシュ化の例
UPDATE users SET password_hash = crypt('plain_password', gen_salt('bf'));
```

## 9. モニタリング

### 9.1 監視対象メトリクス

```sql
-- テーブルサイズ監視
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- インデックス使用状況
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- スロークエリ監視
SELECT 
    query,
    calls,
    total_time,
    mean,
    max
FROM pg_stat_statements
WHERE mean > 100  -- 100ms以上
ORDER BY mean DESC
LIMIT 20;
```

### 9.2 アラート設定

- **ディスク使用率**: 80%超過時
- **接続数**: 最大接続数の90%超過時
- **レプリケーション遅延**: 10秒以上
- **デッドロック**: 1時間に5回以上

### 3.11 auto_transform_rules

自動変換ルールテーブル。

```sql
CREATE TABLE auto_transform_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_pattern TEXT NOT NULL,
    transformation_type VARCHAR(50) NOT NULL,
    target_tone VARCHAR(50),
    intensity_level INTEGER CHECK (intensity_level BETWEEN 1 AND 3),
    active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    conditions JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_auto_transform_rules_organization_id ON auto_transform_rules(organization_id);
CREATE INDEX idx_auto_transform_rules_active ON auto_transform_rules(active);
CREATE INDEX idx_auto_transform_rules_priority ON auto_transform_rules(priority);
```

### 3.12 webhooks

Webhook設定テーブル。

```sql
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    headers JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 3,
    timeout_ms INTEGER DEFAULT 30000,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_webhooks_organization_id ON webhooks(organization_id);
CREATE INDEX idx_webhooks_active ON webhooks(active);
CREATE INDEX idx_webhooks_events ON webhooks USING gin(events);
```

### 3.13 integrations

外部サービス統合設定テーブル。

```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    service_type VARCHAR(50) NOT NULL, -- slack, teams, discord, outlook
    config JSONB NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    webhook_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT unique_service_per_org UNIQUE (organization_id, service_type)
);

-- インデックス
CREATE INDEX idx_integrations_organization_id ON integrations(organization_id);
CREATE INDEX idx_integrations_service_type ON integrations(service_type);
CREATE INDEX idx_integrations_active ON integrations(active);
```

### 3.14 notification_settings

通知設定テーブル。

```sql
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL, -- email, slack, teams, in_app
    enabled BOOLEAN DEFAULT TRUE,
    frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, hourly, daily, weekly
    conditions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT unique_notification_per_user UNIQUE (user_id, notification_type, channel)
);

-- インデックス
CREATE INDEX idx_notification_settings_user_id ON notification_settings(user_id);
CREATE INDEX idx_notification_settings_organization_id ON notification_settings(organization_id);
CREATE INDEX idx_notification_settings_enabled ON notification_settings(enabled);
```

### 3.15 teams

チーム管理テーブル。

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- チームメンバー中間テーブル
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_team FOREIGN KEY (team_id) 
        REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT unique_team_member UNIQUE (team_id, user_id)
);

-- インデックス
CREATE INDEX idx_teams_organization_id ON teams(organization_id);
CREATE INDEX idx_teams_deleted_at ON teams(deleted_at);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
```

### 3.16 ml_models

MLモデル管理テーブル。

```sql
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'training', -- training, ready, failed, archived
    config JSONB DEFAULT '{}',
    training_data JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    model_path TEXT,
    trained_by UUID REFERENCES users(id),
    training_started_at TIMESTAMP WITH TIME ZONE,
    training_completed_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_ml_models_organization_id ON ml_models(organization_id);
CREATE INDEX idx_ml_models_status ON ml_models(status);
CREATE INDEX idx_ml_models_model_type ON ml_models(model_type);
```

### 3.17 feedback

ユーザーフィードバックテーブル。

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transformation_id UUID,
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_type VARCHAR(50) NOT NULL, -- quality, accuracy, tone, usefulness
    comment TEXT,
    original_text TEXT,
    transformed_text TEXT,
    suggested_text TEXT,
    is_helpful BOOLEAN,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_organization FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_organization_id ON feedback(organization_id);
CREATE INDEX idx_feedback_transformation_id ON feedback(transformation_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_feedback_processed ON feedback(processed);
```

### 3.18 sessions

セッション管理テーブル。

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

## 10. 移行計画

### 10.1 初期データ投入

```sql
-- 初期マスタデータ投入
INSERT INTO organizations (name, plan) VALUES 
    ('デモ組織', 'free'),
    ('テスト企業', 'standard');

-- デフォルト辞書データ
INSERT INTO dictionaries (technical_term, business_term, category) VALUES
    ('PR', 'プルリクエスト', 'technical'),
    ('CI/CD', '継続的インテグレーション/デリバリー', 'technical'),
    ('API', 'アプリケーションプログラミングインターフェース', 'technical');
```

### 10.2 データ移行スクリプト

```bash
#!/bin/bash
# データ移行スクリプト

# 旧システムからエクスポート
pg_dump -h old_host -U old_user -d old_db > old_data.sql

# 新システムへインポート
psql -h new_host -U new_user -d tonebridge_db < old_data.sql

# データ変換処理
psql -h new_host -U new_user -d tonebridge_db -f data_transformation.sql
```