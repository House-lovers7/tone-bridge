# バックアップ・リカバリ仕様書

## 1. 概要

ToneBridgeシステムのバックアップとディザスタリカバリ戦略を定義します。本仕様書では、データ保護、バックアップ手順、リカバリ手順、および事業継続計画について説明します。

## 2. バックアップ戦略

### 2.1 バックアップ対象

| 対象 | 種類 | 重要度 | バックアップ頻度 | 保持期間 |
|------|------|--------|-----------------|----------|
| PostgreSQLデータベース | フル/増分 | Critical | 日次/1時間ごと | 30日/7日 |
| Redis データ | スナップショット | High | 1時間ごと | 7日 |
| アプリケーションコード | Git リポジトリ | Critical | リアルタイム | 無期限 |
| 環境設定ファイル | ファイル | High | 日次 | 30日 |
| ログファイル | アーカイブ | Medium | 日次 | 90日 |
| ユーザーアップロードファイル | オブジェクトストレージ | High | リアルタイム | 無期限 |

### 2.2 バックアップアーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Primary   │────>│   Backup    │────>│   Archive   │
│   Storage   │     │   Storage   │     │   Storage   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                    │
       │ Real-time         │ Daily             │ Monthly
       │ Replication       │ Snapshot          │ Archive
       │                   │                    │
       ▼                   ▼                    ▼
  Hot Standby         S3 Standard          S3 Glacier
```

## 3. PostgreSQLバックアップ

### 3.1 物理バックアップ（pg_basebackup）

#### フルバックアップスクリプト
```bash
#!/bin/bash
# PostgreSQL Full Backup Script

BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="fullbackup_${DATE}"

# バックアップ実行
pg_basebackup \
    -h localhost \
    -p 5432 \
    -U backup_user \
    -D "${BACKUP_DIR}/${BACKUP_NAME}" \
    -Ft \
    -z \
    -P \
    -X stream

# 圧縮とアーカイブ
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    -C "${BACKUP_DIR}" \
    "${BACKUP_NAME}"

# S3へアップロード
aws s3 cp \
    "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    "s3://tonebridge-backups/postgresql/${BACKUP_NAME}.tar.gz" \
    --storage-class STANDARD_IA

# ローカルの古いバックアップを削除（7日以上）
find ${BACKUP_DIR} -name "fullbackup_*.tar.gz" -mtime +7 -delete

# バックアップ成功通知
curl -X POST ${SLACK_WEBHOOK_URL} \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"PostgreSQL full backup completed: ${BACKUP_NAME}\"}"
```

### 3.2 論理バックアップ（pg_dump）

```bash
#!/bin/bash
# PostgreSQL Logical Backup Script

DB_NAME="tonebridge_db"
BACKUP_DIR="/backup/postgresql/logical"
DATE=$(date +%Y%m%d_%H%M%S)

# カスタムフォーマットでバックアップ
pg_dump \
    -h localhost \
    -U backup_user \
    -d ${DB_NAME} \
    -Fc \
    -f "${BACKUP_DIR}/logical_${DATE}.dump"

# 特定テーブルのみバックアップ（高頻度更新テーブル）
TABLES="transformations analytics usage_tracking"
for TABLE in ${TABLES}; do
    pg_dump \
        -h localhost \
        -U backup_user \
        -d ${DB_NAME} \
        -t ${TABLE} \
        -Fc \
        -f "${BACKUP_DIR}/${TABLE}_${DATE}.dump"
done
```

### 3.3 継続的アーカイブログ（WAL）

```bash
# postgresql.conf設定
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
archive_timeout = 300  # 5分ごとに強制アーカイブ
max_wal_senders = 3
wal_keep_segments = 64

# WALアーカイブS3同期
*/5 * * * * aws s3 sync /archive/ s3://tonebridge-backups/wal/ --delete
```

### 3.4 ポイントインタイムリカバリ（PITR）

```bash
#!/bin/bash
# Point-in-Time Recovery Script

RECOVERY_TIME="2024-01-15 10:30:00"
BACKUP_BASE="/backup/postgresql/fullbackup_20240115_020000"
DATA_DIR="/var/lib/postgresql/data"

# 既存データディレクトリを退避
mv ${DATA_DIR} ${DATA_DIR}.old

# ベースバックアップをリストア
tar -xzf ${BACKUP_BASE}.tar.gz -C /var/lib/postgresql/

# recovery.conf作成
cat > ${DATA_DIR}/recovery.conf <<EOF
restore_command = 'cp /archive/%f %p'
recovery_target_time = '${RECOVERY_TIME}'
recovery_target_action = 'promote'
EOF

# PostgreSQL起動
systemctl start postgresql

# リカバリ完了確認
psql -U postgres -c "SELECT pg_is_in_recovery();"
```

## 4. Redisバックアップ

### 4.1 RDBスナップショット

```bash
#!/bin/bash
# Redis RDB Backup Script

REDIS_DIR="/var/lib/redis"
BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# BGSAVEコマンドでバックアップ
redis-cli BGSAVE

# バックアップ完了待機
while [ $(redis-cli LASTSAVE) -eq $(redis-cli LASTSAVE) ]; do
    sleep 1
done

# バックアップファイルをコピー
cp ${REDIS_DIR}/dump.rdb ${BACKUP_DIR}/dump_${DATE}.rdb

# S3へアップロード
aws s3 cp \
    ${BACKUP_DIR}/dump_${DATE}.rdb \
    s3://tonebridge-backups/redis/
```

### 4.2 AOF（Append Only File）設定

```bash
# redis.conf設定
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

## 5. アプリケーションバックアップ

### 5.1 Dockerイメージバックアップ

```bash
#!/bin/bash
# Docker Image Backup Script

IMAGES=("tonebridge/gateway:latest" "tonebridge/llm-service:latest")
BACKUP_DIR="/backup/docker"
DATE=$(date +%Y%m%d)

for IMAGE in "${IMAGES[@]}"; do
    IMAGE_NAME=$(echo $IMAGE | tr '/:' '_')
    docker save $IMAGE | gzip > ${BACKUP_DIR}/${IMAGE_NAME}_${DATE}.tar.gz
    
    # ECRへプッシュ
    aws ecr get-login-password --region ap-northeast-1 | \
        docker login --username AWS --password-stdin ${ECR_REGISTRY}
    docker tag $IMAGE ${ECR_REGISTRY}/$IMAGE
    docker push ${ECR_REGISTRY}/$IMAGE
done
```

### 5.2 設定ファイルバックアップ

```bash
#!/bin/bash
# Configuration Backup Script

CONFIG_DIRS=(
    "/etc/nginx"
    "/etc/postgresql"
    "/etc/redis"
    "/app/config"
)

BACKUP_DIR="/backup/configs"
DATE=$(date +%Y%m%d_%H%M%S)

for DIR in "${CONFIG_DIRS[@]}"; do
    DIR_NAME=$(echo $DIR | tr '/' '_')
    tar -czf ${BACKUP_DIR}/${DIR_NAME}_${DATE}.tar.gz $DIR
done

# Git リポジトリへコミット
cd /backup/configs
git add .
git commit -m "Config backup ${DATE}"
git push origin main
```

## 6. ディザスタリカバリ

### 6.1 RPO/RTO目標

| メトリクス | 目標値 | 説明 |
|-----------|--------|------|
| RPO (Recovery Point Objective) | 1時間 | 許容可能なデータ損失量 |
| RTO (Recovery Time Objective) | 4時間 | 許容可能なダウンタイム |
| MTTR (Mean Time To Repair) | 2時間 | 平均修復時間 |

### 6.2 災害シナリオと対応

#### シナリオ1: データベース障害
```bash
#!/bin/bash
# Database Failure Recovery

# ステップ1: 障害検知
pg_isready -h localhost -p 5432
if [ $? -ne 0 ]; then
    echo "Database is down. Starting recovery..."
    
    # ステップ2: スタンバイへフェイルオーバー
    ssh standby-server "touch /tmp/trigger_file"
    
    # ステップ3: DNSまたはロードバランサー更新
    aws route53 change-resource-record-sets \
        --hosted-zone-id Z1234567890ABC \
        --change-batch file://failover-dns.json
    
    # ステップ4: アプリケーション再起動
    kubectl rollout restart deployment/gateway
fi
```

#### シナリオ2: データセンター障害
```yaml
# Kubernetes Disaster Recovery Manifest
apiVersion: v1
kind: ConfigMap
metadata:
  name: dr-config
data:
  primary_region: "us-east-1"
  dr_region: "us-west-2"
  
---
apiVersion: batch/v1
kind: Job
metadata:
  name: dr-failover
spec:
  template:
    spec:
      containers:
      - name: failover
        image: tonebridge/dr-tools:latest
        command: ["/scripts/failover.sh"]
        env:
        - name: TARGET_REGION
          valueFrom:
            configMapKeyRef:
              name: dr-config
              key: dr_region
```

### 6.3 自動フェイルオーバー設定

```yaml
# HAProxy Configuration for Auto-failover
global
    daemon
    maxconn 4096

defaults
    mode tcp
    timeout connect 5000ms
    timeout client 30000ms
    timeout server 30000ms

listen postgresql
    bind *:5432
    option tcp-check
    tcp-check expect string PostgreSQL
    
    server primary 10.0.1.10:5432 check inter 2000 rise 2 fall 3
    server standby 10.0.2.10:5432 check inter 2000 rise 2 fall 3 backup
```

## 7. バックアップ検証

### 7.1 定期リストアテスト

```bash
#!/bin/bash
# Backup Verification Script

TEST_ENV="test-restore"
BACKUP_FILE=$1

# テスト環境作成
docker run -d \
    --name ${TEST_ENV} \
    -e POSTGRES_PASSWORD=testpass \
    postgres:16

# バックアップリストア
docker exec ${TEST_ENV} pg_restore \
    -U postgres \
    -d postgres \
    ${BACKUP_FILE}

# データ整合性チェック
docker exec ${TEST_ENV} psql -U postgres -c "
    SELECT COUNT(*) FROM users;
    SELECT COUNT(*) FROM transformations;
    SELECT COUNT(*) FROM organizations;
"

# クリーンアップ
docker stop ${TEST_ENV}
docker rm ${TEST_ENV}
```

### 7.2 バックアップ監視

```python
# backup_monitor.py
import boto3
import datetime
import requests

def check_backup_age():
    s3 = boto3.client('s3')
    bucket = 'tonebridge-backups'
    
    # 最新バックアップを確認
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='postgresql/',
        MaxKeys=1
    )
    
    if 'Contents' in response:
        last_backup = response['Contents'][0]
        age = datetime.datetime.now() - last_backup['LastModified'].replace(tzinfo=None)
        
        if age.total_seconds() > 86400:  # 24時間以上古い
            alert_slack(f"Warning: Last backup is {age.days} days old")
            return False
    else:
        alert_slack("Critical: No backups found!")
        return False
    
    return True

def alert_slack(message):
    webhook_url = os.environ['SLACK_WEBHOOK_URL']
    requests.post(webhook_url, json={'text': message})

if __name__ == "__main__":
    check_backup_age()
```

## 8. セキュリティ考慮事項

### 8.1 バックアップの暗号化

```bash
# バックアップ暗号化設定
# GPG暗号化
gpg --encrypt \
    --recipient backup@tonebridge.io \
    --output backup.tar.gz.gpg \
    backup.tar.gz

# AWS S3サーバーサイド暗号化
aws s3 cp backup.tar.gz \
    s3://tonebridge-backups/ \
    --server-side-encryption aws:kms \
    --server-side-encryption-aws-kms-key-id arn:aws:kms:region:account:key/key-id
```

### 8.2 アクセス制御

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/BackupRole"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::tonebridge-backups/*"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/RestoreRole"
      },
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::tonebridge-backups/*"
    }
  ]
}
```

## 9. 復旧手順書

### 9.1 システム全体復旧

1. **インフラストラクチャ復旧**
```bash
# Terraformでインフラ再構築
terraform init
terraform plan -out=recovery.plan
terraform apply recovery.plan
```

2. **データベース復旧**
```bash
# 最新のフルバックアップをリストア
./restore_postgresql.sh latest

# WALログを適用
./apply_wal_logs.sh
```

3. **アプリケーション復旧**
```bash
# Dockerイメージをプル
docker-compose pull

# サービス起動
docker-compose up -d

# ヘルスチェック
./health_check.sh
```

### 9.2 部分復旧

#### 特定テーブルの復旧
```bash
# 特定テーブルのみリストア
pg_restore \
    -h localhost \
    -U postgres \
    -d tonebridge_db \
    -t transformations \
    backup.dump
```

#### 特定期間のデータ復旧
```sql
-- 削除されたデータの復旧
INSERT INTO transformations
SELECT * FROM backup.transformations
WHERE created_at BETWEEN '2024-01-10' AND '2024-01-15'
  AND id NOT IN (SELECT id FROM transformations);
```

## 10. 事業継続計画（BCP）

### 10.1 優先度別復旧順序

| 優先度 | システム/サービス | 目標復旧時間 | 理由 |
|--------|------------------|-------------|------|
| 1 | 認証サービス | 30分 | 全サービスの基盤 |
| 2 | データベース | 1時間 | データ永続性 |
| 3 | API Gateway | 1.5時間 | サービス提供 |
| 4 | LLMサービス | 2時間 | コア機能 |
| 5 | キャッシュ | 3時間 | パフォーマンス |
| 6 | 監視システム | 4時間 | 運用管理 |

### 10.2 緊急連絡体制

```yaml
emergency_contacts:
  incident_commander:
    primary: "+81-90-1234-5678"
    backup: "+81-90-9876-5432"
  
  database_team:
    lead: "db-lead@tonebridge.io"
    oncall: "db-oncall@tonebridge.io"
  
  infrastructure_team:
    lead: "infra-lead@tonebridge.io"
    oncall: "infra-oncall@tonebridge.io"
  
  escalation:
    level1: "team-lead@tonebridge.io"
    level2: "engineering-manager@tonebridge.io"
    level3: "cto@tonebridge.io"
```

## 11. コンプライアンス

### 11.1 規制要件

- **データ保持期間**: 最低7年間（会計データ）
- **監査ログ**: 90日間のオンライン保持、3年間のアーカイブ
- **暗号化**: AES-256以上の暗号化強度
- **地理的冗長性**: 異なる地域での複製保持

### 11.2 定期監査

- 四半期ごとのバックアップ検証
- 年次のディザスタリカバリ訓練
- 外部監査機関による評価

## まとめ

ToneBridgeのバックアップ・リカバリ戦略は、データの完全性と可用性を確保し、災害時にも迅速な復旧を可能にします。定期的な検証と改善により、システムの信頼性を維持します。
