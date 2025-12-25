"""
性能指标收集器

收集系统指标（CPU、内存、数据库连接等）并与测试结果关联
"""

import psutil
import time
import logging
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, interval: float = 1.0):
        """
        初始化收集器
        
        Args:
            interval: 收集间隔（秒）
        """
        self.interval = interval
        self.metrics: List[SystemMetrics] = []
        self.is_collecting = False
        self.start_time = None
        self._disk_io_prev = None
        self._network_io_prev = None
    
    def start(self):
        """开始收集指标"""
        self.is_collecting = True
        self.start_time = time.time()
        self.metrics = []
        self._disk_io_prev = psutil.disk_io_counters()
        self._network_io_prev = psutil.net_io_counters()
        logger.info("开始收集系统指标...")
    
    def stop(self):
        """停止收集指标"""
        self.is_collecting = False
        logger.info(f"停止收集系统指标，共收集 {len(self.metrics)} 条记录")
    
    def collect_once(self) -> SystemMetrics:
        """收集一次指标"""
        timestamp = time.time()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = 0
        disk_io_write_mb = 0
        if self._disk_io_prev and disk_io:
            disk_io_read_mb = (disk_io.read_bytes - self._disk_io_prev.read_bytes) / (1024 * 1024)
            disk_io_write_mb = (disk_io.write_bytes - self._disk_io_prev.write_bytes) / (1024 * 1024)
            self._disk_io_prev = disk_io
        
        # 网络IO
        network_io = psutil.net_io_counters()
        network_sent_mb = 0
        network_recv_mb = 0
        if self._network_io_prev and network_io:
            network_sent_mb = (network_io.bytes_sent - self._network_io_prev.bytes_sent) / (1024 * 1024)
            network_recv_mb = (network_io.bytes_recv - self._network_io_prev.bytes_recv) / (1024 * 1024)
            self._network_io_prev = network_io
        
        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def collect_continuously(self):
        """持续收集指标（应在单独线程中运行）"""
        while self.is_collecting:
            self.collect_once()
            time.sleep(self.interval)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics]
        memory_values = [m.memory_percent for m in self.metrics]
        
        return {
            "duration_seconds": self.metrics[-1].timestamp - self.metrics[0].timestamp if len(self.metrics) > 1 else 0,
            "sample_count": len(self.metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
            },
            "memory": {
                "avg_percent": sum(memory_values) / len(memory_values),
                "min_percent": min(memory_values),
                "max_percent": max(memory_values),
                "peak_used_mb": max(m.memory_used_mb for m in self.metrics),
            },
        }
    
    def export_to_dict(self) -> List[Dict[str, Any]]:
        """导出为字典列表"""
        return [asdict(m) for m in self.metrics]


# 使用示例
if __name__ == "__main__":
    import logging
    import threading
    
    logging.basicConfig(level=logging.INFO)
    
    collector = MetricsCollector(interval=1.0)
    
    # 开始收集
    collector.start()
    
    # 在后台线程中持续收集
    collect_thread = threading.Thread(target=collector.collect_continuously, daemon=True)
    collect_thread.start()
    
    # 模拟测试运行
    print("模拟测试运行10秒...")
    time.sleep(10)
    
    # 停止收集
    collector.stop()
    time.sleep(1)  # 等待线程结束
    
    # 获取摘要
    summary = collector.get_summary()
    print("\n指标摘要:")
    print(f"  持续时间: {summary['duration_seconds']:.2f}秒")
    print(f"  样本数: {summary['sample_count']}")
    print(f"  CPU使用率: 平均={summary['cpu']['avg']:.2f}%, 最小={summary['cpu']['min']:.2f}%, 最大={summary['cpu']['max']:.2f}%")
    print(f"  内存使用率: 平均={summary['memory']['avg_percent']:.2f}%, 峰值={summary['memory']['peak_used_mb']:.2f}MB")

