# ToneBridge ドキュメントセンター

## 📚 ドキュメント構成

ToneBridgeプロジェクトのドキュメントは、開発者、運用チーム、ビジネスチーム向けに整理されています。

---

## 🚀 クイックアクセス

### 開発者向け
- [📖 開発者ガイド](./DEVELOPER_GUIDE.md) - 開発環境構築と開発フロー
- [🔧 セットアップガイド](./SETUP_GUIDE.md) - 初期環境構築手順
- [⚡ クイックスタート](./QUICK_START.md) - 最短での動作確認
- [📱 モバイルアプリ開発](../mobile-app/EXPO_SETUP.md) - Expo/React Native開発
- [✅ 実装ステータス](./IMPLEMENTATION_STATUS.md) - 実装済み/未実装機能一覧

### API・SDK
- [🔌 API リファレンス](./API_REFERENCE.md) - エンドポイント仕様
- [📦 SDK ガイド](./SDK_GUIDE.md) - 各言語SDK使用方法
- [🔐 認証フロー](./04_api_design/auth_flow_design.md)

### 運用・デプロイ
- [🚢 デプロイメントガイド](./DEPLOYMENT.md) - 本番環境デプロイ
- [📱 iOS公開ガイド](../mobile-app/IOS_DEPLOYMENT.md) - App Store公開手順

---

## 🎯 プロジェクト概要

**ToneBridge**は、エンジニアと非エンジニア間のコミュニケーションギャップを解消するAI駆動の文章変換プラットフォームです。

### 主要機能

- **7種類の変換モード**: Soften, Clarify, Structure, Summarize, Terminology, Requirements, Background
- **マルチプラットフォーム対応**: Slack, Teams, Discord, Outlook, Web, Mobile (iOS/Android)
- **リアルタイム変換**: WebSocket対応
- **自動変換**: ルールベース自動変換システム
- **MLファインチューニング**: カスタムモデル学習

### 技術スタック

- **API Gateway**: Golang (Fiber v2) - 30ms レスポンス (ポート 8082)
- **LLM Service**: Python (FastAPI + LangChain)
- **Real-time**: Socket.IO + Redis
- **Database**: PostgreSQL + pgvector
- **Cache**: L1 (LRU) + L2 (Redis)
- **Queue**: Asynq (Golang)
- **Mobile**: React Native + Expo SDK 49

## 📊 パフォーマンス指標

| メトリクス | 値 |
|-----------|-----|
| API レスポンス (p50) | 30ms |
| API レスポンス (p99) | 150ms |
| 同時接続数 | 15,000+ |
| スループット | 5,000 rps |
| メモリ使用量 | 400MB/インスタンス |
| キャッシュヒット率 | 85% |

---

## 📂 ドキュメントカテゴリー

### 01. 要件定義
プロジェクトのビジョン、機能要件、非機能要件など基本的な要件定義

- [ビジョンとコンセプト](./01_requirements/vision_and_concept.md)
- [機能要件](./01_requirements/functional_requirements.md)
- [非機能要件](./01_requirements/nonfunctional_requirements.md)
- [制約事項](./01_requirements/constraints.md)
- [実装ロードマップ](./01_requirements/implementation_roadmap.md)

### 02. アーキテクチャ設計
システム全体の設計、コンポーネント構成、インフラ構成

- [システムアーキテクチャ](./02_architecture/system_architecture.md)
- [コンポーネント設計](./02_architecture/component_design.md)
- [インフラアーキテクチャ](./02_architecture/infrastructure_architecture.md)
- [サービス仕様書](./02_architecture/SERVICE_SPECIFICATION.md)
- [📊 アーキテクチャ概要](./ARCHITECTURE.md)
- [最適化アーキテクチャ](./optimized-architecture.md)

### 03. データ設計
データベース設計、APIレスポンススキーマ、データフロー

- [テーブル定義](./03_data_design/table_definitions.md)
- [ER図](./03_data_design/er_diagram.md)
- [データフロー図](./03_data_design/data_flow_diagram.md)
- [APIレスポンススキーマ](./03_data_design/api_response_schemas.md)

### 04. API設計
API仕様、エンドポイント設計、エラーハンドリング

- [API仕様](./04_api_design/api_specification.md)
- [リクエスト/レスポンス例](./04_api_design/api_request_response_examples.md)
- [認証フロー](./04_api_design/auth_flow_design.md)
- [エラーハンドリング](./04_api_design/error_handling.md)

### 05. セキュリティ・運用
認証認可、バックアップ、モニタリング戦略

- [認証・認可](./05_security_operations/authentication_authorization.md)
- [バックアップ・リカバリ](./05_security_operations/backup_and_recovery.md)
- [ロギング・モニタリング](./05_security_operations/logging_and_monitoring.md)

### 06. テスト設計
テスト戦略とテスト計画

- [テスト戦略](./06_test_design/test_strategy.md)

### 07. AI・機械学習
AI実装、モデル設計、評価指標

- [AI実装ガイド](./07_ai_resources/ai_implementation_guide.md)
- [モデル設計と選定](./07_ai_resources/model_design_and_selection.md)
- [評価指標](./07_ai_resources/evaluation_metrics.md)
- [データ前処理フロー](./07_ai_resources/data_preprocessing_flow.md)
- [コーチングAPI実装](./07_ai_resources/coaching_api_implementation.md)
- [プロンプトテンプレート](./07_ai_resources/prompt_templates.md)

### 08. 調査アーカイブ
技術調査、検証結果のアーカイブ

- [サンプル調査](./08_investigation_archive/sample_investigation.md)

### 09. 市場調査
競合分析、市場規模、ターゲット分析

- [競合分析](./09_market_research/competitor_analysis.md)
- [顧客ニーズ調査](./09_market_research/customer_needs_survey.md)
- [市場規模](./09_market_research/market_size.md)
- [ターゲット分析](./09_market_research/target_analysis.md)
- [トレンド予測](./09_market_research/trend_forecast.md)

### 10. 営業戦略
価格戦略、パートナーシップ、成長計画

- [ローンチキャンペーン計画](./10_sales_strategy/launch_campaign_plan.md)
- [パートナーシップ計画](./10_sales_strategy/partnership_plan.md)
- [価格戦略](./10_sales_strategy/pricing_strategy.md)
- [リテンション・成長計画](./10_sales_strategy/retention_growth_plan.md)
- [ユーザー獲得チャネル](./10_sales_strategy/user_acquisition_channels.md)

### 11. プロダクト計画
機能リスト、MVP範囲、リスク分析

- [機能リスト](./11_product_planning/feature_list.md)
- [MVP範囲](./11_product_planning/mvp_scope.md)
- [リスク分析](./11_product_planning/risk_analysis.md)
- [ユーザーストーリーマップ](./11_product_planning/user_story_map.md)
- [ワイヤーフレームコンセプト](./11_product_planning/wireframe_concept.md)

---

## 📈 プロジェクト進捗・レポート

開発進捗とマイルストーン達成記録 - [📊 進捗レポート一覧](./progress/README.md)

- [Phase 2 完了報告](./progress/PHASE2_COMPLETION.md)
- [Phase 3 進捗](./phase3-progress.md)
- [プロジェクトサマリー](./progress/PROJECT_SUMMARY.md)
- [成果報告](./progress/ACHIEVEMENT_REPORT.md)
- [クイックスタート成功事例](./progress/QUICKSTART_SUCCESS.md)
- [プレビューモード実装](./progress/PREVIEW_MODE.md)
- [ML トレーニング実装](./progress/ML_TRAINING_IMPLEMENTATION.md)
- [モバイルアプリExpo対応](./progress/MOBILE_APP_EXPO.md)

---

## 🛠️ 開発ツール

### Make コマンド
```bash
make help           # ヘルプ表示
make setup          # 初期セットアップ
make up             # サービス起動
make test           # テスト実行
make build-prod     # 本番ビルド
```

### Docker 操作
```bash
cd infrastructure
docker-compose up -d    # サービス起動
docker-compose logs -f  # ログ確認
docker-compose down     # サービス停止
```

### モバイルアプリ開発
```bash
cd mobile-app
npm install             # 依存関係インストール
npm start              # Expo起動
eas build --platform ios  # iOSビルド
```

---

## 📂 ディレクトリ構造

```
docs/
├── README.md              # このファイル
├── QUICK_START.md        # クイックスタートガイド
├── SETUP_GUIDE.md        # セットアップガイド
├── DEVELOPER_GUIDE.md    # 開発者ガイド
├── ARCHITECTURE.md       # アーキテクチャ設計書
├── API_REFERENCE.md      # API詳細仕様
├── SDK_GUIDE.md          # SDK使用ガイド
├── DEPLOYMENT.md         # デプロイメントガイド
├── optimized-architecture.md  # 最適化アーキテクチャ詳細
├── phase3-progress.md    # Phase 3進捗
├── progress/             # 進捗レポート
│   ├── README.md
│   ├── PHASE2_COMPLETION.md
│   ├── PROJECT_SUMMARY.md
│   ├── ACHIEVEMENT_REPORT.md
│   ├── QUICKSTART_SUCCESS.md
│   ├── PREVIEW_MODE.md
│   ├── ML_TRAINING_IMPLEMENTATION.md
│   └── MOBILE_APP_EXPO.md
├── 01_requirements/      # 要件定義
├── 02_architecture/      # 詳細設計ドキュメント
├── 03_data_design/       # データベース設計
├── 04_api_design/        # API設計詳細
├── 05_security_operations/  # セキュリティガイド
├── 06_test_design/       # テスト設計
├── 07_ai_resources/      # AI/LLM設定リソース
├── 08_investigation_archive/  # 調査アーカイブ
├── 09_market_research/   # 市場調査
├── 10_sales_strategy/    # 営業戦略
└── 11_product_planning/  # プロダクト計画
```

---

## 📝 ドキュメント規約

### ファイル命名規則
- 英語、小文字、アンダースコア区切り
- 例: `api_specification.md`

### ディレクトリ構成
- 番号プレフィックスでカテゴリー分類
- 例: `01_requirements/`, `02_architecture/`

### テンプレート
各カテゴリーに `_template_*.md` ファイルを配置

---

## 🔗 関連リンク

### 内部ドキュメント
- [メインREADME](../README.md) - プロジェクト概要
- [CLAUDE.md](../CLAUDE.md) - Claude Code向けガイド

### 外部リソース
- [Expo Documentation](https://docs.expo.dev/)
- [React Native Docs](https://reactnative.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [LangChain Documentation](https://docs.langchain.com/)
- [Fiber Documentation](https://docs.gofiber.io/)

---

## 📝 バージョン情報

- **Current Version**: 3.0.0
- **Release Date**: 2024-01
- **Status**: Production Ready
- **最終更新**: 2024年12月

## 📞 サポート

- Issues: [GitHub Issues](https://github.com/tonebridge/issues)
- Email: support@tonebridge.io
- Documentation: このリポジトリ

---

© 2024 ToneBridge. All rights reserved.