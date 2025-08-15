/**
 * Analyze Service
 * Handles text analysis operations
 */

import { AxiosInstance } from 'axios';
import {
  AnalyzeRequest,
  AnalyzeResponse,
  AnalysisType,
  Priority
} from '../types';
import { API_ENDPOINTS, MAX_TEXT_LENGTH } from '../constants';
import { ValidationError } from '../errors';

export class AnalyzeService {
  constructor(private axios: AxiosInstance) {}

  /**
   * Analyze text
   * @param request Analyze request
   * @returns Analysis results
   * @example
   * ```typescript
   * const analysis = await client.analyze.analyze({
   *   text: "This is an urgent request",
   *   analysis_types: ['tone', 'priority'],
   *   include_suggestions: true
   * });
   * ```
   */
  async analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    this.validateAnalyzeRequest(request);

    const response = await this.axios.post<AnalyzeResponse>(
      API_ENDPOINTS.ANALYZE,
      request
    );

    return response.data;
  }

  /**
   * Quick analyze for tone
   * @param text Text to analyze
   */
  async analyzeTone(text: string): Promise<string> {
    const result = await this.analyze({
      text,
      analysis_types: ['tone']
    });

    return result.data.tone;
  }

  /**
   * Quick analyze for clarity
   * @param text Text to analyze
   */
  async analyzeClarity(text: string): Promise<number> {
    const result = await this.analyze({
      text,
      analysis_types: ['clarity']
    });

    return result.data.clarity_score;
  }

  /**
   * Quick analyze for priority
   * @param text Text to analyze
   */
  async analyzePriority(text: string): Promise<{
    priority: Priority;
    quadrant?: string;
  }> {
    const result = await this.analyze({
      text,
      analysis_types: ['priority']
    });

    return {
      priority: result.data.priority,
      quadrant: result.data.priority_quadrant
    };
  }

  /**
   * Quick analyze for sentiment
   * @param text Text to analyze
   */
  async analyzeSentiment(text: string): Promise<{
    polarity: number;
    subjectivity: number;
  }> {
    const result = await this.analyze({
      text,
      analysis_types: ['sentiment']
    });

    return result.data.sentiment;
  }

  /**
   * Comprehensive analysis with all types
   * @param text Text to analyze
   * @param includeSuggestions Include improvement suggestions
   */
  async comprehensiveAnalysis(
    text: string,
    includeSuggestions: boolean = true
  ): Promise<AnalyzeResponse> {
    return this.analyze({
      text,
      analysis_types: [
        'tone',
        'clarity',
        'priority',
        'sentiment',
        'structure',
        'completeness'
      ],
      include_suggestions: includeSuggestions
    });
  }

  /**
   * Score priority using Eisenhower Matrix
   * @param text Text to score
   * @param context Additional context
   */
  async scorePriority(
    text: string,
    context?: Record<string, any>
  ): Promise<{
    score: number;
    quadrant: string;
    urgency: number;
    importance: number;
    reasoning: string;
  }> {
    const response = await this.axios.post(
      API_ENDPOINTS.SCORE_PRIORITY,
      {
        text,
        context
      }
    );

    return response.data;
  }

  /**
   * Batch score priorities for multiple messages
   * @param messages Array of messages to score
   */
  async batchScorePriorities(
    messages: Array<{ id: string; text: string; context?: any }>
  ): Promise<Array<{
    id: string;
    score: number;
    quadrant: string;
    ranking: number;
  }>> {
    const response = await this.axios.post(
      API_ENDPOINTS.BATCH_SCORE_PRIORITIES,
      {
        messages
      }
    );

    return response.data;
  }

  /**
   * Check if message needs transformation
   * @param text Text to check
   * @returns Recommendation for transformation
   */
  async checkNeedsTransformation(text: string): Promise<{
    needs_transformation: boolean;
    recommended_type?: string;
    confidence: number;
    reasons: string[];
  }> {
    const analysis = await this.comprehensiveAnalysis(text, true);
    
    const needsTransformation = 
      analysis.data.clarity_score < 70 ||
      analysis.data.tone === 'harsh' ||
      analysis.data.tone === 'technical' ||
      (analysis.data.sentiment?.polarity || 0) < -0.3;

    const reasons = [];
    if (analysis.data.clarity_score < 70) {
      reasons.push('Low clarity score');
    }
    if (analysis.data.tone === 'harsh') {
      reasons.push('Harsh tone detected');
    }
    if (analysis.data.tone === 'technical') {
      reasons.push('Technical language detected');
    }
    if ((analysis.data.sentiment?.polarity || 0) < -0.3) {
      reasons.push('Negative sentiment');
    }

    let recommendedType = 'soften';
    if (analysis.data.clarity_score < 60) {
      recommendedType = 'clarify';
    } else if (analysis.data.tone === 'technical') {
      recommendedType = 'terminology';
    }

    return {
      needs_transformation: needsTransformation,
      recommended_type: needsTransformation ? recommendedType : undefined,
      confidence: needsTransformation ? 0.8 : 0.2,
      reasons
    };
  }

  /**
   * Get improvement suggestions
   * @param text Text to get suggestions for
   */
  async getSuggestions(text: string): Promise<string[]> {
    const result = await this.analyze({
      text,
      include_suggestions: true
    });

    return result.data.suggestions || [];
  }

  /**
   * Validate analyze request
   */
  private validateAnalyzeRequest(request: AnalyzeRequest): void {
    if (!request.text) {
      throw new ValidationError('Text is required');
    }

    if (request.text.length > MAX_TEXT_LENGTH) {
      throw new ValidationError(
        `Text exceeds maximum length of ${MAX_TEXT_LENGTH} characters`
      );
    }
  }
}