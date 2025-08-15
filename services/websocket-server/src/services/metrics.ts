import { logger } from '../utils/logger';

interface ConnectionMetrics {
  totalConnections: number;
  activeConnections: number;
  totalDisconnections: number;
  averageConnectionDuration: number;
  connectionsByTenant: Map<string, number>;
  connectionsByUser: Map<string, number>;
}

interface RequestMetrics {
  totalRequests: number;
  requestsByType: Map<string, number>;
  averageResponseTime: Map<string, number>;
  errorCount: number;
  errorRate: number;
}

interface PerformanceMetrics {
  cpuUsage: number;
  memoryUsage: number;
  eventLoopLag: number;
  uptime: number;
}

class MetricsCollector {
  private connectionMetrics: ConnectionMetrics;
  private requestMetrics: RequestMetrics;
  private connectionStartTimes: Map<string, number>;
  private requestStartTimes: Map<string, number>;
  private responseTimes: Map<string, number[]>;
  private startTime: number;

  constructor() {
    this.connectionMetrics = {
      totalConnections: 0,
      activeConnections: 0,
      totalDisconnections: 0,
      averageConnectionDuration: 0,
      connectionsByTenant: new Map(),
      connectionsByUser: new Map()
    };

    this.requestMetrics = {
      totalRequests: 0,
      requestsByType: new Map(),
      averageResponseTime: new Map(),
      errorCount: 0,
      errorRate: 0
    };

    this.connectionStartTimes = new Map();
    this.requestStartTimes = new Map();
    this.responseTimes = new Map();
    this.startTime = Date.now();

    // Start periodic metrics reporting
    this.startPeriodicReporting();
  }

  recordConnection(socketId: string, userId: string, tenantId: string): void {
    this.connectionMetrics.totalConnections++;
    this.connectionMetrics.activeConnections++;
    this.connectionStartTimes.set(socketId, Date.now());

    // Track by tenant
    const tenantCount = this.connectionMetrics.connectionsByTenant.get(tenantId) || 0;
    this.connectionMetrics.connectionsByTenant.set(tenantId, tenantCount + 1);

    // Track by user
    const userCount = this.connectionMetrics.connectionsByUser.get(userId) || 0;
    this.connectionMetrics.connectionsByUser.set(userId, userCount + 1);

    logger.debug(`Connection recorded: ${socketId} (User: ${userId}, Tenant: ${tenantId})`);
  }

  recordDisconnection(socketId: string): void {
    this.connectionMetrics.activeConnections--;
    this.connectionMetrics.totalDisconnections++;

    // Calculate connection duration
    const startTime = this.connectionStartTimes.get(socketId);
    if (startTime) {
      const duration = Date.now() - startTime;
      this.updateAverageConnectionDuration(duration);
      this.connectionStartTimes.delete(socketId);
    }

    logger.debug(`Disconnection recorded: ${socketId}`);
  }

  recordRequest(type: string, socketId: string): void {
    this.requestMetrics.totalRequests++;
    
    // Track by type
    const typeCount = this.requestMetrics.requestsByType.get(type) || 0;
    this.requestMetrics.requestsByType.set(type, typeCount + 1);

    // Record start time
    const requestId = `${socketId}-${Date.now()}`;
    this.requestStartTimes.set(requestId, Date.now());

    return requestId as any;
  }

  recordResponse(requestId: string, type: string): void {
    const startTime = this.requestStartTimes.get(requestId);
    if (startTime) {
      const responseTime = Date.now() - startTime;
      
      // Track response times by type
      if (!this.responseTimes.has(type)) {
        this.responseTimes.set(type, []);
      }
      this.responseTimes.get(type)!.push(responseTime);

      // Update average response time
      this.updateAverageResponseTime(type);
      
      this.requestStartTimes.delete(requestId);
    }
  }

  recordError(type: string, socketId?: string): void {
    this.requestMetrics.errorCount++;
    this.updateErrorRate();
    logger.debug(`Error recorded: ${type} (Socket: ${socketId || 'unknown'})`);
  }

  private updateAverageConnectionDuration(newDuration: number): void {
    const totalConnections = this.connectionMetrics.totalConnections;
    const currentAverage = this.connectionMetrics.averageConnectionDuration;
    
    this.connectionMetrics.averageConnectionDuration = 
      (currentAverage * (totalConnections - 1) + newDuration) / totalConnections;
  }

  private updateAverageResponseTime(type: string): void {
    const times = this.responseTimes.get(type);
    if (times && times.length > 0) {
      const average = times.reduce((a, b) => a + b, 0) / times.length;
      this.requestMetrics.averageResponseTime.set(type, average);
      
      // Keep only last 100 response times
      if (times.length > 100) {
        this.responseTimes.set(type, times.slice(-100));
      }
    }
  }

  private updateErrorRate(): void {
    if (this.requestMetrics.totalRequests > 0) {
      this.requestMetrics.errorRate = 
        this.requestMetrics.errorCount / this.requestMetrics.totalRequests;
    }
  }

  getConnectionMetrics(): ConnectionMetrics {
    return { ...this.connectionMetrics };
  }

  getRequestMetrics(): RequestMetrics {
    return { ...this.requestMetrics };
  }

  getPerformanceMetrics(): PerformanceMetrics {
    const usage = process.cpuUsage();
    const memUsage = process.memoryUsage();
    
    return {
      cpuUsage: (usage.user + usage.system) / 1000000, // Convert to seconds
      memoryUsage: memUsage.heapUsed / 1024 / 1024, // Convert to MB
      eventLoopLag: 0, // Would need additional monitoring
      uptime: (Date.now() - this.startTime) / 1000 // Convert to seconds
    };
  }

  getAllMetrics(): any {
    return {
      connections: this.getConnectionMetrics(),
      requests: this.getRequestMetrics(),
      performance: this.getPerformanceMetrics(),
      timestamp: new Date().toISOString()
    };
  }

  private startPeriodicReporting(): void {
    // Report metrics every 60 seconds
    setInterval(() => {
      const metrics = this.getAllMetrics();
      logger.info('Metrics Report:', JSON.stringify(metrics, null, 2));
    }, 60000);
  }

  reset(): void {
    this.connectionMetrics = {
      totalConnections: 0,
      activeConnections: this.connectionMetrics.activeConnections,
      totalDisconnections: 0,
      averageConnectionDuration: 0,
      connectionsByTenant: new Map(),
      connectionsByUser: new Map()
    };

    this.requestMetrics = {
      totalRequests: 0,
      requestsByType: new Map(),
      averageResponseTime: new Map(),
      errorCount: 0,
      errorRate: 0
    };

    this.responseTimes.clear();
    logger.info('Metrics reset');
  }

  // Get metrics summary for dashboard
  getSummary(): any {
    const metrics = this.getAllMetrics();
    
    return {
      status: 'healthy',
      connections: {
        active: metrics.connections.activeConnections,
        total: metrics.connections.totalConnections
      },
      requests: {
        total: metrics.requests.totalRequests,
        errorRate: `${(metrics.requests.errorRate * 100).toFixed(2)}%`
      },
      performance: {
        cpu: `${metrics.performance.cpuUsage.toFixed(2)}s`,
        memory: `${metrics.performance.memoryUsage.toFixed(2)}MB`,
        uptime: `${Math.floor(metrics.performance.uptime / 60)}m`
      },
      topEndpoints: Array.from(metrics.requests.requestsByType.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([type, count]) => ({ type, count }))
    };
  }
}

export { MetricsCollector };