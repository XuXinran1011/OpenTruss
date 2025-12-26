/**
 * 构造校验器（规则引擎 Phase 2）
 * 
 * 实现角度吸附和Z轴完整性检查
 */

export interface ConstructabilityConfig {
  angles: {
    standard: number[];
    tolerance: number;
    allow_custom: boolean;
  };
  z_axis: {
    require_height: boolean;
    require_base_offset: boolean;
    element_types: string[];
  };
}

export class ConstructabilityValidator {
  private config: ConstructabilityConfig;

  constructor(config?: ConstructabilityConfig) {
    // 默认配置
    this.config = config || {
      angles: {
        standard: [45, 90, 180],
        tolerance: 5,
        allow_custom: false,
      },
      z_axis: {
        require_height: true,
        require_base_offset: true,
        element_types: ['Wall', 'Column'],
      },
    };
  }

  /**
   * 角度吸附到最近的标准角度
   * 
   * @param angle 角度值（度）
   * @returns 吸附后的角度，如果无法吸附则返回 null
   */
  snapAngle(angle: number): number | null {
    const standardAngles = this.config.angles.standard;
    const tolerance = this.config.angles.tolerance;

    // 标准化角度到 [0, 180] 范围
    let normalizedAngle = angle % 360;
    if (normalizedAngle > 180) {
      normalizedAngle = 360 - normalizedAngle;
    }

    // 查找最接近的标准角度
    let minDiff = Infinity;
    let closestAngle: number | null = null;

    for (const stdAngle of standardAngles) {
      const diff = Math.abs(normalizedAngle - stdAngle);
      if (diff < minDiff) {
        minDiff = diff;
        closestAngle = stdAngle;
      }
    }

    // 如果最接近的角度在容差范围内，返回该角度
    if (closestAngle !== null && minDiff <= tolerance) {
      return closestAngle;
    }

    return null;
  }

  /**
   * 计算路径角度
   * 
   * @param path 路径点列表 [[x1, y1], [x2, y2], ...]
   * @returns 角度（度）
   */
  calculatePathAngle(path: number[][]): number {
    if (path.length < 2) {
      return 0.0;
    }

    const start = path[0];
    const end = path[path.length - 1];

    const dx = end[0] - start[0];
    const dy = end[1] - start[1];

    // 计算角度（0-360度）
    let angle = Math.atan2(dy, dx) * (180 / Math.PI);
    if (angle < 0) {
      angle += 360;
    }

    // 转换为 0-180 度范围（因为 180° 和 360° 等价）
    if (angle > 180) {
      angle -= 180;
    }

    return angle;
  }

  /**
   * 计算路径中的转弯角度（用于多段路径）
   * 
   * @param path 路径点列表
   * @param pointIndex 转弯点索引（路径中的中间点，1 到 path.length-2）
   * @returns 转弯角度（度）
   */
  calculateTurnAngle(path: number[][], pointIndex: number): number {
    if (path.length < 3 || pointIndex < 1 || pointIndex >= path.length - 1) {
      return 0.0;
    }

    const p1 = path[pointIndex - 1];
    const p2 = path[pointIndex];
    const p3 = path[pointIndex + 1];

    // 向量1：从p1到p2
    const v1 = { x: p2[0] - p1[0], y: p2[1] - p1[1] };
    // 向量2：从p2到p3
    const v2 = { x: p3[0] - p2[0], y: p3[1] - p2[1] };

    // 计算角度
    const angle1 = Math.atan2(v1.y, v1.x);
    const angle2 = Math.atan2(v2.y, v2.x);

    // 计算角度差（转为度）
    let angleDiff = Math.abs((angle2 - angle1) * (180 / Math.PI));

    // 标准化到 [0, 360)
    if (angleDiff < 0) {
      angleDiff += 360;
    }

    // 转换为内角（0-180度）
    if (angleDiff > 180) {
      angleDiff = 360 - angleDiff;
    }

    return angleDiff;
  }

  /**
   * 验证角度是否符合标准
   * 
   * @param angle 角度值（度）
   * @returns 验证结果
   */
  validateAngle(angle: number): {
    valid: boolean;
    snappedAngle: number | null;
    error?: string;
  } {
    const standardAngles = this.config.angles.standard;
    const tolerance = this.config.angles.tolerance;
    const allowCustom = this.config.angles.allow_custom;

    // 标准化角度到 [0, 180] 范围
    let normalizedAngle = angle % 360;
    if (normalizedAngle > 180) {
      normalizedAngle = 360 - normalizedAngle;
    }

    // 查找最接近的标准角度
    const snappedAngle = this.snapAngle(angle);

    if (snappedAngle === null) {
      // 无法吸附到标准角度
      if (allowCustom) {
        // 允许自定义角度
        return {
          valid: true,
          snappedAngle: normalizedAngle,
        };
      } else {
        return {
          valid: false,
          snappedAngle: null,
          error: `角度 ${angle.toFixed(1)}° 不在标准角度列表中 ${standardAngles.join(', ')}°，且不允许自定义角度`,
        };
      }
    } else {
      // 成功吸附到标准角度
      const diff = Math.abs(normalizedAngle - snappedAngle);
      if (diff <= tolerance) {
        return {
          valid: true,
          snappedAngle,
        };
      } else {
        return {
          valid: false,
          snappedAngle,
          error: `角度 ${angle.toFixed(1)}° 与标准角度 ${snappedAngle}° 的差距 ${diff.toFixed(1)}° 超过容差 ${tolerance}°`,
        };
      }
    }
  }
}

