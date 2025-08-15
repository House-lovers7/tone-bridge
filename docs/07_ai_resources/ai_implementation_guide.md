# AI実装ガイド

## 1. 概要

ToneBridgeのAI実装は、LangChainフレームワークを基盤として、複数のLLMプロバイダー（OpenAI、Anthropic、Google）をサポートする柔軟な設計となっています。本ガイドでは、AI機能の実装詳細、プロンプトエンジニアリング、最適化手法について説明します。

## 2. アーキテクチャ

### 2.1 全体構成

```
┌──────────────────────────────────────────────────────┐
│                   API Gateway                         │
│                  (Request Router)                     │
└──────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────┐
│                  LLM Service Layer                    │
│  ┌────────────────────────────────────────────────┐  │
│  │            LangChain Framework                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐      │  │
│  │  │  Chains  │ │ Prompts  │ │  Memory  │      │  │
│  │  └──────────┘ └──────────┘ └──────────┘      │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  OpenAI  │ │Anthropic │ │  Google  │
        │  GPT-4   │ │  Claude  │ │  Gemini  │
        └──────────┘ └──────────┘ └──────────┘
```

### 2.2 コンポーネント説明

- **LangChain Framework**: チェーン管理、プロンプトテンプレート、メモリ管理
- **Multi-Provider Support**: 複数のLLMプロバイダーを動的に切り替え
- **Cache Layer**: Redis/In-memoryキャッシュによる応答高速化
- **Fallback Mechanism**: プライマリLLM障害時の自動フォールバック

## 3. 変換チェーン実装

### 3.1 Tone Transformation Chain

```python
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

class ToneTransformationChain:
    """文体変換チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text", "target_tone", "intensity_level"],
            template="""
You are an expert communication specialist helping to bridge the gap between engineers and non-engineers.

Transform the following text to have a {target_tone} tone with intensity level {intensity_level} (1=subtle, 2=moderate, 3=strong) while preserving the core message and intent.

Target tone descriptions:
- warm: 温かみのある、配慮のある表現。相手への感謝と敬意を示す
- professional: プロフェッショナルで洗練された表現
- casual: カジュアルで親しみやすい表現
- technical: 技術的で正確な表現
- executive: エグゼクティブ向けの簡潔で戦略的な表現

Original text:
{text}

Transformed text:
"""
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            max_tokens=2000
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    async def transform(self, text: str, target_tone: str, intensity_level: int) -> dict:
        """テキストを変換"""
        result = await self.chain.ainvoke({
            "text": text,
            "target_tone": target_tone,
            "intensity_level": intensity_level
        })
        
        return {
            "transformed_text": result["text"],
            "metadata": {
                "model": "gpt-4-turbo-preview",
                "tone": target_tone,
                "intensity": intensity_level
            }
        }
```

### 3.2 Structure Transformation Chain

```python
class StructureTransformationChain:
    """構造化変換チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template="""
あなたは文章構造化の専門家です。以下のテキストを構造化して、読みやすく整理してください。

構造化の原則:
1. 要点を明確に抽出
2. 論理的な順序で配置
3. 箇条書きや番号付きリストを活用
4. 段落を適切に分割
5. 見出しを追加（必要に応じて）

元のテキスト:
{text}

構造化されたテキスト:
"""
        )
```

### 3.3 Summarization Chain

```python
class SummarizationChain:
    """要約チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text", "max_length"],
            template="""
以下のテキストを{max_length}文字以内で要約してください。

要約の原則:
1. 最も重要な情報を優先
2. 具体的な数値や固有名詞は保持
3. アクションアイテムは必ず含める
4. 技術的な正確性を維持

元のテキスト:
{text}

要約:
"""
        )
```

### 3.4 Terminology Chain

```python
class TerminologyChain:
    """専門用語変換チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text", "domain", "dictionary"],
            template="""
以下のテキストの専門用語を、非エンジニアにも理解しやすい表現に変換してください。

ドメイン: {domain}
カスタム辞書: {dictionary}

変換原則:
1. 専門用語には簡潔な説明を追加
2. 略語は初出時にフルスペルを併記
3. 技術的な概念は日常的な例えで説明
4. 重要な用語は太字や強調表示を提案

元のテキスト:
{text}

変換後のテキスト:
"""
        )
```

## 4. 分析チェーン実装

### 4.1 Tone Analysis Chain

```python
class ToneAnalysisChain:
    """トーン分析チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template="""
以下のテキストのトーンと感情を分析してください。

分析項目:
1. 全体的なトーン（urgent, friendly, formal, casual, technical, emotional）
2. 感情スコア（-1.0〜1.0）
3. 緊急度（low, medium, high, critical）
4. 明瞭度（0.0〜1.0）
5. 配慮レベル（0.0〜1.0）

テキスト:
{text}

JSON形式で出力:
{
    "tone": "",
    "emotion_score": 0.0,
    "urgency": "",
    "clarity": 0.0,
    "consideration": 0.0,
    "reasoning": ""
}
"""
        )
```

### 4.2 Structure Analysis Chain

```python
class StructureAnalysisChain:
    """構造分析チェーン"""
    
    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template="""
以下のテキストの構造を分析してください。

分析項目:
1. 構造化レベル（poor, fair, good, excellent）
2. 段落数
3. 文章数
4. アクションアイテムの有無
5. 期限の明記有無
6. 改善提案

テキスト:
{text}

JSON形式で出力:
{
    "structure_level": "",
    "paragraph_count": 0,
    "sentence_count": 0,
    "has_action_items": false,
    "has_deadline": false,
    "improvement_suggestions": []
}
"""
        )
```

## 5. プロンプトエンジニアリング

### 5.1 ベストプラクティス

#### 1. 明確な指示

```python
# 良い例
prompt = """
あなたはコミュニケーション専門家です。
以下のルールに従ってテキストを変換してください：
1. 元の意味を保持
2. 温かみのある表現を使用
3. 感謝の言葉を追加
"""

# 悪い例
prompt = "テキストを優しく変換してください"
```

#### 2. Few-Shot Learning

```python
prompt = PromptTemplate(
    input_variables=["text"],
    template="""
以下の例を参考に、テキストを変換してください。

例1:
入力: "バグを直してください"
出力: "お手数ですが、バグの修正をお願いできますでしょうか"

例2:
入力: "締切は明日です"
出力: "明日が締切となっておりますので、ご確認いただければ幸いです"

入力: {text}
出力:
"""
)
```

#### 3. Chain of Thought

```python
prompt = PromptTemplate(
    input_variables=["text"],
    template="""
ステップバイステップで考えてください：

1. まず、テキストの主要な意図を特定
2. 次に、現在のトーンを分析
3. 目標トーンとのギャップを特定
4. 適切な変換を適用

テキスト: {text}

思考プロセス:
1. 主要な意図: [ここに記入]
2. 現在のトーン: [ここに記入]
3. ギャップ: [ここに記入]
4. 変換結果: [ここに記入]
"""
)
```

### 5.2 プロンプト最適化

#### 動的プロンプト調整

```python
class DynamicPromptOptimizer:
    """コンテキストに基づいてプロンプトを動的に調整"""
    
    def optimize_prompt(self, base_prompt: str, context: dict) -> str:
        # テキスト長に基づく調整
        if context.get("text_length", 0) > 500:
            base_prompt += "\n注意: 長文のため、要点を保持しながら簡潔に。"
        
        # ドメインに基づく調整
        if context.get("domain") == "technical":
            base_prompt += "\n技術的な正確性を特に重視してください。"
        
        # 緊急度に基づく調整
        if context.get("urgency") == "high":
            base_prompt += "\n緊急性を適切に伝える表現を使用してください。"
        
        return base_prompt
```

## 6. モデル選択戦略

### 6.1 タスク別モデル選択

| タスク | 推奨モデル | 理由 |
|--------|-----------|------|
| 文体変換 | GPT-4 Turbo | 高い文脈理解能力と自然な文章生成 |
| 要約 | Claude 3 | 長文処理能力と正確な要約 |
| 構造化 | GPT-4 | 論理的思考と構造認識 |
| 専門用語変換 | Gemini Pro | 広範な知識ベース |
| リアルタイム変換 | GPT-3.5 Turbo | 高速レスポンス |

### 6.2 フォールバック戦略

```python
class ModelFallbackStrategy:
    """モデル障害時のフォールバック戦略"""
    
    def __init__(self):
        self.models = [
            {"provider": "openai", "model": "gpt-4-turbo-preview", "priority": 1},
            {"provider": "anthropic", "model": "claude-3-opus", "priority": 2},
            {"provider": "google", "model": "gemini-pro", "priority": 3},
            {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 4}
        ]
    
    async def execute_with_fallback(self, task: callable, *args, **kwargs):
        for model_config in sorted(self.models, key=lambda x: x["priority"]):
            try:
                result = await task(model_config, *args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"Model {model_config['model']} failed: {e}")
                continue
        
        raise Exception("All models failed")
```

## 7. パフォーマンス最適化

### 7.1 キャッシング戦略

```python
class TransformationCache:
    """変換結果のキャッシング"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 86400  # 24時間
    
    def generate_key(self, text: str, params: dict) -> str:
        """キャッシュキーの生成"""
        content = f"{text}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get_or_transform(self, text: str, params: dict, transform_func):
        key = self.generate_key(text, params)
        
        # キャッシュチェック
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # 変換実行
        result = await transform_func(text, **params)
        
        # キャッシュ保存
        await self.redis.setex(key, self.ttl, json.dumps(result))
        
        return result
```

### 7.2 バッチ処理

```python
class BatchProcessor:
    """バッチ処理による効率化"""
    
    async def process_batch(self, texts: List[str], transform_func):
        """複数テキストの並列処理"""
        tasks = [transform_func(text) for text in texts]
        results = await asyncio.gather(*tasks)
        return results
```

### 7.3 ストリーミング対応

```python
class StreamingTransformer:
    """ストリーミング変換"""
    
    async def stream_transform(self, text: str, callback):
        """チャンク単位でのストリーミング処理"""
        async for chunk in self.llm.astream(text):
            await callback(chunk)
```

## 8. 評価メトリクス

### 8.1 品質メトリクス

| メトリクス | 説明 | 目標値 |
|-----------|------|--------|
| BLEU Score | 変換品質 | > 0.7 |
| Perplexity | 文章の自然さ | < 50 |
| Semantic Similarity | 意味の保持 | > 0.85 |
| Tone Accuracy | トーン変換の正確性 | > 90% |
| User Satisfaction | ユーザー満足度 | > 4.5/5 |

### 8.2 パフォーマンスメトリクス

| メトリクス | 説明 | 目標値 |
|-----------|------|--------|
| Response Time (p50) | 中央値レスポンス時間 | < 500ms |
| Response Time (p99) | 99パーセンタイル | < 2000ms |
| Throughput | 処理能力 | > 100 req/s |
| Cache Hit Rate | キャッシュヒット率 | > 40% |
| Error Rate | エラー率 | < 0.1% |

### 8.3 評価実装

```python
class TransformationEvaluator:
    """変換品質の評価"""
    
    def evaluate_transformation(self, original: str, transformed: str, expected: str):
        metrics = {}
        
        # BLEU Score
        metrics["bleu"] = self.calculate_bleu(transformed, expected)
        
        # Semantic Similarity
        metrics["similarity"] = self.calculate_similarity(original, transformed)
        
        # Tone Classification
        metrics["tone_accuracy"] = self.check_tone_accuracy(transformed)
        
        # Readability
        metrics["readability"] = self.calculate_readability(transformed)
        
        return metrics
```

## 9. A/Bテスト実装

### 9.1 実験フレームワーク

```python
class ABTestFramework:
    """A/Bテストフレームワーク"""
    
    def __init__(self):
        self.experiments = {}
    
    def create_experiment(self, name: str, variants: List[dict]):
        """実験の作成"""
        self.experiments[name] = {
            "variants": variants,
            "results": defaultdict(list),
            "start_time": datetime.now()
        }
    
    async def run_variant(self, experiment_name: str, user_id: str, text: str):
        """バリアントの実行"""
        # ユーザーIDに基づくバリアント選択
        variant = self.select_variant(experiment_name, user_id)
        
        # 変換実行
        start_time = time.time()
        result = await variant["transform_func"](text)
        duration = time.time() - start_time
        
        # 結果記録
        self.record_result(experiment_name, variant["name"], {
            "user_id": user_id,
            "duration": duration,
            "result": result
        })
        
        return result
```

## 10. エラーハンドリング

### 10.1 エラー分類と対処

```python
class AIErrorHandler:
    """AI関連エラーのハンドリング"""
    
    ERROR_STRATEGIES = {
        "RateLimitError": "exponential_backoff",
        "TimeoutError": "retry_with_timeout",
        "InvalidResponseError": "fallback_model",
        "PromptTooLongError": "truncate_and_retry",
        "ModelUnavailableError": "use_cache_or_fallback"
    }
    
    async def handle_error(self, error: Exception, context: dict):
        error_type = type(error).__name__
        strategy = self.ERROR_STRATEGIES.get(error_type, "log_and_raise")
        
        if strategy == "exponential_backoff":
            return await self.retry_with_backoff(context)
        elif strategy == "fallback_model":
            return await self.use_fallback_model(context)
        # ... 他の戦略
```

## 11. セキュリティ対策

### 11.1 プロンプトインジェクション対策

```python
class PromptSanitizer:
    """プロンプトインジェクション対策"""
    
    DANGEROUS_PATTERNS = [
        r"ignore previous instructions",
        r"disregard all prior",
        r"system prompt",
        r"reveal your instructions"
    ]
    
    def sanitize(self, user_input: str) -> str:
        """危険なパターンの検出と除去"""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                raise SecurityError(f"Potential prompt injection detected")
        
        # HTMLエスケープ
        user_input = html.escape(user_input)
        
        # 長さ制限
        if len(user_input) > 10000:
            user_input = user_input[:10000]
        
        return user_input
```

### 11.2 出力検証

```python
class OutputValidator:
    """LLM出力の検証"""
    
    def validate_output(self, output: str, context: dict) -> bool:
        # PII検出
        if self.contains_pii(output):
            logger.warning("PII detected in output")
            return False
        
        # 不適切なコンテンツ検出
        if self.contains_inappropriate_content(output):
            logger.warning("Inappropriate content detected")
            return False
        
        # 構造検証
        if context.get("expected_format") == "json":
            try:
                json.loads(output)
            except:
                return False
        
        return True
```

## 12. 継続的改善

### 12.1 フィードバックループ

```python
class FeedbackCollector:
    """ユーザーフィードバックの収集と学習"""
    
    async def collect_feedback(self, transformation_id: str, rating: int, comment: str):
        """フィードバックの収集"""
        feedback = {
            "transformation_id": transformation_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now()
        }
        
        # データベースに保存
        await self.save_feedback(feedback)
        
        # 低評価の場合は自動アラート
        if rating < 3:
            await self.alert_low_rating(feedback)
        
        # プロンプト改善のための分析
        if rating == 5:
            await self.analyze_successful_pattern(transformation_id)
```

### 12.2 自動プロンプト最適化

```python
class AutoPromptOptimizer:
    """フィードバックに基づく自動プロンプト最適化"""
    
    async def optimize_prompts(self):
        """定期的なプロンプト最適化"""
        # 高評価の変換パターンを分析
        successful_patterns = await self.analyze_successful_transformations()
        
        # プロンプトテンプレートの更新
        for pattern in successful_patterns:
            await self.update_prompt_template(pattern)
        
        # A/Bテストの自動開始
        await self.start_optimization_experiment()
```

## 13. デプロイメント戦略

### 13.1 モデルバージョニング

```python
class ModelVersionManager:
    """モデルバージョン管理"""
    
    def __init__(self):
        self.versions = {
            "stable": "gpt-4-0613",
            "latest": "gpt-4-turbo-preview",
            "experimental": "gpt-4-vision-preview"
        }
    
    def get_model(self, version_tag: str = "stable"):
        return self.versions.get(version_tag, self.versions["stable"])
```

### 13.2 カナリアデプロイメント

```python
class CanaryDeployment:
    """段階的なモデルロールアウト"""
    
    def __init__(self):
        self.canary_percentage = 5  # 5%のトラフィックを新モデルへ
    
    def should_use_canary(self, user_id: str) -> bool:
        """カナリアモデルを使用するか判定"""
        hash_value = hashlib.md5(user_id.encode()).hexdigest()
        return int(hash_value, 16) % 100 < self.canary_percentage
```

## 14. まとめ

ToneBridgeのAI実装は、以下の要素により高品質なテキスト変換を実現しています：

1. **柔軟なアーキテクチャ**: 複数のLLMプロバイダーをサポート
2. **最適化されたプロンプト**: タスク特化型のプロンプトエンジニアリング
3. **パフォーマンス最適化**: キャッシング、バッチ処理、ストリーミング
4. **継続的改善**: フィードバックループとA/Bテスト
5. **セキュリティ**: プロンプトインジェクション対策と出力検証

今後も、新しいモデルの統合、プロンプトの改善、パフォーマンスの最適化を継続的に行い、より良いユーザー体験を提供していきます。