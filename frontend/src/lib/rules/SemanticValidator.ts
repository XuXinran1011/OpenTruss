/**
 * 语义校验器（前端）
 * 
 * 使用配置文件进行快速验证，避免频繁调用后端 API
 * 用于在 Canvas 中提供实时反馈
 */

interface SemanticMapping {
  mappings?: Record<string, string>;
  relationships?: Record<string, {
    examples?: Array<[string, string]>;
  }>;
}

/**
 * 语义校验器类
 * 
 * 使用配置文件进行快速验证，支持：
 * - 检查两种元素类型是否可以连接
 * - 获取允许的关系类型列表
 * - 提供错误信息和建议
 */
export class SemanticValidator {
  private mapping: SemanticMapping = {};

  constructor(mapping?: SemanticMapping) {
    this.mapping = mapping || this.getDefaultMapping();
  }

  /**
   * 获取默认映射配置
   * 
   * 这是一个简化的配置，实际应该从后端加载或使用配置文件
   */
  private getDefaultMapping(): SemanticMapping {
    return {
      relationships: {
        feeds: {
          examples: [
            // MEP 系统连接
            ['Pipe', 'Pipe'],
            ['Duct', 'Duct'],
            ['CableTray', 'CableTray'],
            ['Conduit', 'Conduit'],
            ['Wire', 'Wire'],
            // 设备连接
            ['Pipe', 'Duct'], // 某些情况下可以连接（如热交换器）
            // 禁止的连接（通过不在列表中表示）
          ],
        },
        feeds_from: {
          examples: [
            ['Pipe', 'Pipe'],
            ['Duct', 'Duct'],
            ['CableTray', 'CableTray'],
            ['Conduit', 'Conduit'],
            ['Wire', 'Wire'],
          ],
        },
        controls: {
          examples: [
            // 控制关系（如阀门控制管道）
            ['Pipe', 'Pipe'],
          ],
        },
      },
    };
  }

  /**
   * 检查两种元素类型是否可以连接
   * 
   * @param sourceType 源元素类型
   * @param targetType 目标元素类型
   * @param relationship 关系类型（默认为 'feeds'）
   * @returns 是否可以连接
   */
  canConnect(
    sourceType: string,
    targetType: string,
    relationship: string = 'feeds'
  ): boolean {
    const relationships = this.mapping.relationships || {};
    const relationshipConfig = relationships[relationship];

    if (!relationshipConfig) {
      // 如果关系类型不存在，默认不允许连接
      return false;
    }

    const examples = relationshipConfig.examples || [];
    
    // 检查是否有匹配的示例
    for (const example of examples) {
      if (example.length === 2 && example[0] === sourceType && example[1] === targetType) {
        return true;
      }
    }

    return false;
  }

  /**
   * 获取允许的关系类型列表
   * 
   * @param sourceType 源元素类型
   * @param targetType 目标元素类型
   * @returns 允许的关系类型列表
   */
  getAllowedRelationships(sourceType: string, targetType: string): string[] {
    const allowed: string[] = [];
    const relationships = this.mapping.relationships || {};

    for (const [relName, relConfig] of Object.entries(relationships)) {
      const examples = relConfig.examples || [];
      for (const example of examples) {
        if (example.length === 2 && example[0] === sourceType && example[1] === targetType) {
          allowed.push(relName);
        }
      }
    }

    return allowed;
  }

  /**
   * 验证连接（返回完整验证结果）
   * 
   * @param sourceType 源元素类型
   * @param targetType 目标元素类型
   * @param relationship 关系类型（默认为 'feeds'）
   * @returns 验证结果
   */
  validateConnection(
    sourceType: string,
    targetType: string,
    relationship: string = 'feeds'
  ): {
    valid: boolean;
    source_type: string;
    target_type: string;
    relationship: string;
    allowed_relationships: string[];
    error?: string;
    suggestion?: string;
  } {
    const canConnect = this.canConnect(sourceType, targetType, relationship);
    const allowedRelationships = this.getAllowedRelationships(sourceType, targetType);

    return {
      valid: canConnect,
      source_type: sourceType,
      target_type: targetType,
      relationship,
      allowed_relationships: allowedRelationships,
      error: canConnect ? undefined : `${sourceType} cannot ${relationship} ${targetType}`,
      suggestion: !canConnect && allowedRelationships.length > 0 ? allowedRelationships[0] : undefined,
    };
  }
}

