# ToneBridge JavaScript SDK

Official JavaScript/TypeScript SDK for the ToneBridge API - Transform communication with AI-powered text processing.

[![npm version](https://img.shields.io/npm/v/@tonebridge/sdk.svg)](https://www.npmjs.com/package/@tonebridge/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)

## Installation

```bash
npm install @tonebridge/sdk
# or
yarn add @tonebridge/sdk
# or
pnpm add @tonebridge/sdk
```

## Quick Start

```typescript
import { ToneBridgeClient } from '@tonebridge/sdk';

// Initialize client
const client = new ToneBridgeClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.tonebridge.io' // Optional
});

// Transform text
const result = await client.transform.soften(
  "This needs to be fixed immediately!",
  2 // intensity (0-3)
);

console.log(result.data.transformed_text);
// Output: "I'd appreciate if we could address this when you have a moment."
```

## Authentication

### API Key Authentication

```typescript
const client = new ToneBridgeClient({
  apiKey: 'your-api-key'
});
```

### Email/Password Authentication

```typescript
const client = new ToneBridgeClient();

// Login
const auth = await client.authenticate('user@example.com', 'password');
console.log(auth.access_token);

// The client automatically manages tokens
```

### Direct Token

```typescript
const client = new ToneBridgeClient();
client.setAccessToken('your-access-token');
```

## Core Features

### Text Transformation

#### Basic Transformations

```typescript
// Soften harsh language
const softened = await client.transform.soften(
  "Your code is terrible and needs complete rewrite",
  2 // intensity
);

// Clarify confusing text
const clarified = await client.transform.clarify(
  "The thing needs to be updated with the new stuff ASAP",
  2
);

// Structure unorganized text
const structured = await client.transform.structure(
  "We need API docs login system should be secure also need tests",
  2
);

// Summarize long text
const summary = await client.transform.summarize(longText, 2);
```

#### Advanced Transformations

```typescript
// Structure requirements into 4 quadrants
const requirements = await client.transform.structureRequirements(
  "We need a login system that's secure and fast..."
);

// Complete missing background information
const completed = await client.transform.completeBackground(
  "The API should handle user authentication"
);

// Custom transformation with instructions
const custom = await client.transform.customTransform(
  "Technical specification text...",
  "Convert this to executive summary format"
);
```

#### Batch Transformation

```typescript
const batch = await client.transform.batchTransform({
  items: [
    { text: "Text 1", transformation_type: "soften", intensity: 2 },
    { text: "Text 2", transformation_type: "clarify", intensity: 1 },
    { text: "Text 3", transformation_type: "structure", intensity: 3 }
  ],
  parallel: true,
  stop_on_error: false
});

console.log(batch.results);
```

### Text Analysis

```typescript
// Comprehensive analysis
const analysis = await client.analyze.comprehensiveAnalysis(
  "This is an urgent request that needs immediate attention!"
);

console.log(analysis.data);
// {
//   tone: "urgent",
//   clarity_score: 85,
//   priority: "high",
//   priority_quadrant: "Q1",
//   sentiment: { polarity: -0.2, subjectivity: 0.7 },
//   suggestions: ["Consider adding specific deadlines", ...]
// }

// Individual analyses
const tone = await client.analyze.analyzeTone(text);
const clarity = await client.analyze.analyzeClarity(text);
const priority = await client.analyze.analyzePriority(text);
const sentiment = await client.analyze.analyzeSentiment(text);
```

### Auto-Transform

Configure automatic transformations based on triggers:

```typescript
// Enable auto-transform
await client.autoTransform.enable();

// Create keyword-based rule
await client.autoTransform.createKeywordRule(
  "Soften Urgent Messages",
  ["urgent", "ASAP", "immediately"],
  "soften"
);

// Create sentiment-based rule
await client.autoTransform.createSentimentRule(
  "Fix Negative Tone",
  -0.5,          // threshold
  "less_than",   // operator
  "soften"
);

// Create time-based rule
await client.autoTransform.createTimeRule(
  "End of Day Summaries",
  "17:00",       // after
  "19:00",       // before
  "summarize"
);

// Evaluate message
const context = {
  message: "This needs to be done ASAP!",
  user_id: "user123",
  tenant_id: "tenant456",
  platform: "slack"
};

const evaluation = await client.autoTransform.evaluate(context);
if (evaluation.should_transform) {
  const result = await client.autoTransform.transform(context, evaluation);
  console.log(result.transformed);
}
```

### Real-time WebSocket

```typescript
const client = new ToneBridgeClient({
  apiKey: 'your-api-key',
  enableWebSocket: true,
  onConnect: () => console.log('Connected'),
  onMessage: (data) => console.log('Message:', data),
  onError: (error) => console.error('Error:', error)
});

// Send real-time transform request
client.ws?.sendTransform({
  text: "Transform this in real-time",
  transformation_type: "soften"
});

// Listen for specific events
client.ws?.on('transform', (data) => {
  console.log('Transform result:', data);
});
```

## Advanced Usage

### Custom Request Configuration

```typescript
// Make custom API request
const customData = await client.request({
  method: 'POST',
  url: '/custom-endpoint',
  data: { custom: 'data' }
});
```

### Error Handling

```typescript
import { ToneBridgeError, ValidationError, RateLimitError } from '@tonebridge/sdk';

try {
  const result = await client.transform.soften(text);
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation failed:', error.details);
  } else if (error instanceof RateLimitError) {
    console.error('Rate limited. Retry after:', error.retryAfter);
  } else if (error instanceof ToneBridgeError) {
    console.error('API error:', error.statusCode, error.message);
  }
}
```

### TypeScript Support

The SDK is written in TypeScript and provides comprehensive type definitions:

```typescript
import { 
  TransformRequest,
  TransformResponse,
  AnalyzeRequest,
  AnalyzeResponse,
  TransformationType,
  Priority
} from '@tonebridge/sdk';

const request: TransformRequest = {
  text: "Your text here",
  transformation_type: "soften",
  intensity: 2,
  options: {
    preserve_formatting: true,
    target_audience: "executive"
  }
};

const response: TransformResponse = await client.transform.transform(request);
```

## API Reference

### Client Options

```typescript
interface ToneBridgeConfig {
  baseUrl?: string;           // API base URL
  apiKey?: string;            // API key for authentication
  timeout?: number;           // Request timeout in ms
  maxRetries?: number;        // Max retry attempts
  enableWebSocket?: boolean;  // Enable WebSocket connection
  onConnect?: () => void;     // WebSocket connect callback
  onDisconnect?: () => void;  // WebSocket disconnect callback
  onMessage?: (data) => void; // WebSocket message callback
  onError?: (error) => void;  // WebSocket error callback
}
```

### Transform Service Methods

- `transform(request: TransformRequest)` - General transformation
- `soften(text, intensity?, options?)` - Soften harsh language
- `clarify(text, intensity?, options?)` - Improve clarity
- `structure(text, intensity?, options?)` - Structure text
- `summarize(text, intensity?, options?)` - Summarize text
- `transformTerminology(text, options?)` - Convert technical terms
- `structureRequirements(text, options?)` - Structure requirements
- `completeBackground(text, options?)` - Complete background info
- `adjustTone(text, intensity, targetTone?)` - Adjust tone
- `customTransform(text, instructions, options?)` - Custom transformation
- `batchTransform(request)` - Batch transformation
- `getHistory(limit?, offset?)` - Get transformation history

### Analyze Service Methods

- `analyze(request: AnalyzeRequest)` - General analysis
- `analyzeTone(text)` - Analyze tone
- `analyzeClarity(text)` - Get clarity score
- `analyzePriority(text)` - Determine priority
- `analyzeSentiment(text)` - Analyze sentiment
- `comprehensiveAnalysis(text, includeSuggestions?)` - Full analysis
- `scorePriority(text, context?)` - Score using Eisenhower Matrix
- `batchScorePriorities(messages)` - Batch priority scoring
- `checkNeedsTransformation(text)` - Check if transformation needed
- `getSuggestions(text)` - Get improvement suggestions

### Auto-Transform Service Methods

- `getConfig(tenantId?)` - Get configuration
- `updateConfig(config, tenantId?)` - Update configuration
- `enable(tenantId?)` - Enable auto-transform
- `disable(tenantId?)` - Disable auto-transform
- `evaluate(context)` - Evaluate message
- `transform(context, transformation)` - Apply transformation
- `getRules(tenantId?)` - Get all rules
- `createRule(rule, tenantId?)` - Create rule
- `updateRule(ruleId, updates, tenantId?)` - Update rule
- `deleteRule(ruleId, tenantId?)` - Delete rule
- `getTemplates()` - Get rule templates
- `applyTemplate(templateId, tenantId?)` - Apply template

## Examples

### Express.js Integration

```typescript
import express from 'express';
import { ToneBridgeClient } from '@tonebridge/sdk';

const app = express();
const tonebridge = new ToneBridgeClient({ apiKey: process.env.TONEBRIDGE_API_KEY });

app.post('/api/transform', async (req, res) => {
  try {
    const result = await tonebridge.transform.soften(req.body.text);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### React Hook

```typescript
import { useState, useCallback } from 'react';
import { ToneBridgeClient } from '@tonebridge/sdk';

const client = new ToneBridgeClient({ apiKey: 'your-api-key' });

export function useToneTransform() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const transform = useCallback(async (text, type = 'soften') => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await client.transform[type](text);
      return result.data.transformed_text;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { transform, loading, error };
}
```

### CLI Tool

```typescript
#!/usr/bin/env node
import { ToneBridgeClient } from '@tonebridge/sdk';
import { program } from 'commander';

const client = new ToneBridgeClient({ 
  apiKey: process.env.TONEBRIDGE_API_KEY 
});

program
  .command('soften <text>')
  .description('Soften harsh text')
  .option('-i, --intensity <n>', 'intensity (0-3)', '2')
  .action(async (text, options) => {
    const result = await client.transform.soften(
      text, 
      parseInt(options.intensity)
    );
    console.log(result.data.transformed_text);
  });

program.parse();
```

## Environment Variables

```bash
# .env
TONEBRIDGE_API_KEY=your-api-key
TONEBRIDGE_BASE_URL=https://api.tonebridge.io
```

```typescript
const client = new ToneBridgeClient({
  apiKey: process.env.TONEBRIDGE_API_KEY,
  baseUrl: process.env.TONEBRIDGE_BASE_URL
});
```

## Browser Support

The SDK supports modern browsers with ES6+ support. For older browsers, use a transpiler like Babel.

```html
<script src="https://unpkg.com/@tonebridge/sdk/dist/tonebridge.min.js"></script>
<script>
  const client = new ToneBridge.Client({ apiKey: 'your-api-key' });
</script>
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## Building

```bash
# Build the SDK
npm run build

# Generate documentation
npm run docs
```

## Support

- Documentation: [https://docs.tonebridge.io](https://docs.tonebridge.io)
- API Reference: [https://api.tonebridge.io/docs](https://api.tonebridge.io/docs)
- Issues: [GitHub Issues](https://github.com/tonebridge/javascript-sdk/issues)
- Email: support@tonebridge.io

## License

MIT © ToneBridge

---

Made with ❤️ by the ToneBridge Team