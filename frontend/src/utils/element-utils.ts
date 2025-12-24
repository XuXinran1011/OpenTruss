/** 构件工具函数 */

import { ElementDetail, getElementDetail } from '@/services/elements';

/**
 * 批量获取构件详情
 */
export async function batchGetElementDetails(elementIds: string[]): Promise<Map<string, ElementDetail>> {
  const detailsMap = new Map<string, ElementDetail>();
  
  // 并行获取所有构件详情
  const promises = elementIds.map(async (id) => {
    try {
      const detail = await getElementDetail(id);
      return { id, detail };
    } catch (error) {
      console.error(`Failed to fetch element ${id}:`, error);
      return null;
    }
  });
  
  const results = await Promise.all(promises);
  results.forEach((result) => {
    if (result) {
      detailsMap.set(result.id, result.detail);
    }
  });
  
  return detailsMap;
}

