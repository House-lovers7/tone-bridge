# ToneBridge Go SDK

Official Go SDK for the ToneBridge API - Transform communication tone with AI-powered text transformation.

## Installation

```bash
go get github.com/tonebridge/go-sdk
```

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    "log"
    
    "github.com/tonebridge/go-sdk/tonebridge"
)

func main() {
    // Initialize client with API key
    client := tonebridge.NewClient("your-api-key")
    
    // Or with authentication
    client := tonebridge.NewClient("")
    authResp, err := client.Authenticate(context.Background(), "user@example.com", "password")
    if err != nil {
        log.Fatal(err)
    }
    
    // Transform text
    resp, err := client.Transform.Soften(context.Background(), 
        "This is completely unacceptable!", 
        2, 
        nil)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println("Transformed:", resp.Data.TransformedText)
}
```

## Features

- ✅ Text transformation (soften, clarify, structure, summarize, etc.)
- ✅ Text analysis (tone, clarity, priority, sentiment)
- ✅ Auto-transform rules and templates
- ✅ Real-time WebSocket support
- ✅ Batch operations
- ✅ Custom dictionaries
- ✅ Comprehensive error handling
- ✅ Automatic retry logic
- ✅ Token refresh

## Services

### Transform Service

Transform text with various transformation types:

```go
// Soften harsh language
resp, err := client.Transform.Soften(ctx, "Fix this now!", 2, nil)

// Clarify confusing text
resp, err := client.Transform.Clarify(ctx, confusingText, 2, nil)

// Structure unorganized text
resp, err := client.Transform.Structure(ctx, unorganizedText, 2, nil)

// Summarize long text
resp, err := client.Transform.Summarize(ctx, longText, 2, nil)

// Convert technical terminology
resp, err := client.Transform.TransformTerminology(ctx, technicalText, nil)

// Structure requirements using Eisenhower Matrix
resp, err := client.Transform.StructureRequirements(ctx, requirements, nil)

// Complete background information
resp, err := client.Transform.CompleteBackground(ctx, incompleteText, nil)

// Custom transformation
resp, err := client.Transform.CustomTransform(ctx, text, "Make it more formal", nil)
```

### Analyze Service

Analyze text for various metrics:

```go
// Analyze tone
toneResult, err := client.Analyze.AnalyzeTone(ctx, text)

// Analyze clarity
clarityResult, err := client.Analyze.AnalyzeClarity(ctx, text)

// Analyze priority (Eisenhower Matrix)
priorityResult, err := client.Analyze.AnalyzePriority(ctx, text)

// Analyze sentiment
sentimentResult, err := client.Analyze.AnalyzeSentiment(ctx, text)

// Comprehensive analysis
comprehensive, err := client.Analyze.ComprehensiveAnalysis(ctx, text)
```

### Auto-Transform Service

Manage automatic transformation rules:

```go
// Create a rule
rule := &tonebridge.AutoTransformRule{
    RuleName:               "Soften Harsh Emails",
    Description:           "Automatically soften harsh language in emails",
    Enabled:               true,
    Priority:              1,
    TriggerType:           tonebridge.TriggerSentiment,
    TriggerValue:          map[string]interface{}{"threshold": -0.5},
    TransformationType:    tonebridge.TransformationSoften,
    TransformationIntensity: 2,
}
createdRule, err := client.AutoTransform.CreateRule(ctx, rule)

// Evaluate rules for a message
messageCtx := &tonebridge.MessageContext{
    Message:  "This is terrible!",
    UserID:   "user123",
    TenantID: "tenant456",
    Platform: tonebridge.PlatformSlack,
}
result, err := client.AutoTransform.EvaluateRules(ctx, messageCtx)

// Apply transformation
transformed, err := client.AutoTransform.ApplyTransformation(ctx, messageCtx)
```

### WebSocket Client

Real-time communication:

```go
// Initialize with WebSocket
client := tonebridge.NewClient("your-api-key",
    tonebridge.WithWebSocket(
        func() { fmt.Println("Connected") },
        func() { fmt.Println("Disconnected") },
        func(msg interface{}) { fmt.Printf("Message: %v\n", msg) },
        func(err error) { fmt.Printf("Error: %v\n", err) },
    ))

// Connect WebSocket
err := client.WebSocket.Connect()

// Subscribe to events
err = client.WebSocket.Subscribe("transformations")

// Real-time transformation
err = client.WebSocket.TransformRealtime(
    &tonebridge.TransformRequest{
        Text:               "Fix this immediately!",
        TransformationType: tonebridge.TransformationSoften,
        Intensity:          2,
    },
    func(resp *tonebridge.TransformResponse, err error) {
        if err != nil {
            log.Printf("Error: %v", err)
            return
        }
        fmt.Println("Transformed:", resp.Data.TransformedText)
    },
)
```

## Advanced Usage

### Batch Operations

```go
// Batch transform
batchReq := &tonebridge.BatchTransformRequest{
    Items: []tonebridge.TransformRequest{
        {Text: "Text 1", TransformationType: tonebridge.TransformationSoften, Intensity: 2},
        {Text: "Text 2", TransformationType: tonebridge.TransformationClarify, Intensity: 1},
    },
    Parallel: true,
}
batchResp, err := client.Transform.BatchTransform(ctx, batchReq)

// Batch analyze
batchAnalyze, err := client.Analyze.BatchAnalyze(ctx, 
    []string{"Text 1", "Text 2"},
    []tonebridge.AnalysisType{
        tonebridge.AnalysisTone,
        tonebridge.AnalysisClarity,
    },
)
```

### Custom Options

```go
// Transform with options
options := &tonebridge.TransformOptions{
    PreserveFormatting: true,
    IncludeSignature:   true,
    TargetAudience:     "executives",
    Language:           "en",
}
resp, err := client.Transform.Soften(ctx, text, 2, options)
```

### Auto-Transform Templates

```go
// List templates
templates, err := client.AutoTransform.ListTemplates(ctx, "communication")

// Apply template
rule, err := client.AutoTransform.ApplyTemplate(ctx, "template-id", 
    map[string]interface{}{
        "custom_field": "value",
    },
)
```

### Error Handling

```go
resp, err := client.Transform.Soften(ctx, text, 2, nil)
if err != nil {
    switch e := err.(type) {
    case *tonebridge.ValidationError:
        fmt.Printf("Validation error: %s\n", e.Message)
        for _, field := range e.Fields {
            fmt.Printf("  %s: %s\n", field.Field, field.Message)
        }
    case *tonebridge.RateLimitError:
        fmt.Printf("Rate limited. Retry after %d seconds\n", e.RetryAfter)
    case *tonebridge.AuthenticationError:
        fmt.Println("Authentication failed:", e.Message)
    default:
        fmt.Println("Error:", err)
    }
}
```

## Configuration

### Client Options

```go
client := tonebridge.NewClient("your-api-key",
    tonebridge.WithBaseURL("https://custom.api.url"),
    tonebridge.WithTimeout(60 * time.Second),
    tonebridge.WithMaxRetries(5),
)
```

### Environment Variables

```bash
export TONEBRIDGE_API_KEY="your-api-key"
export TONEBRIDGE_BASE_URL="https://api.tonebridge.io/api/v1"
```

## Examples

See the [examples](./examples) directory for complete examples:

- [Basic transformation](./examples/basic/main.go)
- [Analysis](./examples/analysis/main.go)
- [Auto-transform](./examples/auto-transform/main.go)
- [WebSocket](./examples/websocket/main.go)
- [Batch operations](./examples/batch/main.go)
- [Error handling](./examples/error-handling/main.go)

## Testing

```bash
go test ./...
```

## Requirements

- Go 1.20 or higher
- Dependencies:
  - github.com/go-resty/resty/v2
  - github.com/gorilla/websocket

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Support

- Documentation: https://docs.tonebridge.io
- API Reference: https://api.tonebridge.io/docs
- Issues: https://github.com/tonebridge/go-sdk/issues
- Email: support@tonebridge.io

## Contributing

Contributions are welcome! Please read our [Contributing Guide](./CONTRIBUTING.md) for details.