import axios from 'axios';
import { EventBroadcaster } from '../services/eventBroadcaster';
import { logger } from '../utils/logger';
import { v4 as uuidv4 } from 'uuid';

interface TransformRequest {
  id?: string;
  text: string;
  transformation_type: string;
  intensity?: number;
  options?: any;
  metadata?: any;
}

interface TransformResponse {
  id: string;
  success: boolean;
  original_text: string;
  transformed_text: string;
  transformation_type: string;
  intensity: number;
  processing_time_ms: number;
  timestamp: string;
}

export class TransformHandler {
  private apiUrl: string;
  private eventBroadcaster: EventBroadcaster;

  constructor(eventBroadcaster: EventBroadcaster) {
    this.apiUrl = process.env.API_URL || 'http://localhost:8000';
    this.eventBroadcaster = eventBroadcaster;
  }

  async handle(request: TransformRequest, user: any): Promise<TransformResponse> {
    const requestId = request.id || uuidv4();
    const startTime = Date.now();

    try {
      logger.info(`Processing transform request ${requestId} for user ${user.id}`);

      // Validate request
      if (!request.text) {
        throw new Error('Text is required');
      }

      if (!request.transformation_type) {
        throw new Error('Transformation type is required');
      }

      // Call the transformation API
      const response = await axios.post(
        `${this.apiUrl}/api/v1/transform`,
        {
          text: request.text,
          transformation_type: request.transformation_type,
          intensity: request.intensity || 2,
          options: request.options,
          metadata: {
            ...request.metadata,
            user_id: user.id,
            tenant_id: user.tenantId,
            request_id: requestId,
            source: 'websocket'
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'X-Request-ID': requestId
          }
        }
      );

      const processingTime = Date.now() - startTime;

      const result: TransformResponse = {
        id: requestId,
        success: true,
        original_text: response.data.data.original_text,
        transformed_text: response.data.data.transformed_text,
        transformation_type: response.data.data.transformation_type,
        intensity: response.data.data.intensity,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      };

      // Broadcast success event
      this.eventBroadcaster.broadcastToUser(user.id, 'transform_success', result);

      // Log metrics
      logger.info(`Transform request ${requestId} completed in ${processingTime}ms`);

      return result;
    } catch (error: any) {
      const processingTime = Date.now() - startTime;
      
      logger.error(`Transform request ${requestId} failed:`, error);

      // Broadcast error event
      this.eventBroadcaster.broadcastToUser(user.id, 'transform_error', {
        id: requestId,
        error: error.message,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async handleBatch(requests: TransformRequest[], user: any): Promise<TransformResponse[]> {
    const results = await Promise.all(
      requests.map(request => 
        this.handle(request, user).catch(error => ({
          id: request.id || uuidv4(),
          success: false,
          error: error.message,
          original_text: request.text,
          transformed_text: '',
          transformation_type: request.transformation_type,
          intensity: request.intensity || 2,
          processing_time_ms: 0,
          timestamp: new Date().toISOString()
        }))
      )
    );

    return results;
  }
}