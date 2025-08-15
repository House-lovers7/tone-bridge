# ToneBridge - エンジニア↔非エンジニア摩擦ゼロ化プラットフォーム

<p align="center">
  <strong>AI駆動のコミュニケーション変換プラットフォーム</strong><br>
  技術チームとビジネスチーム間のコミュニケーションギャップを解消
</p>

<p align="center">
  <a href="./docs/QUICK_START.md">クイックスタート</a> •
  <a href="./docs/README.md">ドキュメント</a> •
  <a href="./docs/API_REFERENCE.md">API</a> •
  <a href="./mobile-app/EXPO_SETUP.md">モバイルアプリ</a>
</p>

---

## 🎯 概要

ToneBridgeは、エンジニアと非エンジニア間のコミュニケーションギャップを解消するAI駆動型プラットフォームです。メッセージの文体変換、構造化、要約、専門用語の翻訳などを通じて、チーム間の円滑なコミュニケーションを実現します。

## ✨ 主要機能

- **🔄 文体変換**: 技術的/論理的な文章を温かみのある配慮型文体へ（逆方向も可能）
- **📝 構造化・要約**: 長文や曖昧な文章を構造化・要点抽出
- **🔤 専門用語マッピング**: 技術用語とビジネス用語の双方向変換
- **🚨 優先度判定**: メッセージの緊急度を自動判定
- **🌐 マルチプラットフォーム対応**: Web、Mobile、Slack、Teams、Discord、Outlook

## 🚀 クイックスタート

```bash
# リポジトリをクローン
git clone <repository-url>
cd ToneBridge

# 環境構築と起動
./quickstart.sh

# または Makefile を使用
make setup
make up
```

詳細は [クイックスタートガイド](./docs/QUICK_START.md) を参照してください。

## 📱 モバイルアプリ

```bash
cd mobile-app
npm install
npm start
```

詳細は [Expoセットアップガイド](./mobile-app/EXPO_SETUP.md) を参照してください。

## 🛠 技術スタック

- **API Gateway**: Golang (Fiber v2) - 高性能ルーティング (ポート: 8082)
- **LLM Service**: Python (FastAPI + LangChain) - AI処理
- **Real-time**: Socket.IO + Redis - リアルタイム通信
- **Database**: PostgreSQL 16 + pgvector - ベクトル検索対応
- **Mobile**: React Native + Expo SDK 49 - クロスプラットフォーム

## 📂 プロジェクト構造

```
ToneBridge/
├── services/              # マイクロサービス
│   ├── gateway/          # API Gateway (Golang)
│   ├── llm/              # LLM Service (Python)
│   ├── websocket-server/ # WebSocket Server (Node.js)
│   └── auto-transform/   # 自動変換サービス
├── mobile-app/           # React Native + Expo
├── sdk/                  # 各言語SDK
│   ├── javascript/
│   ├── python/
│   └── go/
├── integrations/         # 外部サービス連携
│   ├── slack/
│   ├── teams/
│   ├── discord/
│   └── outlook/
├── infrastructure/       # インフラ設定
├── docs/                # ドキュメント
└── web/                 # Webフロントエンド
```

## 📡 API エンドポイント

主要なエンドポイント：
- `POST /api/v1/transform` - テキスト変換
- `POST /api/v1/analyze` - テキスト分析
- `POST /api/v1/auth/login` - ログイン
- `GET /api/v1/history` - 変換履歴

詳細は [APIリファレンス](./docs/API_REFERENCE.md) を参照してください。

## 📚 ドキュメント

### 開発者向け
- [開発者ガイド](./docs/DEVELOPER_GUIDE.md)
- [セットアップガイド](./docs/SETUP_GUIDE.md)
- [APIリファレンス](./docs/API_REFERENCE.md)
- [SDKガイド](./docs/SDK_GUIDE.md)
- [実装ステータス](./docs/IMPLEMENTATION_STATUS.md)

### 運用・デプロイ
- [デプロイメントガイド](./docs/DEPLOYMENT.md)
- [iOS App Store公開ガイド](./mobile-app/IOS_DEPLOYMENT.md)

### その他
- [アーキテクチャ設計](./docs/ARCHITECTURE.md)
- [サービス仕様書](./docs/02_architecture/SERVICE_SPECIFICATION.md)
- [全ドキュメント一覧](./docs/README.md)

## 🤝 コントリビューション

プルリクエストは歓迎します。大きな変更の場合は、まず issue を開いて変更内容を議論してください。

開発に参加する場合は [CLAUDE.md](./CLAUDE.md) を参照してください。

## 📄 ライセンス

[MIT](LICENSE)

## 📮 サポート

- **Issues**: [GitHub Issues](https://github.com/tonebridge/issues)
- **Email**: support@tonebridge.io
- **Documentation**: [docs/](./docs/)

---

© 2024 ToneBridge. All rights reserved.