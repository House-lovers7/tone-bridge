# ToneBridge WebSocket Server

Real-time WebSocket server for ToneBridge platform, enabling instant communication and live transformation features.

## Features

- 🚀 **Real-time Transformations**: Instant text transformation via WebSocket
- 📊 **Live Analysis**: Real-time text analysis and sentiment detection
- 🔄 **Auto-Transform**: Automatic transformation based on rules
- 📢 **Event Broadcasting**: Multi-channel event distribution
- 👥 **Presence Management**: User online/offline status tracking
- 🔐 **Secure Authentication**: JWT and API key support
- 📈 **Horizontal Scaling**: Redis adapter for multi-instance deployment
- 📉 **Metrics & Monitoring**: Built-in performance tracking
- 💬 **Collaboration Support**: Real-time collaboration rooms
- 🔔 **Notifications**: Push notifications to users and channels

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Clients   │────▶│   Socket.IO  │────▶│    Redis    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   Handlers   │     │   Pub/Sub   │
                    └──────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Backend API │
                    └──────────────┘
```

## Installation

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Development mode
npm run dev

# Production mode
npm start
```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Server Configuration
PORT=3001
NODE_ENV=production

# CORS Configuration
CORS_ORIGIN=http://localhost:3000,http://localhost:8080

# Authentication
JWT_SECRET=your-jwt-secret-here

# API Configuration
API_URL=http://localhost:8000

# Redis Configuration (for scaling)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=info
```

## WebSocket Events

### Client → Server Events

#### Connection
```javascript
// Connect with authentication
const socket = io('ws://localhost:3001', {
  auth: {
    token: 'your-jwt-or-api-key'
  }
});
```

#### Subscribe to Channels
```javascript
socket.emit('subscribe', { channel: 'transformations' });
socket.emit('unsubscribe', { channel: 'transformations' });
```

#### Transform Text
```javascript
socket.emit('transform', {
  text: 'Text to transform',
  transformation_type: 'soften',
  intensity: 2,
  options: {}
}, (response) => {
  if (response.success) {
    console.log('Transformed:', response.data.transformed_text);
  }
});
```

#### Analyze Text
```javascript
socket.emit('analyze', {
  text: 'Text to analyze',
  analysis_types: ['tone', 'clarity', 'sentiment'],
  include_suggestions: true
}, (response) => {
  if (response.success) {
    console.log('Analysis:', response.data);
  }
});
```

#### Auto-Transform
```javascript
socket.emit('auto_transform', {
  message: 'Message to auto-transform',
  platform: 'slack',
  channel_id: 'general'
}, (response) => {
  if (response.success) {
    console.log('Auto-transformed:', response.data);
  }
});
```

#### Collaboration
```javascript
// Join collaboration room
socket.emit('join_collaboration', { roomId: 'doc-123' });

// Send collaboration update
socket.emit('collaborate', {
  roomId: 'doc-123',
  action: 'edit',
  payload: { line: 5, text: 'Updated text' }
});

// Leave collaboration room
socket.emit('leave_collaboration', { roomId: 'doc-123' });
```

#### Presence
```javascript
// Update presence status
socket.emit('presence_update', { status: 'online' }); // online, away, busy, offline

// Typing indicators
socket.emit('typing_start', { channel: 'general' });
socket.emit('typing_stop', { channel: 'general' });
```

#### Health Check
```javascript
socket.emit('ping'); // Server responds with 'pong'
```

### Server → Client Events

#### Subscription Events
```javascript
socket.on('subscribed', (data) => {
  console.log('Subscribed to:', data.channel);
});

socket.on('unsubscribed', (data) => {
  console.log('Unsubscribed from:', data.channel);
});
```

#### Transformation Events
```javascript
socket.on('transform_success', (data) => {
  console.log('Transform completed:', data);
});

socket.on('transform_error', (data) => {
  console.error('Transform failed:', data.error);
});

socket.on('transformation_event', (data) => {
  console.log('Someone transformed text:', data);
});
```

#### Analysis Events
```javascript
socket.on('analyze_success', (data) => {
  console.log('Analysis completed:', data);
});

socket.on('analyze_error', (data) => {
  console.error('Analysis failed:', data.error);
});

socket.on('analysis_event', (data) => {
  console.log('Someone analyzed text:', data);
});
```

#### Auto-Transform Events
```javascript
socket.on('auto_transform_success', (data) => {
  console.log('Auto-transform completed:', data);
});

socket.on('auto_transform_skipped', (data) => {
  console.log('Auto-transform skipped:', data);
});

socket.on('auto_transform_error', (data) => {
  console.error('Auto-transform failed:', data.error);
});
```

#### Collaboration Events
```javascript
socket.on('collaboration_update', (data) => {
  console.log('Collaboration update:', data);
});

socket.on('user_joined_collaboration', (data) => {
  console.log('User joined:', data.userId);
});

socket.on('user_left_collaboration', (data) => {
  console.log('User left:', data.userId);
});
```

#### Presence Events
```javascript
socket.on('presence_update', (data) => {
  console.log('User presence changed:', data);
});

socket.on('user_typing', (data) => {
  console.log('User is typing:', data.userId);
});

socket.on('user_stopped_typing', (data) => {
  console.log('User stopped typing:', data.userId);
});
```

#### System Events
```javascript
socket.on('notification', (data) => {
  console.log('Notification:', data);
});

socket.on('system_message', (data) => {
  console.log('System message:', data);
});

socket.on('error', (data) => {
  console.error('Error:', data);
});
```

## Default Channels

The server automatically creates these public channels:

- `transformations` - Text transformation events
- `analysis` - Text analysis events
- `auto-transform` - Auto-transformation events
- `general` - General communication
- `notifications` - System notifications

## Testing

### Unit Tests
```bash
npm test
```

### Test Client
Open `test-client.html` in a browser to test WebSocket connections interactively.

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery quick --count 100 --num 10 ws://localhost:3001
```

## Docker Deployment

### Build Image
```bash
docker build -t tonebridge-websocket .
```

### Run Container
```bash
docker run -p 3001:3001 \
  -e JWT_SECRET=your-secret \
  -e API_URL=http://api:8000 \
  -e REDIS_URL=redis://redis:6379 \
  tonebridge-websocket
```

### Docker Compose
```yaml
websocket:
  build: ./services/websocket-server
  ports:
    - "3001:3001"
  environment:
    - NODE_ENV=production
    - JWT_SECRET=${JWT_SECRET}
    - API_URL=http://api:8000
    - REDIS_URL=redis://redis:6379
  depends_on:
    - redis
    - api
```

## Scaling

### Horizontal Scaling with Redis

The server supports horizontal scaling using Redis as a message broker:

1. **Configure Redis**: Set `REDIS_URL` in environment variables
2. **Deploy Multiple Instances**: Run multiple server instances
3. **Load Balancer**: Use nginx or HAProxy with sticky sessions

Example nginx configuration:
```nginx
upstream websocket {
    ip_hash;  # Sticky sessions
    server websocket1:3001;
    server websocket2:3001;
    server websocket3:3001;
}

server {
    listen 80;
    
    location /socket.io/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Check Endpoint
```bash
curl http://localhost:3001/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "connections": 42
}
```

### Metrics

The server tracks:
- Total connections
- Active connections
- Messages per second
- Average response time
- Error rate
- Memory usage
- CPU usage

Access metrics via WebSocket:
```javascript
socket.on('metrics_update', (metrics) => {
  console.log('Server metrics:', metrics);
});
```

## Security

### Authentication Methods

1. **JWT Token**: Bearer token in auth
2. **API Key**: X-API-Key header
3. **Session-based**: Cookie authentication (future)

### Best Practices

- Always use HTTPS/WSS in production
- Implement rate limiting
- Validate all input data
- Use environment variables for secrets
- Enable CORS only for trusted origins
- Implement request timeouts
- Monitor for unusual activity

## Performance Optimization

### Tips for Production

1. **Use WebSocket transport only**: Disable polling
   ```javascript
   const socket = io(url, {
     transports: ['websocket']
   });
   ```

2. **Implement connection pooling**: Reuse connections
3. **Enable compression**: Use Socket.IO compression
4. **Optimize Redis**: Use Redis clustering for high load
5. **Monitor memory**: Watch for memory leaks
6. **Use PM2**: Process manager for production

## Troubleshooting

### Common Issues

1. **Connection fails**
   - Check CORS configuration
   - Verify authentication token
   - Ensure port 3001 is accessible

2. **Messages not received**
   - Verify channel subscription
   - Check event names match
   - Ensure proper authentication

3. **High latency**
   - Check network connectivity
   - Monitor server load
   - Verify Redis performance

4. **Memory leaks**
   - Review event listener cleanup
   - Check for circular references
   - Monitor connection cleanup

## API Integration

The WebSocket server integrates with backend APIs:

- **Transform Service**: `http://api:8000/api/v1/transform`
- **Analyze Service**: `http://api:8000/api/v1/analyze`
- **Auto-Transform Service**: `http://api:8000/api/v1/auto-transform`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT

## Support

- Documentation: https://docs.tonebridge.io
- Issues: https://github.com/tonebridge/websocket-server/issues
- Email: support@tonebridge.io