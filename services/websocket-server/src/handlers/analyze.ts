import axios from 'axios';
import { EventBroadcaster } from '../services/eventBroadcaster';
import { logger } from '../utils/logger';
import { v4 as uuidv4 } from 'uuid';

interface AnalyzeRequest {
  id?: string;
  text: string;
  analysis_types?: string[];
  include_suggestions?: boolean;
  metadata?: any;
}

interface AnalyzeResponse {
  id: string;
  success: boolean;
  text: string;
  tone?: string;
  clarity_score?: number;
  priority?: string;
  priority_quadrant?: string;
  sentiment?: {
    polarity: number;
    subjectivity: number;
  };
  suggestions?: string[];
  improvements?: string[];
  processing_time_ms: number;
  timestamp: string;
}

export class AnalyzeHandler {
  private apiUrl: string;
  private eventBroadcaster: EventBroadcaster;

  constructor(eventBroadcaster: EventBroadcaster) {
    this.apiUrl = process.env.API_URL || 'http://localhost:8000';
    this.eventBroadcaster = eventBroadcaster;
  }

  async handle(request: AnalyzeRequest, user: any): Promise<AnalyzeResponse> {
    const requestId = request.id || uuidv4();
    const startTime = Date.now();

    try {
      logger.info(`Processing analyze request ${requestId} for user ${user.id}`);

      // Validate request
      if (!request.text) {
        throw new Error('Text is required');
      }

      // Default analysis types if not specified
      const analysisTypes = request.analysis_types || [
        'tone',
        'clarity',
        'priority',
        'sentiment'
      ];

      // Call the analysis API
      const response = await axios.post(
        `${this.apiUrl}/api/v1/analyze`,
        {
          text: request.text,
          analysis_types: analysisTypes,
          include_suggestions: request.include_suggestions !== false,
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

      const result: AnalyzeResponse = {
        id: requestId,
        success: true,
        text: response.data.data.text,
        tone: response.data.data.tone,
        clarity_score: response.data.data.clarity_score,
        priority: response.data.data.priority,
        priority_quadrant: response.data.data.priority_quadrant,
        sentiment: response.data.data.sentiment,
        suggestions: response.data.data.suggestions,
        improvements: response.data.data.improvements,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      };

      // Broadcast success event
      this.eventBroadcaster.broadcastToUser(user.id, 'analyze_success', result);

      // Log metrics
      logger.info(`Analyze request ${requestId} completed in ${processingTime}ms`);

      return result;
    } catch (error: any) {
      const processingTime = Date.now() - startTime;
      
      logger.error(`Analyze request ${requestId} failed:`, error);

      // Broadcast error event
      this.eventBroadcaster.broadcastToUser(user.id, 'analyze_error', {
        id: requestId,
        error: error.message,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  async handleBatch(requests: AnalyzeRequest[], user: any): Promise<AnalyzeResponse[]> {
    const results = await Promise.all(
      requests.map(request => 
        this.handle(request, user).catch(error => ({
          id: request.id || uuidv4(),
          success: false,
          error: error.message,
          text: request.text,
          processing_time_ms: 0,
          timestamp: new Date().toISOString()
        }))
      )
    );

    return results;
  }

  async handleComparison(text1: string, text2: string, user: any): Promise<any> {
    const requestId = uuidv4();
    const startTime = Date.now();

    try {
      logger.info(`Processing comparison request ${requestId} for user ${user.id}`);

      // Call the comparison API
      const response = await axios.post(
        `${this.apiUrl}/api/v1/analyze/compare-tone`,
        {
          text1,
          text2
        },
        {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'X-Request-ID': requestId
          }
        }
      );

      const processingTime = Date.now() - startTime;

      const result = {
        id: requestId,
        success: true,
        ...response.data,
        processing_time_ms: processingTime,
        timestamp: new Date().toISOString()
      };

      // Broadcast success event
      this.eventBroadcaster.broadcastToUser(user.id, 'comparison_success', result);

      return result;
    } catch (error: any) {
      logger.error(`Comparison request ${requestId} failed:`, error);
      throw error;
    }
  }
}