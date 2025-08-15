# 📦 ToneBridge SDK Guide

## 概要

ToneBridgeは主要プログラミング言語向けの公式SDKを提供しています。全SDKは統一されたインターフェースと一貫性のある使用体験を提供します。

## 🚀 JavaScript/TypeScript SDK

### インストール

```bash
npm install @tonebridge/sdk
# または
yarn add @tonebridge/sdk
# または
pnpm add @tonebridge/sdk
```

### 基本的な使い方

```typescript
import { ToneBridgeClient } from '@tonebridge/sdk';

// クライアントの初期化
const client = new ToneBridgeClient({
  apiKey: process.env.TONEBRIDGE_API_KEY,
  // または JWT認証
  token: process.env.TONEBRIDGE_TOKEN,
  baseURL: 'https://api.tonebridge.io', // オプション
  timeout: 5000, // オプション（ミリ秒）
  retries: 3, // オプション
});
```

### 変換機能

```typescript
// 基本的な変換
const result = await client.transform.soften(
  "This is totally unacceptable!",
  2 // intensity (1-3)
);
console.log(result.transformedText);
// Output: "This situation needs improvement."

// 詳細オプション付き変換
const detailedResult = await client.transform.execute({
  text: "Fix this bug immediately!",
  transformationType: 'soften',
  intensity: 2,
  context: {
    recipient: 'client',
    channel: 'email',
    metadata: {
      projectId: 'proj_123',
      priority: 'high'
    }
  }
});

// バッチ変換
const batchResult = await client.transform.batch([
  {
    text: "This is wrong!",
    transformationType: 'soften',
    intensity: 2
  },
  {
    text: "We need to implement user authentication, data validation, and error handling",
    transformationType: 'structure',
    intensity: 1
  }
]);

batchResult.results.forEach(item => {
  console.log(`Original: ${item.originalText}`);
  console.log(`Transformed: ${item.transformedText}`);
});
```

### 分析機能

```typescript
// テキスト分析
const analysis = await client.analyze.text(
  "We must implement this feature immediately or face serious consequences."
);

console.log(`Tone: ${analysis.tone.primary}`);
console.log(`Clarity Score: ${analysis.clarity.score}`);
console.log(`Suggestions:`, analysis.suggestions);

// 優先度スコアリング
const priorities = await client.analyze.priorities([
  {
    id: 'msg_1',
    text: 'Critical production bug affecting all users',
    sender: 'ops_team'
  },
  {
    id: 'msg_2',
    text: 'New feature request from sales',
    sender: 'sales'
  }
]);

priorities.rankedMessages.forEach(msg => {
  console.log(`${msg.id}: Priority ${msg.priorityScore}`);
});
```

### 高度な機能

```typescript
// 要件構造化
const requirements = await client.advanced.structureRequirements(
  "We need better performance, modern UI, and mobile support. Also fix the login bug.",
  "E-commerce Platform"
);

console.log('Must Have:', requirements.structuredRequirements.mustHave);
console.log('Should Have:', requirements.structuredRequirements.shouldHave);

// 背景・目的補完
const completed = await client.advanced.completeBackground(
  "Add CSV export",
  { project: "Admin Dashboard", role: "product_manager" }
);

console.log(completed.withBackground);

// トーン調整（スライダー）
const toneAdjusted = await client.advanced.adjustTone({
  text: "This is completely wrong!",
  currentTone: 9,
  targetTone: 3,
  preserveMeaning: true
});

console.log(toneAdjusted.selected.text);
```

### リアルタイム機能

```typescript
// WebSocket接続
const ws = client.realtime.connect();

// イベントリスナー
ws.on('connected', () => {
  console.log('Connected to ToneBridge real-time service');
});

ws.on('transform.completed', (data) => {
  console.log('Transformation completed:', data);
});

// リアルタイム変換
ws.transform({
  text: "This needs to be fixed!",
  transformationType: 'soften',
  intensity: 2
});

// 切断
ws.disconnect();
```

### エラーハンドリング

```typescript
import { ToneBridgeError, RateLimitError, ValidationError } from '@tonebridge/sdk';

try {
  const result = await client.transform.soften("Text to transform", 2);
} catch (error) {
  if (error instanceof RateLimitError) {
    console.log(`Rate limit exceeded. Reset at: ${error.resetTime}`);
  } else if (error instanceof ValidationError) {
    console.log(`Validation error: ${error.field} - ${error.reason}`);
  } else if (error instanceof ToneBridgeError) {
    console.log(`API error: ${error.message}`);
  } else {
    console.log('Unexpected error:', error);
  }
}
```

### TypeScript型定義

```typescript
import type {
  TransformOptions,
  TransformResult,
  AnalysisResult,
  TransformationType,
  Intensity
} from '@tonebridge/sdk';

// 型安全な使用
const options: TransformOptions = {
  text: "Sample text",
  transformationType: 'soften' as TransformationType,
  intensity: 2 as Intensity,
  context: {
    recipient: 'client',
    channel: 'email'
  }
};

const result: TransformResult = await client.transform.execute(options);
```

## 🐍 Python SDK

### インストール

```bash
pip install tonebridge
# または
poetry add tonebridge
# または
pipenv install tonebridge
```

### 基本的な使い方

```python
from tonebridge import ToneBridgeClient
import os

# クライアントの初期化
client = ToneBridgeClient(
    api_key=os.environ.get('TONEBRIDGE_API_KEY'),
    # または JWT認証
    token=os.environ.get('TONEBRIDGE_TOKEN'),
    base_url='https://api.tonebridge.io',  # オプション
    timeout=5.0,  # オプション（秒）
    max_retries=3  # オプション
)
```

### 変換機能

```python
# 基本的な変換
result = client.transform.soften(
    text="This is totally unacceptable!",
    intensity=2
)
print(result.transformed_text)
# Output: "This situation needs improvement."

# 詳細オプション付き変換
detailed_result = client.transform.execute(
    text="Fix this bug immediately!",
    transformation_type='soften',
    intensity=2,
    context={
        'recipient': 'client',
        'channel': 'email',
        'metadata': {
            'project_id': 'proj_123',
            'priority': 'high'
        }
    }
)

# バッチ変換
batch_result = client.transform.batch([
    {
        'text': "This is wrong!",
        'transformation_type': 'soften',
        'intensity': 2
    },
    {
        'text': "We need to implement user authentication, data validation, and error handling",
        'transformation_type': 'structure',
        'intensity': 1
    }
])

for item in batch_result.results:
    print(f"Original: {item.original_text}")
    print(f"Transformed: {item.transformed_text}")
```

### 分析機能

```python
# テキスト分析
analysis = client.analyze.text(
    "We must implement this feature immediately or face serious consequences."
)

print(f"Tone: {analysis.tone.primary}")
print(f"Clarity Score: {analysis.clarity.score}")
print(f"Suggestions: {analysis.suggestions}")

# 優先度スコアリング
priorities = client.analyze.priorities([
    {
        'id': 'msg_1',
        'text': 'Critical production bug affecting all users',
        'sender': 'ops_team'
    },
    {
        'id': 'msg_2',
        'text': 'New feature request from sales',
        'sender': 'sales'
    }
])

for msg in priorities.ranked_messages:
    print(f"{msg.id}: Priority {msg.priority_score}")
```

### 非同期サポート

```python
import asyncio
from tonebridge import AsyncToneBridgeClient

async def main():
    async with AsyncToneBridgeClient(api_key="your_api_key") as client:
        # 非同期変換
        result = await client.transform.soften(
            "This is unacceptable!",
            intensity=2
        )
        print(result.transformed_text)
        
        # 並列バッチ処理
        tasks = [
            client.transform.soften(text, 2)
            for text in ["Text 1", "Text 2", "Text 3"]
        ]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(r.transformed_text)

asyncio.run(main())
```

### エラーハンドリング

```python
from tonebridge.exceptions import (
    ToneBridgeError,
    RateLimitError,
    ValidationError,
    AuthenticationError
)

try:
    result = client.transform.soften("Text to transform", intensity=2)
except RateLimitError as e:
    print(f"Rate limit exceeded. Reset at: {e.reset_time}")
except ValidationError as e:
    print(f"Validation error: {e.field} - {e.reason}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except ToneBridgeError as e:
    print(f"API error: {e.message}")
```

### コンテキストマネージャー

```python
from tonebridge import ToneBridgeClient

# 自動リソース管理
with ToneBridgeClient(api_key="your_api_key") as client:
    result = client.transform.soften("Text", intensity=2)
    print(result.transformed_text)
# 接続は自動的にクリーンアップされる
```

## 🔧 Go SDK

### インストール

```bash
go get github.com/tonebridge/go-sdk
```

### 基本的な使い方

```go
package main

import (
    "context"
    "fmt"
    "log"
    
    "github.com/tonebridge/go-sdk/tonebridge"
)

func main() {
    // クライアントの初期化
    client := tonebridge.NewClient(
        tonebridge.WithAPIKey("your_api_key"),
        // または JWT認証
        tonebridge.WithToken("your_jwt_token"),
        tonebridge.WithBaseURL("https://api.tonebridge.io"),
        tonebridge.WithTimeout(5 * time.Second),
    )
    
    ctx := context.Background()
    
    // 基本的な変換
    result, err := client.Transform.Soften(
        ctx,
        "This is totally unacceptable!",
        2, // intensity
        nil, // options
    )
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Transformed: %s\n", result.TransformedText)
}
```

### 変換機能

```go
// 詳細オプション付き変換
options := &tonebridge.TransformOptions{
    Context: &tonebridge.TransformContext{
        Recipient: "client",
        Channel:   "email",
        Metadata: map[string]interface{}{
            "project_id": "proj_123",
            "priority":   "high",
        },
    },
}

result, err := client.Transform.Execute(
    ctx,
    "Fix this bug immediately!",
    tonebridge.TransformTypeSoften,
    2,
    options,
)

// バッチ変換
batchItems := []tonebridge.BatchItem{
    {
        Text:               "This is wrong!",
        TransformationType: tonebridge.TransformTypeSoften,
        Intensity:          2,
    },
    {
        Text:               "We need to implement user authentication",
        TransformationType: tonebridge.TransformTypeStructure,
        Intensity:          1,
    },
}

batchResult, err := client.Transform.Batch(ctx, batchItems)
if err != nil {
    log.Fatal(err)
}

for _, item := range batchResult.Results {
    fmt.Printf("Original: %s\n", item.OriginalText)
    fmt.Printf("Transformed: %s\n", item.TransformedText)
}
```

### エラーハンドリング

```go
import "github.com/tonebridge/go-sdk/tonebridge"

result, err := client.Transform.Soften(ctx, "Text", 2, nil)
if err != nil {
    switch e := err.(type) {
    case *tonebridge.RateLimitError:
        fmt.Printf("Rate limit exceeded. Reset at: %v\n", e.ResetTime)
    case *tonebridge.ValidationError:
        fmt.Printf("Validation error: %s - %s\n", e.Field, e.Reason)
    case *tonebridge.APIError:
        fmt.Printf("API error: %s\n", e.Message)
    default:
        fmt.Printf("Unexpected error: %v\n", err)
    }
}
```

### 並行処理

```go
import (
    "sync"
    "github.com/tonebridge/go-sdk/tonebridge"
)

func transformConcurrently(client *tonebridge.Client, texts []string) {
    var wg sync.WaitGroup
    results := make(chan *tonebridge.TransformResult, len(texts))
    
    for _, text := range texts {
        wg.Add(1)
        go func(t string) {
            defer wg.Done()
            result, err := client.Transform.Soften(context.Background(), t, 2, nil)
            if err == nil {
                results <- result
            }
        }(text)
    }
    
    go func() {
        wg.Wait()
        close(results)
    }()
    
    for result := range results {
        fmt.Printf("Transformed: %s\n", result.TransformedText)
    }
}
```

## 🎯 ベストプラクティス

### 1. API キーの管理

```javascript
// 環境変数を使用（推奨）
const client = new ToneBridgeClient({
  apiKey: process.env.TONEBRIDGE_API_KEY
});

// 設定ファイルから読み込み
import config from './config';
const client = new ToneBridgeClient({
  apiKey: config.tonebridge.apiKey
});

// 絶対にハードコードしない ❌
const client = new ToneBridgeClient({
  apiKey: "sk_live_abc123..." // 危険！
});
```

### 2. エラー処理

```python
# 常に適切なエラー処理を実装
def safe_transform(text, intensity=2):
    try:
        return client.transform.soften(text, intensity)
    except RateLimitError:
        # レート制限の場合は待機して再試行
        time.sleep(60)
        return safe_transform(text, intensity)
    except ValidationError as e:
        # バリデーションエラーはログして代替処理
        logger.error(f"Validation failed: {e}")
        return None
    except Exception as e:
        # 予期しないエラーは上位に伝播
        logger.error(f"Unexpected error: {e}")
        raise
```

### 3. キャッシング

```typescript
// ローカルキャッシュの実装
class CachedToneBridgeClient {
  private cache = new Map<string, any>();
  private client: ToneBridgeClient;
  
  constructor(apiKey: string) {
    this.client = new ToneBridgeClient({ apiKey });
  }
  
  async transform(text: string, type: string, intensity: number) {
    const key = `${text}:${type}:${intensity}`;
    
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }
    
    const result = await this.client.transform.execute({
      text,
      transformationType: type,
      intensity
    });
    
    this.cache.set(key, result);
    return result;
  }
}
```

### 4. バッチ処理

```python
# 大量のテキストを効率的に処理
def process_large_dataset(texts):
    # 100件ずつのバッチに分割
    batch_size = 100
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_items = [
            {
                'text': text,
                'transformation_type': 'soften',
                'intensity': 2
            }
            for text in batch
        ]
        
        try:
            batch_result = client.transform.batch(batch_items)
            results.extend(batch_result.results)
        except Exception as e:
            logger.error(f"Batch {i//batch_size} failed: {e}")
            # 失敗したバッチは個別処理にフォールバック
            for item in batch_items:
                try:
                    result = client.transform.execute(**item)
                    results.append(result)
                except:
                    results.append(None)
    
    return results
```

### 5. リトライ戦略

```go
// 指数バックオフによるリトライ
func retryWithBackoff(fn func() error, maxRetries int) error {
    var err error
    for i := 0; i < maxRetries; i++ {
        err = fn()
        if err == nil {
            return nil
        }
        
        // Rate limit error の場合は長めに待機
        if rateLimitErr, ok := err.(*tonebridge.RateLimitError); ok {
            time.Sleep(time.Until(rateLimitErr.ResetTime))
            continue
        }
        
        // 指数バックオフ
        waitTime := time.Duration(math.Pow(2, float64(i))) * time.Second
        time.Sleep(waitTime)
    }
    return err
}
```

## 📊 パフォーマンス最適化

### 接続プーリング

```javascript
// Node.js での接続プーリング
const client = new ToneBridgeClient({
  apiKey: process.env.TONEBRIDGE_API_KEY,
  httpOptions: {
    keepAlive: true,
    keepAliveMsecs: 1000,
    maxSockets: 50,
    maxFreeSockets: 10,
    timeout: 5000,
    agentOptions: {
      maxSockets: 100,
      maxFreeSockets: 10,
      timeout: 60000,
      keepAliveMsecs: 1000
    }
  }
});
```

### 並列処理

```python
# 非同期並列処理で高速化
import asyncio
from tonebridge import AsyncToneBridgeClient

async def process_parallel(texts):
    async with AsyncToneBridgeClient(api_key="key") as client:
        tasks = []
        for text in texts:
            task = client.transform.soften(text, intensity=2)
            tasks.append(task)
        
        # すべてのタスクを並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # エラーハンドリング
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Failed to process text {i}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
```

## 🔍 デバッグ

### ロギング設定

```javascript
// JavaScript
const client = new ToneBridgeClient({
  apiKey: process.env.TONEBRIDGE_API_KEY,
  debug: true,
  logger: {
    debug: console.debug,
    info: console.info,
    warn: console.warn,
    error: console.error
  }
});
```

```python
# Python
import logging

logging.basicConfig(level=logging.DEBUG)
client = ToneBridgeClient(
    api_key="your_api_key",
    debug=True
)
```

```go
// Go
client := tonebridge.NewClient(
    tonebridge.WithAPIKey("key"),
    tonebridge.WithDebug(true),
    tonebridge.WithLogger(customLogger),
)
```

## 📚 その他のリソース

- [API リファレンス](API_REFERENCE.md)
- [サンプルコード](https://github.com/tonebridge/examples)
- [よくある質問](https://docs.tonebridge.io/faq)
- [サポート](https://support.tonebridge.io)

---

SDK に関する質問やバグ報告は [GitHub Issues](https://github.com/tonebridge/sdk/issues) までお願いします。