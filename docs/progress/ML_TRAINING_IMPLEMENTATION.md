# ML Training Service 実装ドキュメント

## 📋 概要
ToneBridge ML Training Serviceは、テキスト変換モデルのファインチューニング、評価、デプロイメントを管理する包括的な機械学習プラットフォームです。

## 🏗️ アーキテクチャ

### サービス構成
```
services/ml-training/
├── app/
│   ├── main.py                 # FastAPIアプリケーションエントリポイント
│   ├── config.py               # ✅ 実装済み - 環境設定管理
│   ├── database.py             # ✅ 実装済み - データベース接続管理
│   ├── models/
│   │   └── schemas.py          # ✅ 実装済み - Pydanticモデル定義
│   ├── services/
│   │   ├── model_trainer.py    # ⚠️ 部分実装 - モデルトレーニングロジック
│   │   ├── feedback_collector.py # ❌ 未実装
│   │   ├── model_evaluator.py  # ❌ 未実装
│   │   ├── ab_tester.py        # ❌ 未実装
│   │   └── model_registry.py   # ❌ 未実装
│   └── utils/
│       └── model_utils.py      # ❌ 未実装
├── requirements.txt            # 依存関係定義
└── Dockerfile                  # コンテナ設定
```

## 🔧 技術スタック

### 最新バージョン (2025年1月)
- **HuggingFace Transformers**: 4.36.0 → 4.47.1 (推奨アップグレード)
- **PEFT (LoRA)**: 0.7.0 → 0.17.0 (推奨アップグレード)
- **TRL (RLHF)**: 0.7.4
- **PyTorch**: 2.1.0
- **FastAPI**: 0.104.1
- **MLflow**: 2.9.0
- **Weights & Biases**: 0.16.1

### 互換性確認済み
✅ Transformers + PEFT統合は完全サポート
✅ LoRA/QLoRA実装は最新版で動作確認
✅ 8-bit/4-bit量子化サポート (bitsandbytes)

## 📊 データベーススキーマ

### テーブル構成

#### training_jobs
```sql
- id: String (Primary Key)
- model_type: String (tone_adjustment, structure, etc.)
- base_model: String (gpt-4, claude-3, gemini-pro, etc.)
- dataset_id: String (Foreign Key)
- status: String (pending, running, completed, failed)
- config: JSON
- hyperparameters: JSON
- progress: Float
- metrics: JSON
- error_message: Text
- created_at: DateTime
- started_at: DateTime
- completed_at: DateTime
```

#### models
```sql
- id: String (Primary Key)
- training_job_id: String (Foreign Key)
- name: String
- version: String
- model_type: String
- base_model: String
- path: String
- metrics: JSON
- status: String (draft, staging, production, archived)
- deployed_at: DateTime
- created_at: DateTime
```

#### datasets
```sql
- id: String (Primary Key)
- name: String
- description: Text
- type: String (training, validation, test, feedback)
- file_path: String
- format: String (json, csv, parquet, jsonl)
- size_mb: Float
- num_samples: Integer
- created_at: DateTime
```

#### feedback
```sql
- id: String (Primary Key)
- user_id: String
- session_id: String
- model_id: String (Foreign Key)
- input_text: Text
- output_text: Text
- corrected_text: Text
- transformation_type: String
- rating: Integer (1-5)
- feedback_type: String
- created_at: DateTime
```

#### ab_tests
```sql
- id: String (Primary Key)
- name: String
- model_a_id: String (Foreign Key)
- model_b_id: String (Foreign Key)
- traffic_split: Float
- success_metrics: JSON
- status: String (active, paused, completed)
- winner: String
- results: JSON
- created_at: DateTime
- completed_at: DateTime
```

## 🚀 API エンドポイント

### Training Management
- `POST /train` - トレーニングジョブ開始
- `GET /train/{job_id}/status` - ジョブステータス取得
- `POST /train/{job_id}/stop` - トレーニング停止

### Feedback Collection
- `POST /feedback` - フィードバック送信
- `GET /feedback/stats` - フィードバック統計

### Model Evaluation
- `POST /evaluate/{model_id}` - モデル評価実行
- `POST /evaluate/compare` - モデル比較

### A/B Testing
- `POST /ab-test` - A/Bテスト作成
- `GET /ab-test/{test_id}/results` - テスト結果取得
- `POST /ab-test/{test_id}/stop` - テスト停止

### Model Registry
- `GET /models` - モデル一覧
- `GET /models/{model_id}` - モデル詳細
- `POST /models/{model_id}/deploy` - モデルデプロイ
- `POST /models/{model_id}/rollback` - ロールバック

### RLHF (Reinforcement Learning from Human Feedback)
- `POST /rlhf/start` - RLHF開始
- `GET /rlhf/{job_id}/status` - RLHFステータス

## 🔑 環境変数

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=tonebridge
POSTGRES_PASSWORD=password
POSTGRES_DB=tonebridge_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=tonebridge-training

# Weights & Biases (Optional)
WANDB_API_KEY=your-api-key
WANDB_PROJECT=tonebridge
WANDB_ENTITY=your-entity

# Model Providers
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
HUGGINGFACE_TOKEN=your-token

# Training Configuration
DEFAULT_BATCH_SIZE=8
DEFAULT_LEARNING_RATE=5e-5
DEFAULT_EPOCHS=3
FP16_TRAINING=true
GRADIENT_CHECKPOINTING=true

# LoRA Configuration
LORA_R=8
LORA_ALPHA=32
LORA_DROPOUT=0.1
```

## 🎯 実装状況

### ✅ 完了
1. **config.py**: 環境設定管理
   - Pydantic Settingsによる型安全な設定
   - 環境変数の自動読み込み
   - ディレクトリ自動作成

2. **database.py**: データベース接続
   - SQLAlchemy Async ORM
   - AsyncPGによる高速接続
   - Redis統合
   - コネクションプール管理

3. **schemas.py**: データモデル定義
   - 完全な型定義
   - バリデーション規則
   - リクエスト/レスポンスモデル

### 🚧 実装中
4. **model_trainer.py**: トレーニングロジック
   - 基本構造実装済み
   - PEFT/LoRA統合必要
   - RLHFパイプライン構築中

### ❌ 未実装
5. **feedback_collector.py**: フィードバック収集
6. **model_evaluator.py**: モデル評価
7. **ab_tester.py**: A/Bテスト管理
8. **model_registry.py**: モデルレジストリ
9. **model_utils.py**: ユーティリティ関数

## 💡 実装のポイント

### LoRA実装
```python
from peft import LoraConfig, get_peft_model, TaskType

# LoRA設定
lora_config = LoraConfig(
    r=8,  # ランク
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    task_type=TaskType.CAUSAL_LM
)

# モデルにLoRAを適用
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 学習可能パラメータ: 0.19%
```

### RLHF実装
```python
from trl import PPOTrainer, PPOConfig

ppo_config = PPOConfig(
    batch_size=128,
    mini_batch_size=4,
    learning_rate=1e-5,
    kl_penalty=0.1
)

ppo_trainer = PPOTrainer(
    config=ppo_config,
    model=model,
    ref_model=ref_model,
    tokenizer=tokenizer
)
```

## 🔄 次のステップ

1. **残りのサービス実装**
   - FeedbackCollector
   - ModelEvaluator
   - ABTester
   - ModelRegistry

2. **データベースマイグレーション**
   - Alembicセットアップ
   - 初期マイグレーション作成

3. **テスト実装**
   - ユニットテスト
   - 統合テスト
   - 負荷テスト

4. **デプロイメント準備**
   - Dockerイメージ最適化
   - Kubernetes設定
   - CI/CDパイプライン

## 🐛 既知の問題

1. **GPU メモリ管理**
   - 大規模モデルのOOM対策必要
   - gradient_checkpointing推奨
   - 8-bit/4-bit量子化検討

2. **並列トレーニング**
   - DeepSpeed統合未完了
   - Accelerate設定必要

3. **モデルバージョニング**
   - DVC統合検討
   - S3/GCS対応必要

## 📚 参考資料

- [HuggingFace PEFT Documentation](https://huggingface.co/docs/peft)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

---

*Last Updated: 2025-01-15*
*Version: 0.3.0*
*Status: Development*