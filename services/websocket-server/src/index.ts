import express from 'express';
import { createServer } from 'http';
import { Server, Socket } from 'socket.io';
import cors from 'cors';
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';
import dotenv from 'dotenv';
import { AuthMiddleware } from './middleware/auth';
import { TransformHandler } from './handlers/transform';
import { AnalyzeHandler } from './handlers/analyze';
import { AutoTransformHandler } from './handlers/autoTransform';
import { ChannelManager } from './services/channelManager';
import { EventBroadcaster } from './services/eventBroadcaster';
import { MetricsCollector } from './services/metrics';
import { logger } from './utils/logger';

dotenv.config();

const app = express();
const httpServer = createServer(app);

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    connections: io.engine.clientsCount 
  });
});

// Socket.IO configuration
const io = new Server(httpServer, {
  cors: {
    origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
    methods: ['GET', 'POST'],
    credentials: true
  },
  transports: ['websocket', 'polling'],
  pingTimeout: 60000,
  pingInterval: 25000
});

// Redis adapter for horizontal scaling
const setupRedisAdapter = async () => {
  if (process.env.REDIS_URL) {
    const pubClient = createClient({ url: process.env.REDIS_URL });
    const subClient = pubClient.duplicate();
    
    await Promise.all([pubClient.connect(), subClient.connect()]);
    
    io.adapter(createAdapter(pubClient, subClient));
    logger.info('Redis adapter configured for Socket.IO');
  }
};

// Initialize services
const authMiddleware = new AuthMiddleware();
const channelManager = new ChannelManager();
const eventBroadcaster = new EventBroadcaster(io);
const metricsCollector = new MetricsCollector();

// Initialize handlers
const transformHandler = new TransformHandler(eventBroadcaster);
const analyzeHandler = new AnalyzeHandler(eventBroadcaster);
const autoTransformHandler = new AutoTransformHandler(eventBroadcaster);

// Socket authentication middleware
io.use(async (socket: Socket, next) => {
  try {
    const token = socket.handshake.auth.token || socket.handshake.headers['x-api-key'];
    const user = await authMiddleware.authenticate(token);
    
    if (!user) {
      return next(new Error('Authentication failed'));
    }
    
    socket.data.user = user;
    socket.data.tenantId = user.tenantId;
    next();
  } catch (error) {
    logger.error('Socket authentication error:', error);
    next(new Error('Authentication error'));
  }
});

// Connection handler
io.on('connection', (socket: Socket) => {
  const userId = socket.data.user?.id;
  const tenantId = socket.data.tenantId;
  
  logger.info(`Client connected: ${socket.id} (User: ${userId}, Tenant: ${tenantId})`);
  
  // Track metrics
  metricsCollector.recordConnection(socket.id, userId, tenantId);
  
  // Join tenant room automatically
  if (tenantId) {
    socket.join(`tenant:${tenantId}`);
  }
  
  // Join user room
  if (userId) {
    socket.join(`user:${userId}`);
  }
  
  // Handle subscription to channels
  socket.on('subscribe', async (data: { channel: string }) => {
    try {
      const { channel } = data;
      
      // Validate channel access
      const hasAccess = await channelManager.validateAccess(userId, channel);
      
      if (!hasAccess) {
        socket.emit('error', { 
          type: 'SUBSCRIPTION_ERROR', 
          message: 'Access denied to channel' 
        });
        return;
      }
      
      socket.join(channel);
      socket.emit('subscribed', { channel });
      
      logger.info(`Client ${socket.id} subscribed to channel: ${channel}`);
      
      // Broadcast subscription event
      eventBroadcaster.broadcastToChannel(channel, 'user_joined', {
        userId,
        channel,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Subscription error:', error);
      socket.emit('error', { 
        type: 'SUBSCRIPTION_ERROR', 
        message: 'Failed to subscribe to channel' 
      });
    }
  });
  
  // Handle unsubscription from channels
  socket.on('unsubscribe', (data: { channel: string }) => {
    const { channel } = data;
    socket.leave(channel);
    socket.emit('unsubscribed', { channel });
    
    logger.info(`Client ${socket.id} unsubscribed from channel: ${channel}`);
    
    // Broadcast unsubscription event
    eventBroadcaster.broadcastToChannel(channel, 'user_left', {
      userId,
      channel,
      timestamp: new Date().toISOString()
    });
  });
  
  // Handle transformation requests
  socket.on('transform', async (data: any, callback: Function) => {
    try {
      metricsCollector.recordRequest('transform', socket.id);
      const result = await transformHandler.handle(data, socket.data.user);
      callback({ success: true, data: result });
      
      // Broadcast transformation event
      eventBroadcaster.broadcastToTenant(tenantId, 'transformation_completed', {
        userId,
        transformationType: data.transformation_type,
        timestamp: new Date().toISOString()
      });
    } catch (error: any) {
      logger.error('Transform error:', error);
      callback({ success: false, error: error.message });
    }
  });
  
  // Handle analysis requests
  socket.on('analyze', async (data: any, callback: Function) => {
    try {
      metricsCollector.recordRequest('analyze', socket.id);
      const result = await analyzeHandler.handle(data, socket.data.user);
      callback({ success: true, data: result });
      
      // Broadcast analysis event
      eventBroadcaster.broadcastToTenant(tenantId, 'analysis_completed', {
        userId,
        analysisTypes: data.analysis_types,
        timestamp: new Date().toISOString()
      });
    } catch (error: any) {
      logger.error('Analyze error:', error);
      callback({ success: false, error: error.message });
    }
  });
  
  // Handle auto-transform requests
  socket.on('auto_transform', async (data: any, callback: Function) => {
    try {
      metricsCollector.recordRequest('auto_transform', socket.id);
      const result = await autoTransformHandler.handle(data, socket.data.user);
      callback({ success: true, data: result });
      
      // Broadcast auto-transform event
      eventBroadcaster.broadcastToTenant(tenantId, 'auto_transform_completed', {
        userId,
        ruleApplied: result.ruleApplied,
        timestamp: new Date().toISOString()
      });
    } catch (error: any) {
      logger.error('Auto-transform error:', error);
      callback({ success: false, error: error.message });
    }
  });
  
  // Handle real-time collaboration
  socket.on('collaborate', (data: { roomId: string, action: string, payload: any }) => {
    const { roomId, action, payload } = data;
    
    // Broadcast to all users in the collaboration room
    socket.to(`collab:${roomId}`).emit('collaboration_update', {
      userId,
      action,
      payload,
      timestamp: new Date().toISOString()
    });
  });
  
  // Join collaboration room
  socket.on('join_collaboration', (data: { roomId: string }) => {
    const { roomId } = data;
    socket.join(`collab:${roomId}`);
    
    // Notify others in the room
    socket.to(`collab:${roomId}`).emit('user_joined_collaboration', {
      userId,
      roomId,
      timestamp: new Date().toISOString()
    });
  });
  
  // Leave collaboration room
  socket.on('leave_collaboration', (data: { roomId: string }) => {
    const { roomId } = data;
    socket.leave(`collab:${roomId}`);
    
    // Notify others in the room
    socket.to(`collab:${roomId}`).emit('user_left_collaboration', {
      userId,
      roomId,
      timestamp: new Date().toISOString()
    });
  });
  
  // Handle ping/pong for connection health
  socket.on('ping', () => {
    socket.emit('pong', { timestamp: new Date().toISOString() });
  });
  
  // Handle typing indicators
  socket.on('typing_start', (data: { channel: string }) => {
    socket.to(data.channel).emit('user_typing', {
      userId,
      channel: data.channel,
      timestamp: new Date().toISOString()
    });
  });
  
  socket.on('typing_stop', (data: { channel: string }) => {
    socket.to(data.channel).emit('user_stopped_typing', {
      userId,
      channel: data.channel,
      timestamp: new Date().toISOString()
    });
  });
  
  // Handle presence updates
  socket.on('presence_update', (data: { status: string }) => {
    const { status } = data;
    
    // Update user presence
    channelManager.updatePresence(userId, status);
    
    // Broadcast presence update to tenant
    eventBroadcaster.broadcastToTenant(tenantId, 'presence_changed', {
      userId,
      status,
      timestamp: new Date().toISOString()
    });
  });
  
  // Handle disconnection
  socket.on('disconnect', (reason) => {
    logger.info(`Client disconnected: ${socket.id} (Reason: ${reason})`);
    
    // Track metrics
    metricsCollector.recordDisconnection(socket.id);
    
    // Update presence
    channelManager.updatePresence(userId, 'offline');
    
    // Broadcast disconnection event
    eventBroadcaster.broadcastToTenant(tenantId, 'user_disconnected', {
      userId,
      reason,
      timestamp: new Date().toISOString()
    });
  });
  
  // Handle errors
  socket.on('error', (error) => {
    logger.error(`Socket error for ${socket.id}:`, error);
    metricsCollector.recordError('socket_error', socket.id);
  });
});

// Start server
const PORT = process.env.PORT || 3001;

const startServer = async () => {
  try {
    // Setup Redis adapter if configured
    await setupRedisAdapter();
    
    httpServer.listen(PORT, () => {
      logger.info(`WebSocket server running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`CORS origins: ${process.env.CORS_ORIGIN || 'http://localhost:3000'}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  
  // Close all connections
  io.close(() => {
    logger.info('All connections closed');
  });
  
  // Close HTTP server
  httpServer.close(() => {
    logger.info('HTTP server closed');
    process.exit(0);
  });
  
  // Force shutdown after 10 seconds
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
});

// Start the server
startServer();

export { io, app };