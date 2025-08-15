# プロンプトテンプレート集

## 1. 概要

本ドキュメントは、ToneBridgeで使用するプロンプトテンプレートを集約したものです。各プロンプトは実際の運用を通じて最適化され、高品質な変換結果を生成するよう設計されています。

## 2. 文体変換プロンプト

### 2.1 基本文体変換

```
You are an expert communication specialist helping to bridge the gap between engineers and non-engineers in Japanese business environments.

Transform the following Japanese text to have a {target_tone} tone with intensity level {intensity_level} while preserving the core message and intent.

Intensity levels:
- 1 (subtle): Minimal changes, gentle adjustments
- 2 (moderate): Clear transformation while maintaining professionalism
- 3 (strong): Significant transformation for maximum effect

Target tone: {target_tone}
Intensity: {intensity_level}

Original text:
{text}

Rules:
1. Preserve all technical accuracy and factual information
2. Maintain the original intent and key messages
3. Adjust formality and emotional tone appropriately
4. Use natural Japanese expressions
5. Keep technical terms when necessary, but add explanations if helpful

Transformed text:
```

### 2.2 温かみのある表現への変換

```
あなたは日本のビジネスコミュニケーションの専門家です。

以下のテキストを、相手への配慮と感謝の気持ちが伝わる温かみのある表現に変換してください。

変換の原則:
1. 命令形を依頼形に変更（〜してください → 〜していただけますでしょうか）
2. 感謝の言葉を追加（お忙しい中恐れ入りますが、ありがとうございます）
3. クッション言葉を使用（恐れ入りますが、お手数ですが）
4. 相手の立場を考慮した表現（ご都合の良い時に、お時間のある時に）
5. 柔らかい語尾を使用（〜です → 〜ですね、〜でしょうか）

強度レベル: {intensity_level}
- レベル1: 最小限の調整、基本的な敬語の追加
- レベル2: 明確な配慮表現、適度なクッション言葉
- レベル3: 最大限の配慮、丁寧な前置きと感謝の表現

元のテキスト:
{text}

変換後のテキスト:
```

### 2.3 プロフェッショナル表現への変換

```
Transform the following text into a professional business communication style suitable for Japanese corporate environments.

Professional transformation guidelines:
1. Use formal business Japanese (敬語・謙譲語)
2. Structure information clearly with appropriate transitions
3. Remove casual expressions and emotional language
4. Add professional context where appropriate
5. Ensure clarity and precision in all statements

Original text:
{text}

Professional version:
```

### 2.4 エグゼクティブ向け変換

```
あなたは経営層向けのコミュニケーション専門家です。

以下のテキストを、エグゼクティブ向けの簡潔で戦略的な表現に変換してください。

変換原則:
1. 要点を最初に提示（結論ファースト）
2. 数値とインパクトを強調
3. 戦略的な視点を追加
4. 不要な詳細を削除
5. アクションアイテムを明確化
6. ビジネスインパクトを強調

元のテキスト:
{text}

エグゼクティブサマリー:
```

## 3. 構造化プロンプト

### 3.1 基本構造化

```
あなたは文章構造化の専門家です。

以下の日本語テキストを、論理的で読みやすい構造に整理してください。

構造化の手順:
1. 主要なポイントを特定
2. 情報を論理的な順序で配置
3. 適切な見出しを追加
4. 箇条書きや番号付きリストを活用
5. 段落を適切に分割
6. 接続詞や移行句を追加して流れを改善

元のテキスト:
{text}

構造化されたテキスト:
```

### 3.2 ビジネス文書構造化

```
以下のテキストをビジネス文書として適切に構造化してください。

ビジネス文書の構造:
1. 件名/タイトル
2. 概要（1-2文）
3. 背景・経緯
4. 主要内容
   - ポイント1
   - ポイント2
   - ポイント3
5. 今後の対応/アクションアイテム
6. 期限・スケジュール
7. 補足事項（必要に応じて）

元のテキスト:
{text}

構造化された文書:
```

### 3.3 技術文書構造化

```
Transform the following technical content into a well-structured technical document.

Technical document structure:
1. Overview/Abstract
2. Problem Statement
3. Proposed Solution
4. Technical Details
   - Architecture
   - Implementation
   - Dependencies
5. Testing/Validation
6. Deployment Considerations
7. Future Improvements

Original text:
{text}

Structured technical document:
```

## 4. 要約プロンプト

### 4.1 基本要約

```
以下のテキストを{max_length}文字以内で要約してください。

要約の原則:
1. 最も重要な情報を優先
2. 具体的な数値や日付を保持
3. アクションアイテムは必ず含める
4. 技術的な正確性を維持
5. 因果関係を明確に示す

元のテキスト:
{text}

要約（{max_length}文字以内）:
```

### 4.2 エグゼクティブサマリー作成

```
Create an executive summary of the following content for senior management.

Executive summary requirements:
1. Maximum 3 bullet points
2. Focus on business impact and strategic implications
3. Include key metrics and KPIs
4. Highlight critical decisions needed
5. Specify timeline and resource requirements

Original content:
{text}

Executive Summary:
• [Key Point 1]
• [Key Point 2]  
• [Key Point 3]

Required Action: [Specific action needed]
Timeline: [Deadline or timeframe]
```

### 4.3 技術要約

```
技術的な内容を非エンジニアにも理解できるように要約してください。

要約のガイドライン:
1. 専門用語は平易な言葉で説明
2. 技術的な詳細は最小限に
3. ビジネスへの影響を強調
4. 具体的な例やメタファーを使用
5. 次のステップを明確に

技術的内容:
{text}

非技術者向け要約:
```

## 5. 専門用語変換プロンプト

### 5.1 技術用語の説明

```
以下のテキストに含まれる技術用語を、非エンジニアにも理解できるように説明を追加してください。

変換ルール:
1. 略語は初出時にフルスペルと日本語訳を併記
   例: API (Application Programming Interface, アプリケーション間の接続仕組み)
2. 専門用語には簡潔な説明を括弧内に追加
3. 複雑な概念は日常的な例えで説明
4. 重要な用語は強調表示を提案

カスタム辞書:
{dictionary}

元のテキスト:
{text}

変換後のテキスト:
```

### 5.2 ビジネス用語への変換

```
Transform technical jargon into business-friendly language.

Transformation guidelines:
1. Replace technical terms with business equivalents
2. Focus on business value rather than technical details
3. Use outcome-oriented language
4. Maintain accuracy while improving accessibility
5. Add context for better understanding

Technical text:
{text}

Business-friendly version:
```

## 6. 分析プロンプト

### 6.1 トーン分析

```
以下のテキストのトーンと感情を詳細に分析してください。

分析項目:
1. 全体的なトーン（urgent/friendly/formal/casual/technical/emotional）
2. 感情スコア（-1.0 to 1.0）
3. 緊急度（low/medium/high/critical）
4. 明瞭度スコア（0.0 to 1.0）
5. 配慮レベル（0.0 to 1.0）
6. 改善提案

テキスト:
{text}

分析結果をJSON形式で出力:
{
    "tone": "",
    "emotion_score": 0.0,
    "urgency": "",
    "clarity": 0.0,
    "consideration": 0.0,
    "improvement_suggestions": [],
    "reasoning": ""
}
```

### 6.2 構造分析

```
Analyze the structure and organization of the following text.

Analysis criteria:
1. Structure level (poor/fair/good/excellent)
2. Logical flow and coherence
3. Paragraph organization
4. Presence of action items
5. Clarity of main points
6. Suggestions for improvement

Text:
{text}

Structural analysis (JSON format):
{
    "structure_level": "",
    "logical_flow": 0.0,
    "paragraph_count": 0,
    "sentence_count": 0,
    "has_action_items": false,
    "has_deadline": false,
    "main_points": [],
    "improvement_suggestions": []
}
```

### 6.3 優先度判定

```
以下のメッセージの優先度と対応の緊急性を判定してください。

判定基準:
1. 明示的な期限の有無
2. 影響範囲（個人/チーム/組織/顧客）
3. リスクレベル
4. 感情的な緊急性の表現
5. ビジネスインパクト

メッセージ:
{text}

優先度判定（JSON形式）:
{
    "priority": "low/medium/high/critical",
    "has_deadline": false,
    "deadline": null,
    "impact_scope": "",
    "risk_level": "",
    "business_impact": "",
    "recommended_response_time": "",
    "reasoning": ""
}
```

## 7. 特殊ケース用プロンプト

### 7.1 謝罪文作成

```
以下の状況に対する適切な謝罪文を作成してください。

謝罪文の要素:
1. 真摯な謝罪の表明
2. 問題の認識と責任の受け入れ
3. 原因の簡潔な説明（言い訳にならないよう注意）
4. 再発防止策の提示
5. 今後の対応についての約束

状況:
{situation}

謝罪文:
```

### 7.2 感謝文作成

```
Create a thoughtful thank-you message for the following situation.

Thank-you message components:
1. Specific acknowledgment of what you're thankful for
2. Recognition of effort or impact
3. Personal touch or specific detail
4. Future collaboration mention (if appropriate)
5. Warm closing

Situation:
{situation}

Thank-you message:
```

### 7.3 フィードバック文作成

```
以下の内容について、建設的なフィードバックを作成してください。

フィードバックの原則:
1. ポジティブな点から始める
2. 具体的な改善点を提示
3. 改善提案は実行可能なものに
4. 励ましと期待を込めて締める
5. 個人攻撃にならないよう配慮

フィードバック対象:
{content}

建設的フィードバック:
```

## 8. コンテキスト対応プロンプト

### 8.1 チャット/メッセージング用

```
Transform the following text for chat/messaging platforms (Slack, Teams, etc.).

Chat optimization:
1. Keep it concise and scannable
2. Use bullet points for multiple items
3. Add appropriate emojis sparingly (Japanese business context)
4. Break long messages into logical chunks
5. Include clear call-to-action

Original text:
{text}

Chat-optimized version:
```

### 8.2 メール用

```
以下の内容を正式なビジネスメールとして作成してください。

メールの構成:
1. 件名（明確で具体的）
2. 宛名と挨拶
3. 用件の概要（1-2文）
4. 詳細内容
5. 依頼事項や次のアクション
6. 期限
7. 結びの言葉
8. 署名

内容:
{content}

ビジネスメール:
件名: 
本文:
```

### 8.3 プレゼンテーション用

```
Convert the following content into presentation-ready bullet points.

Presentation format:
1. Maximum 5 bullet points per slide
2. Each point maximum 2 lines
3. Use action verbs
4. Include key metrics
5. Visual suggestions where appropriate

Content:
{content}

Slide content:
[Slide Title]
• Point 1
• Point 2
• Point 3
• Point 4
• Point 5

[Speaker notes]:
```

## 9. 多言語対応プロンプト

### 9.1 日英変換時の注意

```
Translate and adapt the following Japanese business text to English, considering cultural differences.

Translation guidelines:
1. Adapt honorifics and politeness levels appropriately
2. Convert indirect expressions to more direct ones for English
3. Maintain professional tone
4. Adjust cultural references
5. Preserve technical accuracy

Japanese text:
{text}

English adaptation:
```

### 9.2 英日変換時の注意

```
以下の英文を、日本のビジネス文化に適した日本語に翻訳・適応してください。

翻訳・適応のガイドライン:
1. 適切な敬語レベルを選択
2. 直接的すぎる表現を柔らかく
3. 日本のビジネス慣習に合わせた表現
4. カタカナ語と日本語のバランス
5. 文化的なニュアンスの調整

英文:
{text}

日本語版:
```

## 10. プロンプトチェーンテンプレート

### 10.1 複雑な変換チェーン

```python
# Step 1: 分析
analysis_prompt = """
まず、以下のテキストを分析してください:
{text}

分析項目:
- 現在のトーン
- 主要メッセージ
- 改善が必要な点
"""

# Step 2: 変換計画
planning_prompt = """
分析結果: {analysis_result}

この分析に基づいて、以下の変換計画を立ててください:
- 変換の優先順位
- 適用する変換タイプ
- 期待される結果
"""

# Step 3: 実行
execution_prompt = """
変換計画: {plan}

計画に従って、以下のテキストを変換してください:
{text}

変換後:
"""

# Step 4: 検証
validation_prompt = """
元のテキスト: {original}
変換後: {transformed}

変換の品質を評価し、必要に応じて微調整してください:
"""
```

### 10.2 段階的改善チェーン

```
# Phase 1: 基本変換
Perform basic tone transformation

# Phase 2: 構造最適化
Optimize structure and flow

# Phase 3: 専門用語調整
Adjust technical terminology

# Phase 4: 最終調整
Final polish and consistency check
```

## 11. プロンプト最適化ガイドライン

### 11.1 パフォーマンス最適化

1. **明確な指示**: 曖昧さを避け、具体的な指示を提供
2. **例示の活用**: Few-shot learningで品質向上
3. **構造化**: 番号付きリストや見出しで整理
4. **制約の明示**: 文字数、形式、トーンなどの制約を明確に
5. **出力形式の指定**: JSON、箇条書きなど期待する形式を指定

### 11.2 品質向上テクニック

1. **Chain of Thought**: 段階的思考プロセスの明示
2. **Role Assignment**: 専門家としての役割を明確に定義
3. **Context Provision**: 必要な背景情報を提供
4. **Error Prevention**: よくある間違いを事前に警告
5. **Feedback Loop**: 出力の自己評価を要求

### 11.3 デバッグ用プロンプト

```
Debug the transformation:

Original: {original}
Transformed: {transformed}
Expected: {expected}

Identify issues:
1. What was lost in transformation?
2. What was incorrectly changed?
3. What improvements are needed?

Corrected version:
```

## 12. プロンプトメンテナンス

### 12.1 バージョン管理

各プロンプトテンプレートには以下の情報を記録：

```yaml
template:
  id: "tone_transform_v2"
  version: "2.0.1"
  created: "2024-01-01"
  modified: "2024-01-15"
  author: "prompt_team"
  performance_score: 0.92
  usage_count: 10000
  average_rating: 4.5
```

### 12.2 A/Bテスト用バリエーション

```python
variants = {
    "control": "existing_prompt",
    "variant_a": "new_prompt_with_examples",
    "variant_b": "new_prompt_with_cot",
    "variant_c": "new_prompt_simplified"
}
```

### 12.3 プロンプト評価基準

1. **正確性**: 意図した変換が実行されているか
2. **一貫性**: 同じ入力に対して安定した出力
3. **効率性**: トークン使用量とコスト
4. **品質**: ユーザー満足度と評価
5. **速度**: レスポンスタイム

## まとめ

これらのプロンプトテンプレートは、ToneBridgeの中核となる変換機能を支えています。継続的な改善とA/Bテストを通じて、より高品質な変換結果を提供できるよう最適化を続けていきます。

各プロンプトは、日本のビジネス文化と国際的なコミュニケーションの両方を考慮し、エンジニアと非エンジニア間の効果的なコミュニケーションを実現するよう設計されています。