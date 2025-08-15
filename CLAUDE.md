# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ToneBridgeは、エンジニアと非エンジニア間のコミュニケーションギャップを解消するAI駆動型プラットフォームです。メッセージの文体変換、構造化、要約、専門用語の翻訳などを通じて、チーム間の円滑なコミュニケーションを実現します。

## 開発コマンド

### 基本コマンド

```bash
# 初期セットアップ
make setup          # 環境構築（.envファイル作成、依存関係インストール）
./quickstart.sh     # クイックスタート（Dockerイメージビルド・起動）
./dev.sh setup      # 開発環境セットアップ

# サービス管理（注: docker-composeはinfrastructure/ディレクトリで実行）
make up             # 全サービス起動
make down           # 全サービス停止
make restart        # 全サービス再起動
make logs           # サービスログ表示
make status         # サービス状態確認
make health-check   # サービスヘルスチェック
./dev.sh status     # 詳細ヘルスチェック

# ビルド
make build          # Dockerイメージビルド
make build-prod     # 本番用ビルド

# テスト
make test           # 全テスト実行
make test-gateway   # Gateway単体テスト
make test-llm       # LLMサービス単体テスト
make test-transform # 変換エンドポイントテスト
make test-analyze   # 分析エンドポイントテスト
./tests/api_test.sh # APIテスト
./dev.sh test-api   # APIテストヘルパー
python tests/load_test.py  # 負荷テスト
./dev.sh test-load  # 負荷テストヘルパー

# リント
make lint           # 全サービスのリント
make lint-gateway   # Gateway (golangci-lint)
make lint-llm       # LLMサービス (flake8)

# 開発モード起動
make gateway        # Gateway起動 (go run)
make gateway-dev    # Gateway開発モード (localhost:8082)
make llm            # LLMサービス起動 (uvicorn)
make llm-dev        # LLMサービス開発モード (localhost:8000)
make watch-gateway  # Gateway自動リロード (air使用)
make watch-llm      # LLMサービス自動リロード
./dev.sh gateway-dev # Gateway開発モードヘルパー
./dev.sh llm-dev    # LLMサービス開発モードヘルパー

# WebSocketサーバー開発
cd services/websocket-server && npm run dev  # 開発モード起動
cd services/websocket-server && npm run build # ビルド
cd services/websocket-server && npm test      # テスト実行
cd services/websocket-server && npm run lint  # リント実行

# データベース・キャッシュアクセス
make db             # PostgreSQLシェル
make redis-cli      # Redis CLI
./dev.sh db         # PostgreSQLシェルヘルパー
./dev.sh redis      # Redis CLIヘルパー
./dev.sh backup     # DBバックアップ (backups/ディレクトリに保存)
./dev.sh restore backups/backup_file.sql # DBリストア

# クリーンアップ
make clean          # コンテナ・ボリューム削除
make docker-clean-all # 全Docker要素削除（警告：全Dockerリソース削除）
./dev.sh clean      # 対話式クリーンアップ
```

## アーキテクチャ

### システム構成

```
Client Layer (Web, Slack, Teams, Discord, Outlook, SDK)
    ↓
CloudFlare (CDN + WAF)
    ↓
API Gateway (Golang/Fiber v3) :8082
    ├── 認証 (JWT/API Key)
    ├── レート制限
    ├── キャッシュ (L1: In-Memory LRU, L2: Redis)
    └── Circuit Breaker
    ↓
Service Layer
    ├── Transform Service (Python/FastAPI/LangChain) :8001
    ├── Analyze Service (Python/FastAPI) :8002
    ├── Auto-Transform Service :8003
    ├── WebSocket Server (Node.js/Socket.IO) :3001
    └── ML Training Service
    ↓
Data Layer
    ├── PostgreSQL 16 + pgvector :5432
    └── Redis 7 :6379
```

### 主要サービス

1. **API Gateway** (services/gateway/)
   - Golang/Fiber v3
   - JWT認証、レート制限、キャッシング
   - パフォーマンス: 5,000+ RPS, p50 30ms
   - ポート: 8082 (注: 一部ドキュメントで8080と記載されている場合がありますが、正しくは8082です)

2. **LLM Service** (services/llm/)
   - Python/FastAPI/LangChain
   - 7つの変換タイプ（soften, clarify, structure, summarize, terminology, requirements, background）
   - OpenAI GPT-4/Anthropic Claude/Google Gemini対応

3. **WebSocket Server** (services/websocket-server/)
   - Node.js/Socket.IO
   - リアルタイム双方向通信
   - Redis Pub/Sub統合

4. **統合サービス** (integrations/)
   - Slack Bot (Python)
   - Teams Bot (Python)
   - Discord Bot (Python)
   - Outlook Add-in (JavaScript)

### データモデル

- **users**: ユーザー情報、認証
- **organizations**: 組織管理、プラン
- **transformations**: 変換履歴（パーティション対応）
- **embeddings**: ベクトル検索用
- **analytics**: 分析データ

## SDK

各言語向けSDKを提供：

- **JavaScript/TypeScript** (sdk/javascript/)
  ```bash
  cd sdk/javascript
  npm install          # 依存関係インストール
  npm run build        # ビルド
  npm test            # テスト実行
  npm run lint        # リント実行
  ```

- **Python** (sdk/python/)
  ```bash
  cd sdk/python
  python setup.py install  # インストール
  pip install -e .        # 開発モードインストール
  ```

- **Go** (sdk/go/)
  ```bash
  cd sdk/go
  go mod download     # 依存関係ダウンロード
  go test ./...       # テスト実行
  go run examples/basic/main.go  # サンプル実行
  ```

## モバイルアプリ (Expo/React Native)

ToneBridgeのモバイルアプリ開発：

### 開発セットアップ
```bash
cd mobile-app
npm install                    # 依存関係インストール
cp .env.example .env          # 環境変数設定
npm start                     # Expo開発サーバー起動
```

### 開発コマンド
```bash
# プラットフォーム別起動
npm run ios                   # iOSシミュレータで起動
npm run android              # Androidエミュレータで起動
npm run web                  # Webブラウザで起動

# テストとリント
npm test                     # テスト実行
npm run lint                 # ESLint実行
npm run type-check          # TypeScriptチェック
```

### EAS Build/Deploy
```bash
# EAS CLIセットアップ
npm install -g eas-cli
eas login

# ビルド
eas build --platform ios --profile production      # iOS本番ビルド
eas build --platform android --profile production  # Android本番ビルド
eas build --platform all --profile preview        # 両プラットフォーム開発ビルド

# App Store/Play Store提出
eas submit --platform ios --profile production    # App Store提出
eas submit --platform android --profile production # Play Store提出

# ビルド状況確認
eas build:list --platform ios
eas build:view --platform ios
```

### ドキュメント
- [Expoセットアップガイド](mobile-app/EXPO_SETUP.md)
- [iOS App Store公開ガイド](mobile-app/IOS_DEPLOYMENT.md)

## 環境変数

必須の環境変数（.envファイル）：

```bash
# LLM API Keys (最低1つ必須)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key  # Optional
GOOGLE_API_KEY=your-google-key        # Optional

# Database
POSTGRES_PASSWORD=password

# Security
JWT_SECRET=your-secret-key

# Integration (使用する場合)
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
MICROSOFT_APP_ID=
MICROSOFT_APP_PASSWORD=
DISCORD_TOKEN=
```

## 既知の問題

### Transform API エラー [修正済み]

~~現在、変換APIで`intensity_level`パラメータが不足するとエラーが発生します：~~

```json
{"detail":"Transformation failed: Missing some input keys: {'intensity_level'}"}
```

**修正済み**: 
- `web/index.html` に変換強度選択UI追加 (Line 146-153)
- `web/app.js` の`handleTransform`関数を修正 (Line 186, 199)

### レート制限エラー (429 Too Many Requests)

プレビューモードには以下のレート制限が設定されています：
- **1分間に3リクエストまで**
- **1日に10リクエストまで**

**対処法**:
- リクエスト間隔を20秒以上空ける
- Redis接続を確認: `make redis-cli` → `ping`
- レート制限をクリア: `make redis-cli` → `DEL preview:rate:minute:YOUR_IP preview:rate:daily:YOUR_IP`
- レート制限設定を変更: services/gateway/internal/middleware/preview_limiter.go (Line 26-28)
- 開発環境では制限値を増やすか、middleware を一時的に無効化することも可能

## 開発の流れ

1. **環境構築**
   ```bash
   # 方法1: Makefileを使用
   make setup
   # .envファイルにOpenAI API Keyを設定
   make up
   make health-check
   
   # 方法2: クイックスタートスクリプトを使用
   ./quickstart.sh
   ```

2. **開発作業**
   - Gatewayの変更: services/gateway/
     - `make watch-gateway` で自動リロード開発
   - LLMサービスの変更: services/llm/
     - `make watch-llm` で自動リロード開発
   - WebSocketの変更: services/websocket-server/
     - `cd services/websocket-server && npm run dev` で開発

3. **テスト実行**
   ```bash
   make test            # 全テスト実行
   make test-gateway    # Gateway単体テスト
   make test-llm        # LLMサービス単体テスト
   make test-transform  # 変換エンドポイントテスト
   make test-analyze    # 分析エンドポイントテスト
   ```

4. **デプロイ**
   ```bash
   make build-prod
   # CI/CDパイプライン経由でデプロイ
   ```

## パフォーマンスチューニング

### キャッシュ戦略
- L1 Cache (In-Memory LRU): 10,000エントリー、TTL 5分
- L2 Cache (Redis): TTL 24時間
- キャッシュヒット率目標: 合計85%

### スケーリング設定
- API Gateway: 3-20 pods (CPU 70%, Memory 80%)
- Transform Service: 2-10 pods (CPU 60%)
- PostgreSQL: Read Replicaによる読み取り分散

### 接続プール
- PostgreSQL: MaxConns 50, MinConns 10
- Redis: PoolSize 100, MinIdleConns 10

## セキュリティ

- CloudFlare WAF: DDoS保護、IP制限
- JWT認証 (RS256)
- レート制限: ユーザー/IP単位
- 入力検証: Pydantic/Joi
- プロンプトインジェクション対策実装
- データ暗号化: AES-256 (at rest), TLS 1.3 (in transit)

## トラブルシューティング

### Dockerデーモンが起動していないエラー
```
Cannot connect to the Docker daemon at unix:///Users/tg/.docker/run/docker.sock. Is the docker daemon running?
```

**解決方法**:
```bash
# macOS: Docker Desktopを起動
open -a Docker

# Linux: Dockerサービスを起動
sudo systemctl start docker

# 起動確認
docker info

# 再度実行
./quickstart.sh
```

**注意**: `docker-compose.yml`の`version`属性に関する警告は無視して構いません（最新のDocker Composeでは不要）

### サービスが起動しない
```bash
make down
make clean
make build
make up
```

### ログ確認
```bash
make logs                                    # 全サービス
cd infrastructure && docker-compose logs llm # 特定サービス
cd infrastructure && docker-compose logs gateway # Gatewayログ
```

### ポート番号の確認
API Gatewayのポート番号が正しいか確認：
- 正しいポート: **8082**
- もし8080でアクセスしている場合は8082に変更してください
```bash
curl http://localhost:8082/health  # 正しい
curl http://localhost:8080/health  # 間違い（古いドキュメントの場合）
```

### データベース接続エラー
```bash
make db  # PostgreSQL接続確認
# tonebridge_db データベース、tonebridge ユーザーを確認
```

### Redis接続エラー
```bash
make redis-cli
# ping コマンドで応答確認
```

## 重要なファイル

- `Makefile`: 開発コマンド定義
- `docker-compose.yml`: Docker構成
- `quickstart.sh`: クイックスタートスクリプト
- `dev.sh`: 開発ヘルパースクリプト
- `services/gateway/cmd/api/main.go`: Gateway エントリポイント
- `services/llm/app/main.py`: LLMサービス エントリポイント
- `infrastructure/postgres/migrations/`: DBマイグレーション
- `docs/ARCHITECTURE.md`: 詳細アーキテクチャドキュメント