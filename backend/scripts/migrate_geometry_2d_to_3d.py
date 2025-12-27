"""
数据迁移脚本：将 geometry_2d 字段迁移到 geometry（3D 原生）

功能：
- 连接 Memgraph
- 执行 Cypher 迁移查询，将 geometry_2d 转换为 geometry（3D 格式）
- 处理现有数据：2D 坐标自动补 z=0.0
- 验证迁移结果
- 支持回滚（备份）

使用方法:
    python -m scripts.migrate_geometry_2d_to_3d

注意：
- 这是一个一次性迁移脚本，执行前请备份数据库
- 迁移后，geometry_2d 字段将被删除
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Dict, Any, List

from app.utils.memgraph import MemgraphClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


class GeometryMigration:
    """几何数据迁移器"""
    
    def __init__(self, client: MemgraphClient):
        self.client = client
    
    def backup_existing_data(self) -> int:
        """备份现有的 geometry_2d 数据
        
        Returns:
            int: 备份的元素数量
        """
        logger.info("开始备份现有的 geometry_2d 数据...")
        
        backup_query = """
        MATCH (n:Element)
        WHERE n.geometry_2d IS NOT NULL AND n.geometry_2d_backup IS NULL
        SET n.geometry_2d_backup = n.geometry_2d
        RETURN count(n) as backup_count
        """
        
        result = self.client.execute_query(backup_query)
        backup_count = result[0]["backup_count"] if result else 0
        
        logger.info(f"✔ 备份完成，共备份 {backup_count} 个元素")
        return backup_count
    
    def migrate_to_3d(self) -> int:
        """执行迁移：geometry_2d -> geometry（3D）
        
        Returns:
            int: 迁移的元素数量
        """
        logger.info("开始执行迁移：geometry_2d -> geometry（3D）...")
        
        # 迁移查询
        # 对于每个坐标点：
        # - 如果长度为 2（2D）：添加 z=0.0
        # - 如果长度为 3（3D）：直接使用
        # - 其他情况：设置为 [x, y, 0.0]
        migration_query = """
        MATCH (n:Element)
        WHERE n.geometry_2d IS NOT NULL
        WITH n, n.geometry_2d AS geo
        SET n.geometry = {
          type: geo.type,
          coordinates: [coord IN geo.coordinates | 
            CASE 
              WHEN size(coord) = 2 THEN coord + [0.0]
              WHEN size(coord) = 3 THEN coord
              ELSE [coord[0], coord[1], 0.0]
            END],
          closed: COALESCE(geo.closed, false)
        },
        n.updated_at = datetime()
        RETURN count(n) as migrated_count
        """
        
        result = self.client.execute_query(migration_query)
        migrated_count = result[0]["migrated_count"] if result else 0
        
        logger.info(f"✔ 迁移完成，共迁移 {migrated_count} 个元素")
        return migrated_count
    
    def remove_old_field(self) -> int:
        """删除旧的 geometry_2d 字段
        
        Returns:
            int: 删除字段的元素数量
        """
        logger.info("开始删除旧的 geometry_2d 字段...")
        
        remove_query = """
        MATCH (n:Element)
        WHERE n.geometry_2d IS NOT NULL
        REMOVE n.geometry_2d
        RETURN count(n) as removed_count
        """
        
        result = self.client.execute_query(remove_query)
        removed_count = result[0]["removed_count"] if result else 0
        
        logger.info(f"✔ 删除完成，共删除 {removed_count} 个元素的 geometry_2d 字段")
        return removed_count
    
    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果
        
        Returns:
            Dict: 验证结果统计
        """
        logger.info("开始验证迁移结果...")
        
        # 检查还有多少元素有 geometry_2d 字段
        check_old_query = """
        MATCH (n:Element)
        WHERE n.geometry_2d IS NOT NULL
        RETURN count(n) as old_count
        """
        
        # 检查有多少元素有 geometry 字段
        check_new_query = """
        MATCH (n:Element)
        WHERE n.geometry IS NOT NULL
        RETURN count(n) as new_count
        """
        
        # 检查坐标格式（确保都是 3D）
        check_coords_query = """
        MATCH (n:Element)
        WHERE n.geometry IS NOT NULL
        WITH n, n.geometry.coordinates AS coords
        UNWIND coords AS coord
        WITH n, coord, size(coord) AS coord_size
        WHERE coord_size != 3
        RETURN count(DISTINCT n) as invalid_count
        """
        
        old_result = self.client.execute_query(check_old_query)
        new_result = self.client.execute_query(check_new_query)
        invalid_result = self.client.execute_query(check_coords_query)
        
        old_count = old_result[0]["old_count"] if old_result else 0
        new_count = new_result[0]["new_count"] if new_result else 0
        invalid_count = invalid_result[0]["invalid_count"] if invalid_result else 0
        
        stats = {
            "elements_with_geometry_2d": old_count,
            "elements_with_geometry": new_count,
            "elements_with_invalid_coords": invalid_count
        }
        
        logger.info("=" * 60)
        logger.info("迁移验证结果：")
        logger.info(f"  仍包含 geometry_2d 的元素数: {old_count}")
        logger.info(f"  包含 geometry 的元素数: {new_count}")
        logger.info(f"  坐标格式无效的元素数: {invalid_count}")
        logger.info("=" * 60)
        
        return stats
    
    def run(self, backup: bool = True, remove_old: bool = True) -> Dict[str, Any]:
        """执行完整的迁移流程
        
        Args:
            backup: 是否备份现有数据
            remove_old: 是否删除旧的 geometry_2d 字段
        
        Returns:
            Dict: 迁移统计信息
        """
        logger.info("\n" + "=" * 60)
        logger.info("开始执行几何数据迁移：geometry_2d -> geometry（3D）")
        logger.info("=" * 60)
        
        stats = {}
        
        # 1. 备份（可选）
        if backup:
            stats["backup_count"] = self.backup_existing_data()
        else:
            logger.info("⚠ 跳过备份步骤")
        
        # 2. 执行迁移
        stats["migrated_count"] = self.migrate_to_3d()
        
        # 3. 删除旧字段（可选）
        if remove_old:
            stats["removed_count"] = self.remove_old_field()
        else:
            logger.info("⚠ 跳过删除旧字段步骤")
        
        # 4. 验证
        verification_stats = self.verify_migration()
        stats.update(verification_stats)
        
        logger.info("\n" + "=" * 60)
        logger.info("迁移流程完成！")
        logger.info("=" * 60)
        
        return stats


if __name__ == "__main__":
    client = MemgraphClient()
    try:
        migrator = GeometryMigration(client)
        stats = migrator.run(backup=True, remove_old=True)
        
        # 如果有验证问题，显示警告
        if stats.get("elements_with_geometry_2d", 0) > 0:
            logger.warning(f"⚠ 仍有 {stats['elements_with_geometry_2d']} 个元素包含 geometry_2d 字段")
        
        if stats.get("elements_with_invalid_coords", 0) > 0:
            logger.error(f"❌ 有 {stats['elements_with_invalid_coords']} 个元素的坐标格式无效（不是 3D）")
            sys.exit(1)
        
        logger.info("✅ 迁移成功完成！")
    except Exception as e:
        logger.error(f"❌ 迁移过程中发生错误: {e}", exc_info=True)
        sys.exit(1)
    finally:
        client.close()

