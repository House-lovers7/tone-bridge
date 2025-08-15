# ToneBridge Python SDK

Official Python SDK for the ToneBridge API - Transform communication with AI-powered text processing.

[![PyPI version](https://img.shields.io/pypi/v/tonebridge.svg)](https://pypi.org/project/tonebridge/)
[![Python versions](https://img.shields.io/pypi/pyversions/tonebridge.svg)](https://pypi.org/project/tonebridge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install tonebridge
```

For async support:
```bash
pip install tonebridge[async]
```

For development:
```bash
pip install tonebridge[dev]
```

## Quick Start

```python
from tonebridge import ToneBridgeClient

# Initialize client
client = ToneBridgeClient(api_key="your-api-key")

# Transform text
result = client.transform.soften(
    "This needs to be fixed immediately!",
    intensity=2
)

print(result["data"]["transformed_text"])
# Output: "I'd appreciate if we could address this when you have a moment."
```

## Authentication

### API Key Authentication

```python
client = ToneBridgeClient(api_key="your-api-key")
```

### Email/Password Authentication

```python
client = ToneBridgeClient()

# Login
auth = client.authenticate("user@example.com", "password")
print(auth["access_token"])

# The client automatically manages tokens
```

### Direct Token

```python
client = ToneBridgeClient()
client.set_access_token("your-access-token")
```

## Core Features

### Text Transformation

#### Basic Transformations

```python
# Soften harsh language
result = client.transform.soften(
    "Your code is terrible and needs complete rewrite",
    intensity=2
)

# Clarify confusing text
result = client.transform.clarify(
    "The thing needs to be updated with the new stuff ASAP",
    intensity=2
)

# Structure unorganized text
result = client.transform.structure(
    "We need API docs login system should be secure also need tests",
    intensity=2
)

# Summarize long text
result = client.transform.summarize(long_text, intensity=2)
```

#### Advanced Transformations

```python
# Structure requirements into 4 quadrants
result = client.transform.structure_requirements(
    "We need a login system that's secure and fast..."
)

# Complete missing background information
result = client.transform.complete_background(
    "The API should handle user authentication"
)

# Custom transformation with instructions
result = client.transform.custom_transform(
    "Technical specification text...",
    "Convert this to executive summary format"
)
```

#### Batch Transformation

```python
results = client.transform.batch_transform(
    items=[
        {"text": "Text 1", "transformation_type": "soften", "intensity": 2},
        {"text": "Text 2", "transformation_type": "clarify", "intensity": 1},
        {"text": "Text 3", "transformation_type": "structure", "intensity": 3}
    ],
    parallel=True,
    stop_on_error=False
)
```

### Text Analysis

```python
# Comprehensive analysis
analysis = client.analyze.comprehensive_analysis(
    "This is an urgent request that needs immediate attention!",
    include_suggestions=True
)

print(analysis["data"])
# {
#   "tone": "urgent",
#   "clarity_score": 85,
#   "priority": "high",
#   "priority_quadrant": "Q1",
#   "sentiment": {"polarity": -0.2, "subjectivity": 0.7},
#   "suggestions": ["Consider adding specific deadlines", ...]
# }

# Individual analyses
tone = client.analyze.analyze_tone(text)
clarity = client.analyze.analyze_clarity(text)
priority = client.analyze.analyze_priority(text)
sentiment = client.analyze.analyze_sentiment(text)
```

### Auto-Transform

Configure automatic transformations based on triggers:

```python
# Enable auto-transform
client.auto_transform.enable()

# Create keyword-based rule
client.auto_transform.create_keyword_rule(
    name="Soften Urgent Messages",
    keywords=["urgent", "ASAP", "immediately"],
    transformation_type="soften"
)

# Create sentiment-based rule
client.auto_transform.create_sentiment_rule(
    name="Fix Negative Tone",
    threshold=-0.5,
    operator="less_than",
    transformation_type="soften"
)

# Create time-based rule
client.auto_transform.create_time_rule(
    name="End of Day Summaries",
    after="17:00",
    before="19:00",
    transformation_type="summarize"
)

# Evaluate message
from tonebridge.types import MessageContext

context = MessageContext(
    message="This needs to be done ASAP!",
    user_id="user123",
    tenant_id="tenant456",
    platform="slack"
)

evaluation = client.auto_transform.evaluate(context)
if evaluation["should_transform"]:
    result = client.auto_transform.transform(context, evaluation)
    print(result["transformed"])
```

### Real-time WebSocket

```python
def on_connect():
    print("Connected to ToneBridge")

def on_message(data):
    print(f"Received: {data}")

def on_error(error):
    print(f"Error: {error}")

client = ToneBridgeClient(
    api_key="your-api-key",
    enable_websocket=True,
    on_connect=on_connect,
    on_message=on_message,
    on_error=on_error
)

# Send real-time transform request
client.ws.send_transform({
    "text": "Transform this in real-time",
    "transformation_type": "soften"
})
```

## Advanced Usage

### Context Manager

```python
with ToneBridgeClient(api_key="your-api-key") as client:
    result = client.transform.soften("Fix this now!")
    print(result["data"]["transformed_text"])
```

### Error Handling

```python
from tonebridge import (
    ToneBridgeError,
    ValidationError,
    RateLimitError,
    AuthenticationError
)

try:
    result = client.transform.soften(text)
except ValidationError as e:
    print(f"Validation failed: {e.details}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except ToneBridgeError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

### Type Hints

The SDK provides comprehensive type hints for better IDE support:

```python
from tonebridge.types import (
    TransformationType,
    TransformOptions,
    TransformRequest,
    TransformResponse,
    Priority,
    AnalysisType
)

options = TransformOptions(
    preserve_formatting=True,
    target_audience="executive"
)

request = TransformRequest(
    text="Your text here",
    transformation_type=TransformationType.SOFTEN,
    intensity=2,
    options=options
)

# The client methods accept both enum values and strings
result = client.transform.transform(
    text=request.text,
    transformation_type=request.transformation_type,
    intensity=request.intensity,
    options=request.options
)
```

## API Reference

### Client Initialization

```python
ToneBridgeClient(
    api_key: Optional[str] = None,
    base_url: str = "https://api.tonebridge.io/api/v1",
    timeout: int = 30,
    max_retries: int = 3,
    enable_websocket: bool = False,
    on_connect: Optional[Callable] = None,
    on_disconnect: Optional[Callable] = None,
    on_message: Optional[Callable] = None,
    on_error: Optional[Callable] = None
)
```

### Transform Service Methods

- `transform(text, transformation_type, intensity, options, metadata)` - General transformation
- `soften(text, intensity, options)` - Soften harsh language
- `clarify(text, intensity, options)` - Improve clarity
- `structure(text, intensity, options)` - Structure text
- `summarize(text, intensity, options)` - Summarize text
- `transform_terminology(text, options)` - Convert technical terms
- `structure_requirements(text, options)` - Structure requirements
- `complete_background(text, options)` - Complete background info
- `adjust_tone(text, intensity, target_tone)` - Adjust tone
- `custom_transform(text, instructions, options)` - Custom transformation
- `batch_transform(items, parallel, stop_on_error)` - Batch transformation
- `get_history(limit, offset)` - Get transformation history

### Analyze Service Methods

- `analyze(text, analysis_types, include_suggestions, metadata)` - General analysis
- `analyze_tone(text)` - Analyze tone
- `analyze_clarity(text)` - Get clarity score
- `analyze_priority(text)` - Determine priority
- `analyze_sentiment(text)` - Analyze sentiment
- `comprehensive_analysis(text, include_suggestions)` - Full analysis
- `score_priority(text, context)` - Score using Eisenhower Matrix
- `batch_score_priorities(messages)` - Batch priority scoring
- `check_needs_transformation(text)` - Check if transformation needed
- `get_suggestions(text)` - Get improvement suggestions

### Auto-Transform Service Methods

- `get_config(tenant_id)` - Get configuration
- `update_config(config, tenant_id)` - Update configuration
- `enable(tenant_id)` - Enable auto-transform
- `disable(tenant_id)` - Disable auto-transform
- `evaluate(context)` - Evaluate message
- `transform(context, transformation)` - Apply transformation
- `get_rules(tenant_id)` - Get all rules
- `create_rule(rule, tenant_id)` - Create rule
- `update_rule(rule_id, updates, tenant_id)` - Update rule
- `delete_rule(rule_id, tenant_id)` - Delete rule
- `get_templates()` - Get rule templates
- `apply_template(template_id, tenant_id)` - Apply template

## Examples

### Flask Integration

```python
from flask import Flask, request, jsonify
from tonebridge import ToneBridgeClient

app = Flask(__name__)
client = ToneBridgeClient(api_key="your-api-key")

@app.route("/transform", methods=["POST"])
def transform():
    try:
        data = request.json
        result = client.transform.soften(data["text"])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views import View
from tonebridge import ToneBridgeClient
import json

class TransformView(View):
    def __init__(self):
        super().__init__()
        self.client = ToneBridgeClient(api_key=settings.TONEBRIDGE_API_KEY)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            result = self.client.transform.soften(data["text"])
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tonebridge import ToneBridgeClient

app = FastAPI()
client = ToneBridgeClient(api_key="your-api-key")

class TransformRequest(BaseModel):
    text: str
    intensity: int = 2

@app.post("/transform")
async def transform(request: TransformRequest):
    try:
        result = client.transform.soften(
            request.text,
            intensity=request.intensity
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### CLI Tool

```python
#!/usr/bin/env python
import click
from tonebridge import ToneBridgeClient

@click.command()
@click.argument("text")
@click.option("--type", default="soften", help="Transformation type")
@click.option("--intensity", default=2, help="Intensity (0-3)")
@click.option("--api-key", envvar="TONEBRIDGE_API_KEY")
def transform(text, type, intensity, api_key):
    """Transform text using ToneBridge"""
    client = ToneBridgeClient(api_key=api_key)
    
    transform_func = getattr(client.transform, type)
    result = transform_func(text, intensity=intensity)
    
    print(result["data"]["transformed_text"])

if __name__ == "__main__":
    transform()
```

## Environment Variables

```bash
# .env
TONEBRIDGE_API_KEY=your-api-key
TONEBRIDGE_BASE_URL=https://api.tonebridge.io/api/v1
```

```python
import os
from tonebridge import ToneBridgeClient

client = ToneBridgeClient(
    api_key=os.getenv("TONEBRIDGE_API_KEY"),
    base_url=os.getenv("TONEBRIDGE_BASE_URL", "https://api.tonebridge.io/api/v1")
)
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=tonebridge

# Run specific test
pytest tests/test_transform.py
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Support

- Documentation: [https://docs.tonebridge.io](https://docs.tonebridge.io)
- API Reference: [https://api.tonebridge.io/docs](https://api.tonebridge.io/docs)
- Issues: [GitHub Issues](https://github.com/tonebridge/python-sdk/issues)
- Email: support@tonebridge.io

## License

MIT © ToneBridge

---

Made with ❤️ by the ToneBridge Team