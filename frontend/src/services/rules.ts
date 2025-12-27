/**
 * 规则管理服务
 */

export interface RuleInfo {
  rule_type: string;
  name: string;
  description: string;
}

export interface RulePreviewRequest {
  rule_type: 'BY_LEVEL' | 'BY_ZONE' | 'BY_LEVEL_AND_ZONE';
  item_id: string;
}

export interface RulePreviewGroup {
  key: string;
  count: number;
  label: string;
}

export interface RulePreviewResponse {
  rule_type: string;
  estimated_lots: number;
  groups: RulePreviewGroup[];
}

/**
 * 获取规则列表
 */
export async function getRules(): Promise<RuleInfo[]> {
  const response = await fetch('/api/v1/rules', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get rules');
  }

  const result = await response.json();
  return result.data.rules;
}

/**
 * 预览规则
 */
export async function previewRule(request: RulePreviewRequest): Promise<RulePreviewResponse> {
  const response = await fetch('/api/v1/rules/preview', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to preview rule');
  }

  const result = await response.json();
  return result.data;
}

