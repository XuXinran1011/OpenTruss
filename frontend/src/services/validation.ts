/**
 * 校验服务
 * 
 * 提供各种校验功能的 API 调用
 */

import { API_CONFIG } from '@/config/api';
import { apiPost } from './api';

export interface SemanticValidationRequest {
  source_type: string;
  target_type: string;
  relationship?: string;
}

export interface SemanticValidationResponse {
  valid: boolean;
  source_type: string;
  target_type: string;
  relationship: string;
  allowed_relationships: string[];
  error?: string;
  suggestion?: string;
}

/**
 * 验证语义连接
 * 
 * 验证两种元素类型是否可以连接（规则引擎 Phase 1：语义防呆）
 */
export async function validateSemanticConnection(
  request: SemanticValidationRequest
): Promise<SemanticValidationResponse> {
  const response = await apiPost<{ status: string; data: SemanticValidationResponse }>(
    `${API_CONFIG.baseURL}/validation/semantic/validate-connection`,
    {
      source_type: request.source_type,
      target_type: request.target_type,
      relationship: request.relationship || 'feeds',
    }
  );

  if (response.status !== 'success') {
    throw new Error('语义连接验证失败');
  }

  return response.data;
}

