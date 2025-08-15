/**
 * ToneBridge JavaScript/TypeScript SDK
 * Official SDK for ToneBridge API
 * @packageDocumentation
 */

export { ToneBridgeClient } from './client';
export { TransformService } from './services/transform';
export { AnalyzeService } from './services/analyze';
export { AutoTransformService } from './services/auto-transform';
export { WebSocketClient } from './websocket';

// Export types
export * from './types';
export * from './errors';
export * from './constants';

// Version
export const VERSION = '1.0.0';