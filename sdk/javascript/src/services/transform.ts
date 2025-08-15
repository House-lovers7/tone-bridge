/**
 * Transform Service
 * Handles text transformation operations
 */

import { AxiosInstance } from 'axios';
import {
  TransformRequest,
  TransformResponse,
  BatchTransformRequest,
  BatchTransformResponse,
  TransformationType,
  TransformOptions
} from '../types';
import { API_ENDPOINTS, MAX_TEXT_LENGTH, DEFAULT_INTENSITY } from '../constants';
import { ValidationError } from '../errors';

export class TransformService {
  constructor(private axios: AxiosInstance) {}

  /**
   * Transform text
   * @param request Transform request
   * @returns Transform response
   * @example
   * ```typescript
   * const result = await client.transform.transform({
   *   text: "This needs to be softer",
   *   transformation_type: "soften",
   *   intensity: 2
   * });
   * ```
   */
  async transform(request: TransformRequest): Promise<TransformResponse> {
    this.validateTransformRequest(request);

    const response = await this.axios.post<TransformResponse>(
      API_ENDPOINTS.TRANSFORM,
      request
    );

    return response.data;
  }

  /**
   * Quick transform with soften
   * @param text Text to soften
   * @param intensity Transformation intensity (0-3)
   */
  async soften(
    text: string,
    intensity: number = DEFAULT_INTENSITY,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'soften',
      intensity,
      options
    });
  }

  /**
   * Quick transform with clarify
   * @param text Text to clarify
   * @param intensity Transformation intensity (0-3)
   */
  async clarify(
    text: string,
    intensity: number = DEFAULT_INTENSITY,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'clarify',
      intensity,
      options
    });
  }

  /**
   * Quick transform with structure
   * @param text Text to structure
   * @param intensity Transformation intensity (0-3)
   */
  async structure(
    text: string,
    intensity: number = DEFAULT_INTENSITY,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'structure',
      intensity,
      options
    });
  }

  /**
   * Quick transform with summarize
   * @param text Text to summarize
   * @param intensity Transformation intensity (0-3)
   */
  async summarize(
    text: string,
    intensity: number = DEFAULT_INTENSITY,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'summarize',
      intensity,
      options
    });
  }

  /**
   * Transform terminology (technical to non-technical)
   * @param text Text with technical terms
   */
  async transformTerminology(
    text: string,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'terminology',
      intensity: DEFAULT_INTENSITY,
      options
    });
  }

  /**
   * Structure requirements into 4 quadrants
   * @param text Unstructured requirements
   */
  async structureRequirements(
    text: string,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    const response = await this.axios.post<TransformResponse>(
      API_ENDPOINTS.STRUCTURE_REQUIREMENTS,
      {
        text,
        options
      }
    );

    return response.data;
  }

  /**
   * Complete background information
   * @param text Text with potentially missing background
   */
  async completeBackground(
    text: string,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    const response = await this.axios.post<TransformResponse>(
      API_ENDPOINTS.COMPLETE_BACKGROUND,
      {
        text,
        options
      }
    );

    return response.data;
  }

  /**
   * Adjust tone with specific intensity
   * @param text Text to adjust
   * @param intensity Tone adjustment intensity (0-3)
   */
  async adjustTone(
    text: string,
    intensity: number,
    targetTone?: string
  ): Promise<TransformResponse> {
    const response = await this.axios.post<TransformResponse>(
      API_ENDPOINTS.ADJUST_TONE,
      {
        text,
        intensity,
        target_tone: targetTone
      }
    );

    return response.data;
  }

  /**
   * Auto-detect optimal transformation intensity
   * @param text Text to analyze
   * @param transformationType Type of transformation
   */
  async autoDetectIntensity(
    text: string,
    transformationType: TransformationType
  ): Promise<{ intensity: number; confidence: number }> {
    const response = await this.axios.post(
      API_ENDPOINTS.AUTO_DETECT_INTENSITY,
      {
        text,
        transformation_type: transformationType
      }
    );

    return response.data;
  }

  /**
   * Get available tone presets
   */
  async getTonePresets(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    settings: any;
  }>> {
    const response = await this.axios.get(API_ENDPOINTS.TONE_PRESETS);
    return response.data;
  }

  /**
   * Batch transform multiple texts
   * @param request Batch transform request
   */
  async batchTransform(
    request: BatchTransformRequest
  ): Promise<BatchTransformResponse> {
    if (!request.items || request.items.length === 0) {
      throw new ValidationError('No items to transform');
    }

    // Validate each item
    request.items.forEach(item => this.validateTransformRequest(item));

    const response = await this.axios.post<BatchTransformResponse>(
      API_ENDPOINTS.BATCH_TRANSFORM,
      request
    );

    return response.data;
  }

  /**
   * Transform with custom instructions
   * @param text Text to transform
   * @param instructions Custom transformation instructions
   */
  async customTransform(
    text: string,
    instructions: string,
    options?: TransformOptions
  ): Promise<TransformResponse> {
    return this.transform({
      text,
      transformation_type: 'custom',
      intensity: DEFAULT_INTENSITY,
      options: {
        ...options,
        custom_instructions: instructions
      }
    });
  }

  /**
   * Get transformation history
   * @param limit Number of items to retrieve
   * @param offset Offset for pagination
   */
  async getHistory(limit: number = 10, offset: number = 0): Promise<any> {
    const response = await this.axios.get(API_ENDPOINTS.HISTORY, {
      params: { limit, offset }
    });

    return response.data;
  }

  /**
   * Validate transform request
   */
  private validateTransformRequest(request: TransformRequest): void {
    if (!request.text) {
      throw new ValidationError('Text is required');
    }

    if (request.text.length > MAX_TEXT_LENGTH) {
      throw new ValidationError(
        `Text exceeds maximum length of ${MAX_TEXT_LENGTH} characters`
      );
    }

    if (!request.transformation_type) {
      throw new ValidationError('Transformation type is required');
    }

    if (
      request.intensity !== undefined &&
      (request.intensity < 0 || request.intensity > 3)
    ) {
      throw new ValidationError('Intensity must be between 0 and 3');
    }
  }
}