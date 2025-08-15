# 🚀 ToneBridge セットアップガイド

## 📋 目次

1. [前提条件](#前提条件)
2. [クイックセットアップ（5分）](#クイックセットアップ5分)
3. [詳細セットアップ](#詳細セットアップ)
4. [開発環境セットアップ](#開発環境セットアップ)
5. [トラブルシューティング](#トラブルシューティング)
6. [次のステップ](#次のステップ)

## 前提条件

### 必須要件

- **Docker Desktop** (v20.10以上)
  - [Mac](https://docs.docker.com/desktop/install/mac-install/)
  - [Windows](https://docs.docker.com/desktop/install/windows-install/)
  - [Linux](https://docs.docker.com/desktop/install/linux-install/)
- **Docker Compose** (v2.0以上)
- **Git**
- **OpenAI API Key** ([取得方法](https://platform.openai.com/api-keys))

### 推奨要件

- **メモリ**: 8GB以上
- **ディスク容量**: 10GB以上の空き容量
- **OS**: macOS 11+, Windows 10/11 (WSL2), Ubuntu 20.04+

### オプション（開発者向け）

- **Node.js** v18+ (Web UI開発)
- **Go** 1.21+ (API Gateway開発)
- **Python** 3.11+ (LLMサービス開発)
- **PostgreSQL** クライアント (データベース管理)
- **Redis** クライアント (キャッシュ管理)

## クイックセットアップ（5分）

最も簡単な方法でToneBridgeを起動します。

### 1. リポジトリのクローン

```bash
# HTTPSを使用
git clone https://github.com/tonebridge/tonebridge.git

# または SSHを使用
git clone git@github.com:tonebridge/tonebridge.git

cd tonebridge
```

### 2. 自動セットアップスクリプトの実行

```bash
# 実行権限を付与
chmod +x quickstart.sh

# セットアップ実行
./quickstart.sh
```

スクリプトが以下を自動的に実行します：
- 環境チェック
- `.env`ファイルの作成
- Dockerイメージのビルド
- サービスの起動
- ヘルスチェック

### 3. OpenAI API Keyの設定

`.env`ファイルを編集してAPIキーを設定：

```bash
# エディタで開く
nano .env
# または
vi .env
# または
code .env  # VS Code
```

以下の行を更新：
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
↓
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. サービスの再起動

```bash
cd infrastructure
docker-compose restart
```

### 5. 動作確認

ブラウザで以下にアクセス：
- **Web UI**: http://localhost:8082
- **API Health**: http://localhost:8082/health
- **API Docs**: http://localhost:8082/docs

## 詳細セットアップ

### Step 1: 環境変数の詳細設定

```bash
# .env.exampleから.envを作成
cp .env.example .env
```

#### 必須設定項目

```env
# LLM設定（必須）
OPENAI_API_KEY=sk-your-api-key-here

# データベース（デフォルトでOK）
DATABASE_URL=postgresql://tonebridge:tonebridge123@localhost:5432/tonebridge

# Redis（デフォルトでOK）
REDIS_URL=redis://localhost:6379

# JWT認証（本番環境では必ず変更）
JWT_SECRET=your-secure-jwt-secret-min-32-chars
JWT_REFRESH_SECRET=your-secure-refresh-secret-min-32-chars
```

#### オプション設定

```env
# 他のLLMプロバイダー
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Slack統合
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# Teams統合
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...

# Discord統合
DISCORD_BOT_TOKEN=...
```

### Step 2: Dockerイメージのビルド

```bash
cd infrastructure

# 全サービスをビルド
docker-compose build

# 特定サービスのみビルド
docker-compose build api-gateway
docker-compose build llm
```

### Step 3: データベースの初期化

```bash
# PostgreSQLコンテナのみ起動
docker-compose up -d postgres

# マイグレーション実行
docker-compose exec postgres psql -U tonebridge -d tonebridge -f /docker-entrypoint-initdb.d/init.sql

# テーブル確認
docker-compose exec postgres psql -U tonebridge -d tonebridge -c "\dt"
```

### Step 4: サービスの起動

```bash
# バックグラウンドで全サービス起動
docker-compose up -d

# または、ログを見ながら起動
docker-compose up

# 特定サービスのみ起動
docker-compose up -d api-gateway llm postgres redis
```

### Step 5: サービスの確認

```bash
# 起動状態確認
docker-compose ps

# ログ確認
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f api-gateway
```

## 開発環境セットアップ

### ローカル開発（Docker不使用）

#### 1. PostgreSQLのインストールと設定

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-16 postgresql-contrib

# データベース作成
createdb tonebridge
psql tonebridge < infrastructure/postgres/init.sql
```

#### 2. Redisのインストールと起動

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

#### 3. API Gatewayの起動（Golang）

```bash
cd services/api-gateway

# 依存関係インストール
go mod download

# 環境変数設定
export DATABASE_URL="postgresql://localhost/tonebridge"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="development-secret-key"

# 起動
go run main.go
```

#### 4. LLMサービスの起動（Python）

```bash
cd services/llm

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
export OPENAI_API_KEY="sk-your-api-key"
export DATABASE_URL="postgresql://localhost/tonebridge"

# 起動
uvicorn app.main:app --reload --port 8000
```

#### 5. Web UIの起動

```bash
cd web

# Nginxで静的ファイルをサーブ
python -m http.server 3000

# または Node.jsのサーバー
npx serve -p 3000
```

### VS Code開発環境

`.vscode/launch.json`を作成：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "API Gateway",
      "type": "go",
      "request": "launch",
      "mode": "debug",
      "program": "${workspaceFolder}/services/api-gateway/main.go",
      "env": {
        "DATABASE_URL": "postgresql://localhost/tonebridge",
        "REDIS_URL": "redis://localhost:6379"
      }
    },
    {
      "name": "LLM Service",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/services/llm",
      "env": {
        "OPENAI_API_KEY": "sk-your-api-key"
      }
    }
  ]
}
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. Docker関連のエラー

**問題**: `Cannot connect to the Docker daemon`
```bash
# Docker Desktopが起動しているか確認
docker version

# Dockerサービスを再起動
# macOS/Windows: Docker Desktopを再起動
# Linux:
sudo systemctl restart docker
```

**問題**: `port is already allocated`
```bash
# 使用中のポートを確認
lsof -i :8082  # Mac/Linux
netstat -ano | findstr :8082  # Windows

# プロセスを終了するか、ポートを変更
# docker-compose.ymlでポートを変更
ports:
  - "8083:8080"  # 8083に変更（内部ポート8080はそのまま）
```

#### 2. データベース接続エラー

**問題**: `could not connect to database`
```bash
# PostgreSQLコンテナの状態確認
docker-compose ps postgres
docker-compose logs postgres

# データベースに直接接続してテスト
docker-compose exec postgres psql -U tonebridge -d tonebridge

# 接続文字列を確認
echo $DATABASE_URL
```

#### 3. OpenAI APIエラー

**問題**: `Invalid API key`
```bash
# API Keyが正しく設定されているか確認
grep OPENAI_API_KEY .env

# 環境変数が読み込まれているか確認
docker-compose exec llm env | grep OPENAI

# サービスを再起動
docker-compose restart llm
```

#### 4. メモリ不足

**問題**: `Container killed due to memory limit`
```bash
# Docker Desktopのメモリ設定を増やす
# Settings > Resources > Memory: 4GB以上に設定

# または docker-compose.ymlでメモリ制限を調整
deploy:
  resources:
    limits:
      memory: 2G
```

### ログの確認方法

```bash
# 全サービスのログ
docker-compose logs

# リアルタイムログ（フォロー）
docker-compose logs -f

# 特定サービスのログ
docker-compose logs api-gateway

# 最新100行のみ
docker-compose logs --tail=100

# タイムスタンプ付き
docker-compose logs -t
```

### サービスの管理

```bash
# サービスの停止
docker-compose stop

# サービスの削除（データは保持）
docker-compose down

# サービスとデータの完全削除
docker-compose down -v

# 特定サービスの再起動
docker-compose restart api-gateway

# サービスの再ビルドと起動
docker-compose up -d --build
```

## 次のステップ

### 1. APIをテストする

```bash
# ユーザー登録
curl -X POST http://localhost:8082/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "name": "Test User"
  }'

# ログイン
curl -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# テキスト変換（トークンを使用）
curl -X POST http://localhost:8082/api/v1/transform \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is completely unacceptable!",
    "transformation_type": "soften",
    "intensity": 2
  }'
```

### 2. SDK を使ってみる

```javascript
// JavaScript
npm install @tonebridge/sdk

const { ToneBridgeClient } = require('@tonebridge/sdk');
const client = new ToneBridgeClient({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:8082'
});

const result = await client.transform.soften(
  "This is unacceptable!",
  2
);
console.log(result.transformedText);
```

### 3. ドキュメントを読む

- [API リファレンス](API_REFERENCE.md)
- [SDK ガイド](SDK_GUIDE.md)
- [アーキテクチャ](ARCHITECTURE.md)
- [デプロイメント](DEPLOYMENT.md)

### 4. 統合を設定する

- [Slack Bot設定](../integrations/slack/README.md)
- [Teams Bot設定](../integrations/teams/README.md)
- [Discord Bot設定](../integrations/discord/README.md)
- [Outlook Add-in設定](../integrations/outlook/README.md)

## サポート

問題が解決しない場合：

1. [GitHub Issues](https://github.com/tonebridge/tonebridge/issues)で既知の問題を検索
2. [ディスカッションフォーラム](https://github.com/tonebridge/tonebridge/discussions)で質問
3. support@tonebridge.io にメールで問い合わせ

---

Happy Coding! 🎉