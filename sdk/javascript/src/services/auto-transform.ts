/**
 * Auto-Transform Service
 * Handles automatic transformation rules and configurations
 */

import { AxiosInstance } from 'axios';
import {
  AutoTransformConfig,
  AutoTransformRule,
  AutoTransformTemplate,
  MessageContext,
  TransformationResult,
  TriggerType
} from '../types';
import { ValidationError } from '../errors';

export class AutoTransformService {
  private baseUrl = '/auto-transform';

  constructor(private axios: AxiosInstance) {}

  /**
   * Get auto-transform configuration
   * @param tenantId Tenant ID
   */
  async getConfig(tenantId?: string): Promise<AutoTransformConfig> {
    const url = tenantId 
      ? `${this.baseUrl}/config/${tenantId}`
      : `${this.baseUrl}/config`;
    
    const response = await this.axios.get<AutoTransformConfig>(url);
    return response.data;
  }

  /**
   * Update auto-transform configuration
   * @param config Configuration to update
   * @param tenantId Tenant ID
   */
  async updateConfig(
    config: Partial<AutoTransformConfig>,
    tenantId?: string
  ): Promise<AutoTransformConfig> {
    const url = tenantId
      ? `${this.baseUrl}/config/${tenantId}`
      : `${this.baseUrl}/config`;

    const response = await this.axios.put<AutoTransformConfig>(url, config);
    return response.data;
  }

  /**
   * Enable auto-transform
   * @param tenantId Tenant ID
   */
  async enable(tenantId?: string): Promise<void> {
    await this.updateConfig({ enabled: true }, tenantId);
  }

  /**
   * Disable auto-transform
   * @param tenantId Tenant ID
   */
  async disable(tenantId?: string): Promise<void> {
    await this.updateConfig({ enabled: false }, tenantId);
  }

  /**
   * Evaluate if message should be auto-transformed
   * @param context Message context
   */
  async evaluate(context: MessageContext): Promise<TransformationResult> {
    this.validateMessageContext(context);

    const response = await this.axios.post<TransformationResult>(
      `${this.baseUrl}/evaluate`,
      context
    );

    return response.data;
  }

  /**
   * Apply auto-transformation
   * @param context Message context
   * @param transformation Transformation result from evaluation
   */
  async transform(
    context: MessageContext,
    transformation: TransformationResult
  ): Promise<{
    success: boolean;
    original: string;
    transformed: string;
    rule_applied: string;
    confidence: number;
  }> {
    const response = await this.axios.post(
      `${this.baseUrl}/transform`,
      {
        context,
        transformation
      }
    );

    return response.data;
  }

  /**
   * Get all rules
   * @param tenantId Tenant ID
   */
  async getRules(tenantId?: string): Promise<AutoTransformRule[]> {
    const url = tenantId
      ? `${this.baseUrl}/rules/${tenantId}`
      : `${this.baseUrl}/rules`;

    const response = await this.axios.get<AutoTransformRule[]>(url);
    return response.data;
  }

  /**
   * Get rule by ID
   * @param ruleId Rule ID
   * @param tenantId Tenant ID
   */
  async getRule(
    ruleId: string,
    tenantId?: string
  ): Promise<AutoTransformRule> {
    const url = tenantId
      ? `${this.baseUrl}/rules/${tenantId}/${ruleId}`
      : `${this.baseUrl}/rules/${ruleId}`;

    const response = await this.axios.get<AutoTransformRule>(url);
    return response.data;
  }

  /**
   * Create a new rule
   * @param rule Rule to create
   * @param tenantId Tenant ID
   */
  async createRule(
    rule: Omit<AutoTransformRule, 'id'>,
    tenantId?: string
  ): Promise<{ success: boolean; rule_id: string }> {
    this.validateRule(rule);

    const url = tenantId
      ? `${this.baseUrl}/rules/${tenantId}`
      : `${this.baseUrl}/rules`;

    const response = await this.axios.post(url, rule);
    return response.data;
  }

  /**
   * Update a rule
   * @param ruleId Rule ID
   * @param updates Updates to apply
   * @param tenantId Tenant ID
   */
  async updateRule(
    ruleId: string,
    updates: Partial<AutoTransformRule>,
    tenantId?: string
  ): Promise<AutoTransformRule> {
    const url = tenantId
      ? `${this.baseUrl}/rules/${tenantId}/${ruleId}`
      : `${this.baseUrl}/rules/${ruleId}`;

    const response = await this.axios.put<AutoTransformRule>(url, updates);
    return response.data;
  }

  /**
   * Delete a rule
   * @param ruleId Rule ID
   * @param tenantId Tenant ID
   */
  async deleteRule(ruleId: string, tenantId?: string): Promise<void> {
    const url = tenantId
      ? `${this.baseUrl}/rules/${tenantId}/${ruleId}`
      : `${this.baseUrl}/rules/${ruleId}`;

    await this.axios.delete(url);
  }

  /**
   * Enable a rule
   * @param ruleId Rule ID
   * @param tenantId Tenant ID
   */
  async enableRule(ruleId: string, tenantId?: string): Promise<void> {
    await this.updateRule(ruleId, { enabled: true }, tenantId);
  }

  /**
   * Disable a rule
   * @param ruleId Rule ID
   * @param tenantId Tenant ID
   */
  async disableRule(ruleId: string, tenantId?: string): Promise<void> {
    await this.updateRule(ruleId, { enabled: false }, tenantId);
  }

  /**
   * Get available templates
   */
  async getTemplates(): Promise<AutoTransformTemplate[]> {
    const response = await this.axios.get<AutoTransformTemplate[]>(
      `${this.baseUrl}/templates`
    );
    return response.data;
  }

  /**
   * Apply a template
   * @param templateId Template ID
   * @param tenantId Tenant ID
   */
  async applyTemplate(
    templateId: string,
    tenantId?: string
  ): Promise<{ success: boolean; rule_id: string }> {
    const url = tenantId
      ? `${this.baseUrl}/apply-template/${tenantId}/${templateId}`
      : `${this.baseUrl}/apply-template/${templateId}`;

    const response = await this.axios.post(url);
    return response.data;
  }

  /**
   * Create keyword-based rule
   * @param name Rule name
   * @param keywords Keywords to trigger on
   * @param transformationType Transformation to apply
   * @param tenantId Tenant ID
   */
  async createKeywordRule(
    name: string,
    keywords: string[],
    transformationType: string,
    tenantId?: string
  ): Promise<{ success: boolean; rule_id: string }> {
    return this.createRule(
      {
        rule_name: name,
        enabled: true,
        priority: 0,
        trigger_type: 'keyword',
        trigger_value: { keywords },
        transformation_type: transformationType as any,
        transformation_intensity: 2
      },
      tenantId
    );
  }

  /**
   * Create sentiment-based rule
   * @param name Rule name
   * @param threshold Sentiment threshold
   * @param operator Comparison operator
   * @param transformationType Transformation to apply
   * @param tenantId Tenant ID
   */
  async createSentimentRule(
    name: string,
    threshold: number,
    operator: 'less_than' | 'greater_than' | 'equals',
    transformationType: string,
    tenantId?: string
  ): Promise<{ success: boolean; rule_id: string }> {
    return this.createRule(
      {
        rule_name: name,
        enabled: true,
        priority: 0,
        trigger_type: 'sentiment',
        trigger_value: { threshold, operator },
        transformation_type: transformationType as any,
        transformation_intensity: 2
      },
      tenantId
    );
  }

  /**
   * Create time-based rule
   * @param name Rule name
   * @param after Start time (HH:MM)
   * @param before End time (HH:MM)
   * @param transformationType Transformation to apply
   * @param tenantId Tenant ID
   */
  async createTimeRule(
    name: string,
    after: string,
    before: string,
    transformationType: string,
    tenantId?: string
  ): Promise<{ success: boolean; rule_id: string }> {
    return this.createRule(
      {
        rule_name: name,
        enabled: true,
        priority: 0,
        trigger_type: 'time',
        trigger_value: { after, before },
        transformation_type: transformationType as any,
        transformation_intensity: 2
      },
      tenantId
    );
  }

  /**
   * Get rule statistics
   * @param tenantId Tenant ID
   * @param period Period in days
   */
  async getRuleStatistics(
    tenantId?: string,
    period: number = 30
  ): Promise<{
    total_evaluations: number;
    total_transformations: number;
    rule_usage: Record<string, number>;
    success_rate: number;
  }> {
    const url = tenantId
      ? `${this.baseUrl}/statistics/${tenantId}`
      : `${this.baseUrl}/statistics`;

    const response = await this.axios.get(url, {
      params: { period }
    });

    return response.data;
  }

  /**
   * Validate message context
   */
  private validateMessageContext(context: MessageContext): void {
    if (!context.message) {
      throw new ValidationError('Message is required');
    }
    if (!context.user_id) {
      throw new ValidationError('User ID is required');
    }
    if (!context.tenant_id) {
      throw new ValidationError('Tenant ID is required');
    }
    if (!context.platform) {
      throw new ValidationError('Platform is required');
    }
  }

  /**
   * Validate rule
   */
  private validateRule(rule: Omit<AutoTransformRule, 'id'>): void {
    if (!rule.rule_name) {
      throw new ValidationError('Rule name is required');
    }
    if (!rule.trigger_type) {
      throw new ValidationError('Trigger type is required');
    }
    if (!rule.trigger_value) {
      throw new ValidationError('Trigger value is required');
    }
    if (!rule.transformation_type) {
      throw new ValidationError('Transformation type is required');
    }
  }
}