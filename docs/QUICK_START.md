# 🚀 ToneBridge クイックスタート

5分でToneBridgeを起動して使い始めるためのガイドです。

## 📋 前提条件

- Docker & Docker Compose
- Git
- OpenAI API Key（または他のLLM API Key）

## 🏃 Quick Setup (1分)

```bash
# 1. リポジトリをクローン
git clone https://github.com/tonebridge/tonebridge.git
cd tonebridge

# 2. 環境変数を設定
cp .env.example .env
# .envファイルを編集してOPENAI_API_KEYを設定

# 3. サービスを起動
docker-compose up -d

# 4. ブラウザでアクセス
open http://localhost:8080
```

## 🎯 最初の変換を試す

### Web UIから

1. http://localhost:8080 にアクセス
2. テキストエリアに文章を入力
3. 変換タイプを選択（Soften, Clarify, etc.）
4. "Transform"ボタンをクリック

### cURLから

```bash
# APIトークンを取得（テスト用）
TOKEN="test-api-key"

# テキスト変換
curl -X POST http://localhost:8000/api/v1/transform \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is totally unacceptable!",
    "transformation_type": "soften",
    "intensity": 2
  }'
```

## 📦 SDK を使う

### JavaScript/TypeScript

```bash
npm install @tonebridge/sdk
```

```javascript
import { ToneBridgeClient } from '@tonebridge/sdk';

const client = new ToneBridgeClient({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:8000'
});

const result = await client.transform.soften(
  "This is totally unacceptable!",
  2
);
console.log(result.transformedText);
```

### Python

```bash
pip install tonebridge
```

```python
from tonebridge import ToneBridgeClient

client = ToneBridgeClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

result = client.transform.soften(
    "This is totally unacceptable!",
    intensity=2
)
print(result.transformed_text)
```

### Go

```bash
go get github.com/tonebridge/go-sdk
```

```go
import "github.com/tonebridge/go-sdk/tonebridge"

client := tonebridge.NewClient("your-api-key")

result, err := client.Transform.Soften(
    ctx,
    "This is totally unacceptable!",
    2,
    nil
)
```

## 🔌 プラットフォーム統合

### Slack

```bash
# 1. Slack Appを作成
# 2. 環境変数を設定
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# 3. Slackボットを起動
docker-compose up slack-bot -d

# 4. Slackで使用
/soften This is unacceptable!
```

### Microsoft Teams

```bash
# 1. Bot Frameworkに登録
# 2. 環境変数を設定
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...

# 3. Teamsボットを起動
docker-compose up teams-bot -d
```

### Discord

```bash
# 1. Discord Appを作成
# 2. 環境変数を設定
DISCORD_TOKEN=...

# 3. Discordボットを起動
docker-compose up discord-bot -d
```

## 🧪 動作確認

### ヘルスチェック

```bash
# API Gateway
curl http://localhost:8000/health

# WebSocket
curl http://localhost:3001/health

# 全サービスの状態確認
docker-compose ps
```

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f api-gateway
```

## 🔧 設定カスタマイズ

### 変換強度の調整

```yaml
# config.yaml
transform:
  default_intensity: 2  # 1-3
  cache_ttl: 300        # seconds
```

### LLMプロバイダーの変更

```bash
# .env
LLM_PROVIDER=openai  # openai, anthropic, google
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

## 🐛 トラブルシューティング

### ポートが使用中

```bash
# 使用中のポートを確認
lsof -i :8000

# docker-compose.ymlでポートを変更
ports:
  - "8001:8000"  # 8001に変更
```

### メモリ不足

```bash
# Docker のメモリ制限を増やす
# Docker Desktop > Preferences > Resources > Memory: 4GB以上
```

### API エラー

```bash
# ログを確認
docker-compose logs api-gateway -f

# サービスを再起動
docker-compose restart api-gateway
```

## 📖 次のステップ

1. [API リファレンス](API_REFERENCE.md) - 全エンドポイントの詳細
2. [SDK ガイド](SDK_GUIDE.md) - SDK の詳細な使用方法
3. [デプロイメント](DEPLOYMENT.md) - 本番環境へのデプロイ
4. [アーキテクチャ](ARCHITECTURE.md) - システム設計の理解

## 💡 Tips

- **開発モード**: `docker-compose.dev.yml` を使用すると、ホットリロード対応
- **テスト実行**: `make test` で全テストを実行
- **パフォーマンス**: Golang API Gatewayにより30msの高速レスポンス

---

問題が解決しない場合は、[GitHub Issues](https://github.com/tonebridge/issues) または support@tonebridge.io までお問い合わせください。