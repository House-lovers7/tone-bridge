import { Server } from 'socket.io';
import { logger } from '../utils/logger';

export class EventBroadcaster {
  private io: Server;

  constructor(io: Server) {
    this.io = io;
  }

  // Broadcast to all connected clients
  broadcastToAll(event: string, data: any): void {
    this.io.emit(event, data);
    logger.debug(`Broadcasted ${event} to all clients`);
  }

  // Broadcast to a specific user
  broadcastToUser(userId: string, event: string, data: any): void {
    this.io.to(`user:${userId}`).emit(event, data);
    logger.debug(`Broadcasted ${event} to user ${userId}`);
  }

  // Broadcast to a specific tenant
  broadcastToTenant(tenantId: string, event: string, data: any): void {
    this.io.to(`tenant:${tenantId}`).emit(event, data);
    logger.debug(`Broadcasted ${event} to tenant ${tenantId}`);
  }

  // Broadcast to a specific channel
  broadcastToChannel(channel: string, event: string, data: any): void {
    this.io.to(channel).emit(event, data);
    logger.debug(`Broadcasted ${event} to channel ${channel}`);
  }

  // Broadcast to multiple channels
  broadcastToChannels(channels: string[], event: string, data: any): void {
    channels.forEach(channel => {
      this.broadcastToChannel(channel, event, data);
    });
  }

  // Broadcast to specific socket IDs
  broadcastToSockets(socketIds: string[], event: string, data: any): void {
    socketIds.forEach(socketId => {
      this.io.to(socketId).emit(event, data);
    });
    logger.debug(`Broadcasted ${event} to ${socketIds.length} sockets`);
  }

  // Broadcast transformation event
  broadcastTransformation(data: {
    userId: string;
    tenantId: string;
    transformationType: string;
    originalText: string;
    transformedText: string;
    metadata?: any;
  }): void {
    const event = 'transformation_event';
    
    // Broadcast to tenant
    this.broadcastToTenant(data.tenantId, event, {
      type: 'transformation',
      userId: data.userId,
      transformationType: data.transformationType,
      timestamp: new Date().toISOString(),
      metadata: data.metadata
    });

    // Broadcast to transformations channel
    this.broadcastToChannel('transformations', event, {
      userId: data.userId,
      transformationType: data.transformationType,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast analysis event
  broadcastAnalysis(data: {
    userId: string;
    tenantId: string;
    analysisTypes: string[];
    results: any;
    metadata?: any;
  }): void {
    const event = 'analysis_event';
    
    // Broadcast to tenant
    this.broadcastToTenant(data.tenantId, event, {
      type: 'analysis',
      userId: data.userId,
      analysisTypes: data.analysisTypes,
      timestamp: new Date().toISOString(),
      metadata: data.metadata
    });

    // Broadcast to analysis channel
    this.broadcastToChannel('analysis', event, {
      userId: data.userId,
      analysisTypes: data.analysisTypes,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast auto-transform event
  broadcastAutoTransform(data: {
    userId: string;
    tenantId: string;
    ruleApplied: string;
    transformed: boolean;
    metadata?: any;
  }): void {
    const event = 'auto_transform_event';
    
    // Broadcast to tenant
    this.broadcastToTenant(data.tenantId, event, {
      type: 'auto_transform',
      userId: data.userId,
      ruleApplied: data.ruleApplied,
      transformed: data.transformed,
      timestamp: new Date().toISOString(),
      metadata: data.metadata
    });

    // Broadcast to auto-transform channel
    this.broadcastToChannel('auto-transform', event, {
      userId: data.userId,
      ruleApplied: data.ruleApplied,
      transformed: data.transformed,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast notification
  broadcastNotification(data: {
    userId?: string;
    tenantId?: string;
    type: 'info' | 'warning' | 'error' | 'success';
    title: string;
    message: string;
    metadata?: any;
  }): void {
    const notification = {
      type: data.type,
      title: data.title,
      message: data.message,
      timestamp: new Date().toISOString(),
      metadata: data.metadata
    };

    if (data.userId) {
      this.broadcastToUser(data.userId, 'notification', notification);
    } else if (data.tenantId) {
      this.broadcastToTenant(data.tenantId, 'notification', notification);
    } else {
      this.broadcastToChannel('notifications', 'notification', notification);
    }
  }

  // Broadcast system message
  broadcastSystemMessage(message: string, type: 'info' | 'warning' | 'maintenance' = 'info'): void {
    this.broadcastToAll('system_message', {
      type,
      message,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast metrics update
  broadcastMetrics(metrics: any): void {
    this.broadcastToChannel('metrics', 'metrics_update', {
      ...metrics,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast collaboration event
  broadcastCollaboration(roomId: string, data: {
    userId: string;
    action: string;
    payload: any;
  }): void {
    this.broadcastToChannel(`collab:${roomId}`, 'collaboration_event', {
      ...data,
      timestamp: new Date().toISOString()
    });
  }

  // Broadcast presence update
  broadcastPresenceUpdate(data: {
    userId: string;
    status: string;
    channels?: string[];
  }): void {
    const presenceData = {
      userId: data.userId,
      status: data.status,
      timestamp: new Date().toISOString()
    };

    // Broadcast to user's channels
    if (data.channels) {
      data.channels.forEach(channel => {
        this.broadcastToChannel(channel, 'presence_update', presenceData);
      });
    }
  }

  // Get connected sockets count
  getConnectionCount(): number {
    return this.io.engine.clientsCount;
  }

  // Get rooms info
  getRoomsInfo(): Map<string, Set<string>> {
    return this.io.sockets.adapter.rooms;
  }
}