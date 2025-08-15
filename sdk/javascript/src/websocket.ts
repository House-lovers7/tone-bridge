/**
 * WebSocket Client for real-time communication
 */

import WebSocket from 'ws';
import { EventEmitter } from 'events';
import { WebSocketConfig, WebSocketMessage } from './types';
import { WebSocketError } from './errors';

export class WebSocketClient extends EventEmitter {
  private ws?: WebSocket;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer?: NodeJS.Timeout;
  private pingTimer?: NodeJS.Timeout;
  private isConnected = false;
  private messageQueue: any[] = [];

  constructor(config: WebSocketConfig) {
    super();
    this.config = {
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 5000,
      ...config
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    try {
      const url = new URL(this.config.url);
      
      // Add token to query params if provided
      if (this.config.token) {
        url.searchParams.set('token', this.config.token);
      }

      this.ws = new WebSocket(url.toString());

      this.ws.on('open', () => {
        this.handleOpen();
      });

      this.ws.on('message', (data: WebSocket.Data) => {
        this.handleMessage(data);
      });

      this.ws.on('error', (error: Error) => {
        this.handleError(error);
      });

      this.ws.on('close', (code: number, reason: string) => {
        this.handleClose(code, reason);
      });

      this.ws.on('ping', () => {
        this.ws?.pong();
      });

    } catch (error) {
      this.handleError(error as Error);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isConnected = false;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.removeAllListeners();
      this.ws.close(1000, 'Client disconnect');
      this.ws = undefined;
    }

    this.emit('disconnected');
  }

  /**
   * Send message
   * @param type Message type
   * @param data Message data
   */
  send(type: string, data: any): void {
    const message: WebSocketMessage = {
      type: type as any,
      data,
      timestamp: new Date().toISOString(),
      id: this.generateId()
    };

    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      this.messageQueue.push(message);
    }
  }

  /**
   * Send transform request
   * @param data Transform data
   */
  sendTransform(data: any): void {
    this.send('transform', data);
  }

  /**
   * Send analyze request
   * @param data Analyze data
   */
  sendAnalyze(data: any): void {
    this.send('analyze', data);
  }

  /**
   * Check if connected
   */
  isConnectedToServer(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Handle connection open
   */
  private handleOpen(): void {
    this.isConnected = true;
    this.reconnectAttempts = 0;
    
    // Clear reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    // Start ping timer
    this.startPingTimer();

    // Send queued messages
    this.flushMessageQueue();

    this.emit('connected');
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: WebSocket.Data): void {
    try {
      const message = JSON.parse(data.toString());
      
      // Emit specific event based on message type
      if (message.type) {
        this.emit(message.type, message.data);
      }

      // Emit general message event
      this.emit('message', message);

    } catch (error) {
      this.emit('error', new WebSocketError('Failed to parse message'));
    }
  }

  /**
   * Handle connection error
   */
  private handleError(error: Error): void {
    this.emit('error', new WebSocketError(error.message));
  }

  /**
   * Handle connection close
   */
  private handleClose(code: number, reason: string): void {
    this.isConnected = false;
    this.clearTimers();

    // Emit close event
    this.emit('close', { code, reason });

    // Attempt reconnection if enabled
    if (this.config.reconnect && 
        this.reconnectAttempts < (this.config.maxReconnectAttempts || 5)) {
      this.scheduleReconnect();
    } else {
      this.emit('disconnected');
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    
    const delay = this.config.reconnectInterval || 5000;
    const backoff = Math.min(delay * this.reconnectAttempts, 30000);

    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      delay: backoff
    });

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, backoff);
  }

  /**
   * Start ping timer
   */
  private startPingTimer(): void {
    // Send ping every 30 seconds
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.ping();
      }
    }, 30000);
  }

  /**
   * Clear timers
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = undefined;
    }
  }

  /**
   * Flush message queue
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Add event listener (typed)
   */
  on(event: 'connected', listener: () => void): this;
  on(event: 'disconnected', listener: () => void): this;
  on(event: 'message', listener: (data: any) => void): this;
  on(event: 'error', listener: (error: Error) => void): this;
  on(event: 'close', listener: (data: { code: number; reason: string }) => void): this;
  on(event: 'reconnecting', listener: (data: { attempt: number; delay: number }) => void): this;
  on(event: 'transform', listener: (data: any) => void): this;
  on(event: 'analyze', listener: (data: any) => void): this;
  on(event: 'notification', listener: (data: any) => void): this;
  on(event: string, listener: (...args: any[]) => void): this {
    return super.on(event, listener);
  }
}