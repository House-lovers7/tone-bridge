import axios from 'axios';
import { EventBroadcaster } from '../services/eventBroadcaster';
import { logger } from '../utils/logger';
import { v4 as uuidv4 } from 'uuid';

interface MessageContext {
  message: string;
  user_id: string;
  tenant_id: string;
  platform: string;
  channel_id?: string;
  recipient_ids?: string[];
  metadata?: any;
}

interface AutoTransformResponse {
  id: string;
  success: boolean;
  original_text: string;
  transformed_text: string;
  should_transform: boolean;
  rule_applied?: {
    id: string;
    name: string;
    transformation_type: string;
    intensity: number;
  };
  confidence: number;
  processing_time_ms: number;
  timestamp: string;
}

export class AutoTransformHandler {
  private apiUrl: string;
  private eventBroadcaster: EventBroadcaster;

  constructor(eventBroadcaster: EventBroadcaster) {
    this.apiUrl = process.env.API_URL || 'http://localhost:8000';
    this.eventBroadcaster = eventBroadcaster;
  }

  async handle(context: MessageContext, user: any): Promise<AutoTransformResponse> {
    const requestId = uuidv4();
    const startTime = Date.now();

    try {
      logger.info(`Processing auto-transform request ${requestId} for user ${user.id}`);

      // Validate request
      if (!context.message) {
        throw new Error('Message is required');
      }

      // Ensure context has required fields
      const enrichedContext = {
        ...context,
        user_id: context.user_id || user.id,
        tenant_id: context.tenant_id || user.tenantId,
        platform: context.platform || 'websocket'
      };

      // First, evaluate if transformation is needed
      const evaluateResponse = await axios.post(
        `${this.apiUrl}/api/v1/auto-transform/evaluate`,
        enrichedContext,
        {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'X-Request-ID': requestId
          }
        }
      );

      const evaluationResult = evaluateResponse.data;

      // If no transformation needed, return original text
      if (!evaluationResult.should_transform) {
        const processingTime = Date.now() - startTime;
        
        const result: AutoTransformResponse = {
          id: requestId,
          success: true,
          original_text: context.message,
          transformed_text: context.message,
          should_transform: false,
          confidence: evaluationResult.confidence || 0,
          processing_time_ms: processingTime,
          timestamp: new Date().toISOString()
        };

        // Broadcast event
        this.eventBroadcaster.broadcastToUser(user.id, 'auto_transform_skipped', result);

        return result;
      }

      // Apply transformation
      const transformResponse = await axios.post(
        `${this.apiUrl}/api/v1/auto-transform/apply`,
        enrichedContext,
        {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'X-Request-ID': requestId
          }
        }
      );

      const processingTime = Date.now() - startTime;

      const result: AutoTransformResponse = {
        id: requestId,
        success: true,
        original_text: transformResponse.data.original_text,
        transformed_text: transformResponse.data.transformed_text,
        should_transform: true,
        rule_applied: transformResponse.data.rule_applied ? {
          id: transformResponse.data.rule_applied.id,
          name: transformResponse.data.rule_applied.rule_name,
          transformation_type: transformResponse.data.rule_applied.transformation_type,
          intensity: transformResponse.data.rule_applied.transformation_intensity
        } : undefined,
        confidence: transformResponse.data.confidence,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      };

      // Broadcast success event
      this.eventBroadcaster.broadcastToUser(user.id, 'auto_transform_success', result);

      // Also broadcast to channel if specified
      if (context.channel_id) {
        this.eventBroadcaster.broadcastToChannel(context.channel_id, 'message_transformed', {
          user_id: user.id,
          original_text: result.original_text,
          transformed_text: result.transformed_text,
          rule_applied: result.rule_applied
        });
      }

      // Log metrics
      logger.info(`Auto-transform request ${requestId} completed in ${processingTime}ms`);

      return result;
    } catch (error: any) {
      const processingTime = Date.now() - startTime;
      
      logger.error(`Auto-transform request ${requestId} failed:`, error);

      // Broadcast error event
      this.eventBroadcaster.broadcastToUser(user.id, 'auto_transform_error', {
        id: requestId,
        error: error.message,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async getRules(user: any): Promise<any> {
    try {
      const response = await axios.get(
        `${this.apiUrl}/api/v1/auto-transform/rules`,
        {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        }
      );

      return response.data;
    } catch (error) {
      logger.error('Failed to get auto-transform rules:', error);
      throw error;
    }
  }

  async updateRule(ruleId: string, updates: any, user: any): Promise<any> {
    try {
      const response = await axios.put(
        `${this.apiUrl}/api/v1/auto-transform/rules/${ruleId}`,
        updates,
        {
          headers: {
            'Authorization': `Bearer ${user.token}`
          }
        }
      );

      // Broadcast rule update event
      this.eventBroadcaster.broadcastToTenant(user.tenantId, 'rule_updated', {
        rule_id: ruleId,
        updates,
        updated_by: user.id,
        timestamp: new Date().toISOString()
      });

      return response.data;
    } catch (error) {
      logger.error(`Failed to update rule ${ruleId}:`, error);
      throw error;
    }
  }

  async testRule(rule: any, sampleText: string, user: any): Promise<any> {
    const requestId = uuidv4();
    
    try {
      const response = await axios.post(
        `${this.apiUrl}/api/v1/auto-transform/test-rule`,
        {
          rule,
          sample_text: sampleText
        },
        {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'X-Request-ID': requestId
          }
        }
      );

      return response.data;
    } catch (error) {
      logger.error('Failed to test rule:', error);
      throw error;
    }
  }
}