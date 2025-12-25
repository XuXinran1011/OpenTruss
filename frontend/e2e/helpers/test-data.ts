/**
 * E2E测试 - 测试数据生成函数
 */

/**
 * 生成测试项目数据
 */
export function generateTestProject(projectId?: string) {
  const id = projectId || `test_project_${Date.now()}`;
  return {
    id,
    name: `测试项目 ${id}`,
    description: 'E2E测试用项目',
  };
}

/**
 * 生成测试构件数据
 */
export function generateTestElement(elementId?: string, speckleType: string = 'Wall') {
  const id = elementId || `test_element_${Date.now()}`;
  return {
    speckle_id: `speckle_${id}`,
    speckle_type: speckleType,
    geometry_2d: {
      type: 'Polyline',
      coordinates: [
        [0, 0],
        [10, 0],
        [10, 5],
        [0, 5],
        [0, 0],
      ],
      closed: true,
    },
    height: 3.0,
    level_id: 'test_level_1',
    units: 'meters',
  };
}

/**
 * 生成测试检验批数据
 */
export function generateTestLot(lotId?: string) {
  const id = lotId || `test_lot_${Date.now()}`;
  return {
    id,
    name: `测试检验批 ${id}`,
    item_id: 'unassigned_item',
    spatial_scope: 'Test Scope',
    status: 'PLANNING',
  };
}

/**
 * 生成测试分项数据
 */
export function generateTestItem(itemId?: string) {
  const id = itemId || `test_item_${Date.now()}`;
  return {
    id,
    name: `测试分项 ${id}`,
    subdivision_id: 'unassigned_subdivision',
  };
}

/**
 * 生成批量测试构件数据
 */
export function generateBatchTestElements(count: number, speckleType: string = 'Wall') {
  return Array.from({ length: count }, (_, i) => 
    generateTestElement(`test_element_${Date.now()}_${i}`, speckleType)
  );
}

/**
 * 生成测试层级结构数据
 */
export function generateTestHierarchy() {
  const projectId = `test_project_${Date.now()}`;
  const buildingId = `test_building_${Date.now()}`;
  const divisionId = `test_division_${Date.now()}`;
  const subdivisionId = `test_subdivision_${Date.now()}`;
  const itemId = `test_item_${Date.now()}`;
  
  return {
    project: {
      id: projectId,
      name: '测试项目',
    },
    building: {
      id: buildingId,
      name: '测试单体',
      project_id: projectId,
    },
    division: {
      id: divisionId,
      name: '测试分部',
      building_id: buildingId,
    },
    subdivision: {
      id: subdivisionId,
      name: '测试子分部',
      division_id: divisionId,
    },
    item: {
      id: itemId,
      name: '测试分项',
      subdivision_id: subdivisionId,
    },
  };
}

