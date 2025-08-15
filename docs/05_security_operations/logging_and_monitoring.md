# ロギング・モニタリング仕様書

## 1. 概要

ToneBridgeシステムのロギングとモニタリング戦略を定義します。本仕様書では、ログ収集、メトリクス監視、アラート設定、およびパフォーマンス分析について説明します。

## 2. ロギングアーキテクチャ

### 2.1 ログ収集フロー

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Application  │────>│   Fluentd   │────>│Elasticsearch│
│   Logs      │     │  Collector  │     │   Cluster   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  S3 Archive │     │   Kibana    │
                    └─────────────┘     └─────────────┘
```

### 2.2 ログレベル定義

| レベル | 値 | 用途 | 例 |
|--------|----|----|-----|
| TRACE | 0 | 詳細なデバッグ情報 | 関数の入出力値 |
| DEBUG | 1 | デバッグ情報 | 変数の状態、処理フロー |
| INFO | 2 | 一般情報 | サービス起動、正常処理完了 |
| WARN | 3 | 警告 | リトライ、デフォルト値使用 |
| ERROR | 4 | エラー | 処理失敗、例外発生 |
| FATAL | 5 | 致命的エラー | サービス停止、データ破損 |

## 3. アプリケーションログ

### 3.1 構造化ログフォーマット

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "gateway",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "b7ad6b7169203331",
  "user_id": "user_123",
  "org_id": "org_456",
  "method": "POST",
  "path": "/api/v1/transform",
  "status": 200,
  "duration_ms": 234,
  "message": "Transform request completed successfully",
  "metadata": {
    "transformation_type": "tone",
    "target_tone": "warm",
    "text_length": 150,
    "model_used": "gpt-4"
  }
}
```

### 3.2 Golangロギング実装

```go
package logger

import (
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

func NewLogger(env string) (*zap.Logger, error) {
    var config zap.Config
    
    if env == "production" {
        config = zap.NewProductionConfig()
        config.EncoderConfig.TimeKey = "timestamp"
        config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    } else {
        config = zap.NewDevelopmentConfig()
        config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
    }
    
    config.OutputPaths = []string{"stdout", "/var/log/tonebridge/app.log"}
    config.ErrorOutputPaths = []string{"stderr", "/var/log/tonebridge/error.log"}
    
    return config.Build()
}

// 使用例
func TransformHandler(logger *zap.Logger) fiber.Handler {
    return func(c *fiber.Ctx) error {
        start := time.Now()
        
        logger.Info("Transform request started",
            zap.String("trace_id", c.Get("X-Trace-ID")),
            zap.String("user_id", c.Locals("user_id").(string)),
            zap.String("path", c.Path()),
        )
        
        // 処理実行
        result, err := processTransform(c)
        
        duration := time.Since(start)
        
        if err != nil {
            logger.Error("Transform failed",
                zap.Error(err),
                zap.Duration("duration", duration),
            )
            return err
        }
        
        logger.Info("Transform completed",
            zap.Duration("duration", duration),
            zap.Int("status", 200),
        )
        
        return c.JSON(result)
    }
}
```

### 3.3 Pythonロギング実装

```python
import logging
import json
from pythonjsonlogger import jsonlogger
from typing import Any, Dict

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'llm-service'
        log_record['level'] = record.levelname
        
        # トレースIDを追加
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id

# ロガー設定
def setup_logger():
    logger = logging.getLogger('tonebridge')
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

# 使用例
logger = setup_logger()

async def transform_text(request: TransformRequest, trace_id: str):
    logger.info("Starting text transformation",
                extra={
                    'trace_id': trace_id,
                    'transformation_type': request.transformation_type,
                    'text_length': len(request.text)
                })
    
    try:
        result = await llm_chain.ainvoke(request.dict())
        logger.info("Transformation completed",
                    extra={
                        'trace_id': trace_id,
                        'processing_time_ms': result.get('processing_time')
                    })
        return result
    except Exception as e:
        logger.error("Transformation failed",
                     extra={
                        'trace_id': trace_id,
                        'error': str(e)
                     },
                     exc_info=True)
        raise
```

## 4. メトリクス監視

### 4.1 Prometheusメトリクス

#### アプリケーションメトリクス
```go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // カウンターメトリクス
    RequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "tonebridge_requests_total",
            Help: "Total number of requests",
        },
        []string{"method", "endpoint", "status"},
    )
    
    // ヒストグラムメトリクス
    RequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "tonebridge_request_duration_seconds",
            Help: "Request duration in seconds",
            Buckets: []float64{0.01, 0.05, 0.1, 0.5, 1, 2, 5},
        },
        []string{"method", "endpoint"},
    )
    
    // ゲージメトリクス
    ActiveConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "tonebridge_active_connections",
            Help: "Number of active connections",
        },
    )
    
    // サマリーメトリクス
    TransformationLatency = promauto.NewSummaryVec(
        prometheus.SummaryOpts{
            Name: "tonebridge_transformation_latency_ms",
            Help: "Transformation latency in milliseconds",
            Objectives: map[float64]float64{
                0.5:  0.05,  // 50th percentile
                0.9:  0.01,  // 90th percentile
                0.99: 0.001, // 99th percentile
            },
        },
        []string{"transformation_type", "model"},
    )
)
```

### 4.2 カスタムメトリクス

```go
// ビジネスメトリクス
type BusinessMetrics struct {
    TransformationsPerMinute float64
    AverageTextLength       float64
    ModelUsageDistribution  map[string]float64
    ErrorRate              float64
    CacheHitRate           float64
}

func CollectBusinessMetrics() BusinessMetrics {
    return BusinessMetrics{
        TransformationsPerMinute: calculateTPM(),
        AverageTextLength:       calculateAvgLength(),
        ModelUsageDistribution:  getModelDistribution(),
        ErrorRate:              calculateErrorRate(),
        CacheHitRate:           getCacheHitRate(),
    }
}
```

## 5. 分散トレーシング

### 5.1 OpenTelemetry実装

```go
package tracing

import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/sdk/trace"
)

func InitTracer(serviceName string) (*trace.TracerProvider, error) {
    // Jaegerエクスポーター設定
    exp, err := jaeger.New(
        jaeger.WithCollectorEndpoint(
            jaeger.WithEndpoint("http://jaeger:14268/api/traces"),
        ),
    )
    if err != nil {
        return nil, err
    }
    
    // TracerProvider作成
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exp),
        trace.WithResource(
            resource.NewWithAttributes(
                semconv.SchemaURL,
                semconv.ServiceNameKey.String(serviceName),
            ),
        ),
    )
    
    otel.SetTracerProvider(tp)
    return tp, nil
}

// トレース使用例
func TransformWithTracing(ctx context.Context, req TransformRequest) error {
    tracer := otel.Tracer("tonebridge")
    ctx, span := tracer.Start(ctx, "transform_operation")
    defer span.End()
    
    // スパン属性を追加
    span.SetAttributes(
        attribute.String("transformation.type", req.Type),
        attribute.Int("text.length", len(req.Text)),
    )
    
    // 子スパン作成
    ctx, validationSpan := tracer.Start(ctx, "validate_request")
    err := validateRequest(req)
    validationSpan.End()
    
    if err != nil {
        span.RecordError(err)
        return err
    }
    
    // LLM呼び出し
    ctx, llmSpan := tracer.Start(ctx, "llm_call")
    result := callLLM(ctx, req)
    llmSpan.End()
    
    return nil
}
```

## 6. モニタリングダッシュボード

### 6.1 Grafanaダッシュボード設定

```json
{
  "dashboard": {
    "title": "ToneBridge Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(tonebridge_requests_total[5m])"
        }]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(tonebridge_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(tonebridge_requests_total{status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Active Users",
        "targets": [{
          "expr": "count(increase(tonebridge_user_activity[5m]) > 0)"
        }]
      }
    ]
  }
}
```

### 6.2 主要ダッシュボード

#### システムヘルスダッシュボード
- CPU使用率
- メモリ使用量
- ディスクI/O
- ネットワークトラフィック
- コンテナステータス

#### アプリケーションダッシュボード
- リクエスト数/秒
- レスポンスタイム分布
- エラー率
- 成功率
- アクティブセッション数

#### ビジネスダッシュボード
- 変換実行数
- ユーザーアクティビティ
- 人気の変換タイプ
- 使用量トレンド
- コスト分析

## 7. アラート設定

### 7.1 Prometheusアラートルール

```yaml
groups:
- name: tonebridge_alerts
  interval: 30s
  rules:
  
  # 高エラー率
  - alert: HighErrorRate
    expr: rate(tonebridge_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
      team: backend
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} (threshold: 5%)"
  
  # 高レスポンスタイム
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(tonebridge_request_duration_seconds_bucket[5m])) > 2
    for: 10m
    labels:
      severity: warning
      team: backend
    annotations:
      summary: "High response time"
      description: "95th percentile response time is {{ $value }}s"
  
  # データベース接続エラー
  - alert: DatabaseConnectionFailure
    expr: up{job="postgresql"} == 0
    for: 1m
    labels:
      severity: critical
      team: database
    annotations:
      summary: "Database connection failed"
      description: "Cannot connect to PostgreSQL"
  
  # メモリ使用率
  - alert: HighMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
    for: 5m
    labels:
      severity: warning
      team: infrastructure
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}%"
  
  # ディスク使用率
  - alert: DiskSpaceRunningOut
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) > 0.8
    for: 5m
    labels:
      severity: warning
      team: infrastructure
    annotations:
      summary: "Disk space running out"
      description: "Disk usage is {{ $value }}%"
```

### 7.2 アラート通知設定

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  
  routes:
  - match:
      severity: critical
    receiver: 'critical'
    continue: true
  
  - match:
      severity: warning
    receiver: 'warning'

receivers:
- name: 'default'
  slack_configs:
  - channel: '#alerts'
    title: 'ToneBridge Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'critical'
  slack_configs:
  - channel: '#critical-alerts'
    title: '🚨 CRITICAL: ToneBridge Alert'
  pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_KEY'

- name: 'warning'
  slack_configs:
  - channel: '#warnings'
    title: '⚠️ Warning: ToneBridge Alert'
```

## 8. ログ分析

### 8.1 Elasticsearchクエリ例

```json
// エラーログ検索
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "error_types": {
      "terms": {"field": "error_type.keyword"}
    }
  }
}

// 特定ユーザーのアクティビティ追跡
{
  "query": {
    "bool": {
      "must": [
        {"term": {"user_id": "user_123"}},
        {"range": {"timestamp": {"gte": "now-24h"}}}
      ]
    }
  },
  "sort": [{"timestamp": {"order": "desc"}}]
}

// パフォーマンス分析
{
  "query": {
    "range": {
      "duration_ms": {"gte": 1000}
    }
  },
  "aggs": {
    "slow_endpoints": {
      "terms": {"field": "path.keyword"},
      "aggs": {
        "avg_duration": {
          "avg": {"field": "duration_ms"}
        }
      }
    }
  }
}
```

### 8.2 ログローテーション設定

```bash
# /etc/logrotate.d/tonebridge
/var/log/tonebridge/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 tonebridge tonebridge
    sharedscripts
    postrotate
        # Fluentdに再読み込みシグナル送信
        kill -USR1 $(cat /var/run/fluentd.pid)
    endscript
}
```

## 9. パフォーマンスプロファイリング

### 9.1 Go pprof設定

```go
import (
    _ "net/http/pprof"
    "net/http"
)

func EnableProfiling() {
    go func() {
        // プロファイリングエンドポイント
        http.ListenAndServe("localhost:6060", nil)
    }()
}

// CPU プロファイル取得
// go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

// メモリプロファイル取得
// go tool pprof http://localhost:6060/debug/pprof/heap

// ゴルーチンプロファイル取得
// go tool pprof http://localhost:6060/debug/pprof/goroutine
```

### 9.2 Python プロファイリング

```python
import cProfile
import pstats
from memory_profiler import profile

# CPU プロファイリング
def profile_transformation():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 処理実行
    result = transform_text(request)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result

# メモリプロファイリング
@profile
def memory_intensive_operation():
    large_data = load_large_dataset()
    processed = process_data(large_data)
    return processed
```

## 10. セキュリティ監視

### 10.1 セキュリティイベント検知

```yaml
# Security alert rules
- alert: SuspiciousLoginAttempts
  expr: rate(login_attempts_failed[5m]) > 10
  labels:
    severity: security
    
- alert: UnauthorizedAPIAccess
  expr: rate(tonebridge_requests_total{status="403"}[5m]) > 5
  labels:
    severity: security
    
- alert: AbnormalDataAccess
  expr: rate(database_queries_total{table="users"}[5m]) > 100
  labels:
    severity: security
```

### 10.2 監査ログ監視

```python
def analyze_audit_logs():
    """監査ログの異常検知"""
    
    # 異常なアクセスパターン検知
    suspicious_patterns = [
        r"SELECT \* FROM users",  # 全ユーザー情報取得
        r"DROP TABLE",            # テーブル削除試行
        r"'; OR '1'='1",         # SQLインジェクション試行
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, log_entry):
            alert_security_team(log_entry)
```

## 11. SLI/SLO定義

### 11.1 Service Level Indicators (SLI)

| SLI | 測定方法 | 目標値 |
|-----|---------|--------|
| 可用性 | 成功リクエスト数 / 全リクエスト数 | 99.9% |
| レイテンシ | 95パーセンタイルレスポンスタイム | < 500ms |
| エラー率 | エラーレスポンス数 / 全レスポンス数 | < 0.1% |
| スループット | 1秒あたりのリクエスト処理数 | > 100 req/s |

### 11.2 Service Level Objectives (SLO)

```yaml
slos:
  - name: API Availability
    sli: (1 - rate(tonebridge_requests_total{status=~"5.."}[30d]))
    target: 0.999
    
  - name: Response Time
    sli: histogram_quantile(0.95, rate(request_duration_seconds_bucket[30d]))
    target: 0.5  # 500ms
    
  - name: Error Budget
    calculation: (1 - 0.999) * 30 * 24 * 60  # 分単位
    alert_threshold: 0.2  # 20%消費で警告
```

## 12. コスト最適化

### 12.1 ログストレージ最適化

```bash
# ログ圧縮とアーカイブ
#!/bin/bash

# 30日以上前のログをS3 Glacierへ移動
aws s3 mv s3://tonebridge-logs/active/ s3://tonebridge-logs/archive/ \
    --recursive \
    --exclude "*" \
    --include "*.log" \
    --storage-class GLACIER \
    --older-than 30

# ローカルログの圧縮
find /var/log/tonebridge -name "*.log" -mtime +7 -exec gzip {} \;
```

## まとめ

ToneBridgeのロギング・モニタリングシステムは、包括的な可観測性を提供し、システムの健全性とパフォーマンスを継続的に監視します。プロアクティブなアラートと詳細な分析により、問題の早期発見と迅速な解決を実現します。
