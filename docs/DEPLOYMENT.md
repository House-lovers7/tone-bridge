# 🚀 ToneBridge Deployment Guide

## 📋 デプロイメント概要

ToneBridgeは複数のデプロイメント方式をサポートし、小規模から大規模まで柔軟にスケール可能です。

## 🏗️ アーキテクチャ選択

### Option 1: モノリシック構成（小規模）
```
┌─────────────────┐
│   CloudFlare    │
│    CDN + WAF    │
└────────┬────────┘
         │
┌────────▼────────┐
│  Single Server  │
│   - API Gateway │
│   - Services    │
│   - Database    │
└─────────────────┘
```

### Option 2: マイクロサービス構成（中〜大規模）
```
┌─────────────────┐
│   CloudFlare    │
└────────┬────────┘
         │
┌────────▼────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    │         │        │          │
┌───▼──┐ ┌───▼──┐ ┌──▼───┐ ┌────▼────┐
│ API  │ │Transform│ │Analyze│ │ML Train │
│Gateway│ │Service │ │Service│ │Service  │
└───┬──┘ └───┬──┘ └──┬───┘ └────┬────┘
    │         │        │          │
    └────┬────┴────────┴──────────┘
         │
    ┌────▼────┐
    │Database │
    │ + Redis │
    └─────────┘
```

## 🐳 Docker デプロイメント

### 1. 環境準備

```bash
# リポジトリクローン
git clone https://github.com/tonebridge/tonebridge.git
cd tonebridge

# 環境変数設定
cp .env.example .env.production
```

### 2. 環境変数設定

```bash
# .env.production
# ========================================
# 基本設定
# ========================================
NODE_ENV=production
APP_NAME=ToneBridge
APP_URL=https://api.tonebridge.io

# ========================================
# データベース
# ========================================
DATABASE_URL=postgresql://user:pass@db:5432/tonebridge
REDIS_URL=redis://redis:6379

# ========================================
# 認証
# ========================================
JWT_SECRET=your-secure-jwt-secret-min-32-chars
JWT_REFRESH_SECRET=your-secure-refresh-secret-min-32-chars
API_KEY_SALT=your-secure-api-key-salt

# ========================================
# LLM プロバイダー
# ========================================
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# ========================================
# サービスURL（マイクロサービス構成）
# ========================================
TRANSFORM_SERVICE_URL=http://transform-service:8001
ANALYZE_SERVICE_URL=http://analyze-service:8002
AUTO_TRANSFORM_SERVICE_URL=http://auto-transform:8003
ML_SERVICE_URL=http://ml-service:8004

# ========================================
# モニタリング
# ========================================
SENTRY_DSN=https://...@sentry.io/...
PROMETHEUS_METRICS=true
GRAFANA_API_KEY=...

# ========================================
# セキュリティ
# ========================================
CORS_ORIGINS=https://app.tonebridge.io,https://admin.tonebridge.io
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=100
```

### 3. Docker Compose 本番設定

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # ===================
  # API Gateway
  # ===================
  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    image: tonebridge/api-gateway:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # ===================
  # Transform Service
  # ===================
  transform-service:
    build:
      context: ./services/transform
      dockerfile: Dockerfile
    image: tonebridge/transform:latest
    restart: always
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 1G

  # ===================
  # Database
  # ===================
  postgres:
    image: pgvector/pgvector:pg16
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      POSTGRES_DB: tonebridge
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # ===================
  # Redis Cache
  # ===================
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # ===================
  # Nginx Reverse Proxy
  # ===================
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./infrastructure/nginx/ssl:/etc/nginx/ssl
      - ./infrastructure/nginx/cache:/var/cache/nginx
    depends_on:
      - api-gateway

volumes:
  postgres_data:
  redis_data:
```

### 4. デプロイ実行

```bash
# イメージビルド
docker-compose -f docker-compose.production.yml build

# サービス起動
docker-compose -f docker-compose.production.yml up -d

# ログ確認
docker-compose -f docker-compose.production.yml logs -f

# ヘルスチェック
curl https://api.tonebridge.io/health
```

## ☸️ Kubernetes デプロイメント

### 1. namespace作成

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tonebridge
```

### 2. ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tonebridge-config
  namespace: tonebridge
data:
  NODE_ENV: "production"
  APP_NAME: "ToneBridge"
  REDIS_URL: "redis://redis-service:6379"
  DATABASE_URL: "postgresql://user:pass@postgres-service:5432/tonebridge"
```

### 3. Secret

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tonebridge-secret
  namespace: tonebridge
type: Opaque
stringData:
  JWT_SECRET: "your-jwt-secret"
  OPENAI_API_KEY: "sk-..."
  DB_PASSWORD: "secure-password"
```

### 4. Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: tonebridge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: tonebridge/api-gateway:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: tonebridge-config
        - secretRef:
            name: tonebridge-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 5. Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: tonebridge
spec:
  selector:
    app: api-gateway
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### 6. HorizontalPodAutoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: tonebridge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 7. デプロイ実行

```bash
# namespace作成
kubectl apply -f k8s/namespace.yaml

# 設定適用
kubectl apply -f k8s/

# 状態確認
kubectl get pods -n tonebridge
kubectl get services -n tonebridge

# ログ確認
kubectl logs -f deployment/api-gateway -n tonebridge
```

## ☁️ クラウドプロバイダー別設定

### AWS デプロイメント

```bash
# 1. ECR にイメージをプッシュ
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ECR_URI
docker tag tonebridge/api-gateway:latest $ECR_URI/tonebridge/api-gateway:latest
docker push $ECR_URI/tonebridge/api-gateway:latest

# 2. ECS タスク定義
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 3. サービス作成
aws ecs create-service \
  --cluster tonebridge-cluster \
  --service-name api-gateway \
  --task-definition tonebridge-api:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"

# 4. RDS PostgreSQL設定
aws rds create-db-instance \
  --db-instance-identifier tonebridge-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16 \
  --master-username tonebridge \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxx
```

### Google Cloud Platform

```bash
# 1. Container Registry にプッシュ
gcloud auth configure-docker
docker tag tonebridge/api-gateway gcr.io/$PROJECT_ID/api-gateway
docker push gcr.io/$PROJECT_ID/api-gateway

# 2. Cloud Run デプロイ
gcloud run deploy api-gateway \
  --image gcr.io/$PROJECT_ID/api-gateway \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NODE_ENV=production

# 3. Cloud SQL設定
gcloud sql instances create tonebridge-db \
  --database-version=POSTGRES_16 \
  --tier=db-n1-standard-2 \
  --region=us-central1
```

### Azure

```bash
# 1. Container Registry にプッシュ
az acr login --name tonebridgeacr
docker tag tonebridge/api-gateway tonebridgeacr.azurecr.io/api-gateway
docker push tonebridgeacr.azurecr.io/api-gateway

# 2. Container Instances デプロイ
az container create \
  --resource-group tonebridge-rg \
  --name api-gateway \
  --image tonebridgeacr.azurecr.io/api-gateway \
  --cpu 1 --memory 1 \
  --environment-variables NODE_ENV=production \
  --ports 8000

# 3. Azure Database for PostgreSQL
az postgres server create \
  --resource-group tonebridge-rg \
  --name tonebridge-db \
  --admin-user tonebridge \
  --admin-password $DB_PASSWORD \
  --sku-name B_Gen5_2
```

## 🔒 セキュリティ設定

### SSL/TLS設定

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.tonebridge.io;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://api-gateway:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### ファイアウォール設定

```bash
# UFW (Ubuntu)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -j DROP
```

## 📊 モニタリング設定

### Prometheus設定

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana ダッシュボード

```json
{
  "dashboard": {
    "title": "ToneBridge Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, api_response_time_bucket)"
          }
        ]
      },
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(api_errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 🔄 CI/CD パイプライン

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
          
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and push Docker images
        env:
          DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        run: |
          docker build -t $DOCKER_REGISTRY/api-gateway:$GITHUB_SHA ./services/api-gateway
          docker push $DOCKER_REGISTRY/api-gateway:$GITHUB_SHA
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        env:
          KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
        run: |
          echo "$KUBE_CONFIG" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
          kubectl set image deployment/api-gateway api-gateway=$DOCKER_REGISTRY/api-gateway:$GITHUB_SHA -n tonebridge
          kubectl rollout status deployment/api-gateway -n tonebridge
```

## 🔧 本番環境チェックリスト

### デプロイ前

- [ ] 環境変数がすべて設定されている
- [ ] データベースのバックアップが設定されている
- [ ] SSL証明書が有効
- [ ] セキュリティグループ/ファイアウォールが設定されている
- [ ] ログ収集が設定されている
- [ ] モニタリングが設定されている
- [ ] アラートが設定されている
- [ ] ロードテストが完了している

### デプロイ後

- [ ] ヘルスチェックが通る
- [ ] APIエンドポイントが応答する
- [ ] データベース接続が確立されている
- [ ] キャッシュが動作している
- [ ] ログが正常に出力されている
- [ ] メトリクスが収集されている
- [ ] アラートが機能している
- [ ] バックアップが動作している

## 🚨 トラブルシューティング

### よくある問題

#### 1. データベース接続エラー
```bash
# 接続確認
psql -h localhost -U tonebridge -d tonebridge

# ログ確認
docker logs postgres

# 解決策
- ファイアウォール設定確認
- 接続文字列確認
- PostgreSQLの接続許可設定確認
```

#### 2. メモリ不足
```bash
# メモリ使用状況確認
docker stats

# 解決策
- コンテナのメモリ制限を増やす
- スワップメモリを設定
- 不要なサービスを停止
```

#### 3. レート制限エラー
```bash
# Redis接続確認
redis-cli ping

# 解決策
- Redis接続設定確認
- Redisメモリ設定確認
- レート制限設定の調整
```

## 📞 サポート

デプロイメントに関する質問：
- Documentation: https://docs.tonebridge.io/deployment
- Support: support@tonebridge.io
- Community: https://community.tonebridge.io

---

Last Updated: 2024-01-15