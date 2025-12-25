"""
性能测试报告生成器

生成HTML格式的性能测试报告，包括图表和统计信息
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class PerformanceReportGenerator:
    """性能测试报告生成器"""
    
    def __init__(self, output_dir: str = "test-results/performance"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(
        self,
        test_name: str,
        metrics: Dict[str, Any],
        output_filename: str = None
    ) -> str:
        """生成HTML格式的性能测试报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"performance_report_{test_name}_{timestamp}.html"
        filepath = self.output_dir / filename
        
        html_content = self._generate_html_content(test_name, metrics)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _generate_html_content(self, test_name: str, metrics: Dict[str, Any]) -> str:
        """生成HTML内容"""
        
        # 提取关键指标
        response_times = metrics.get('response_times', {})
        throughput = metrics.get('throughput', {})
        error_rate = metrics.get('error_rate', 0)
        total_requests = metrics.get('total_requests', 0)
        total_failures = metrics.get('total_failures', 0)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能测试报告 - {test_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            font-weight: 600;
        }}
        .metric-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .chart-container {{
            margin: 30px 0;
            height: 400px;
            position: relative;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>性能测试报告</h1>
        <div class="timestamp">测试名称: {test_name}</div>
        <div class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="summary">
            <div class="metric-card">
                <h3>总请求数</h3>
                <div class="value">{total_requests:,}</div>
            </div>
            <div class="metric-card">
                <h3>失败请求数</h3>
                <div class="value">{total_failures:,}</div>
            </div>
            <div class="metric-card">
                <h3>错误率</h3>
                <div class="value">{error_rate:.2f}%</div>
            </div>
            <div class="metric-card">
                <h3>平均响应时间</h3>
                <div class="value">{response_times.get('avg', 0):.0f}ms</div>
            </div>
            <div class="metric-card">
                <h3>P95 响应时间</h3>
                <div class="value">{response_times.get('p95', 0):.0f}ms</div>
            </div>
            <div class="metric-card">
                <h3>P99 响应时间</h3>
                <div class="value">{response_times.get('p99', 0):.0f}ms</div>
            </div>
        </div>
        
        <h2>响应时间分布</h2>
        <div class="chart-container">
            <canvas id="responseTimeChart"></canvas>
        </div>
        
        <h2>吞吐量（RPS）</h2>
        <div class="chart-container">
            <canvas id="throughputChart"></canvas>
        </div>
        
        <h2>详细指标</h2>
        <table>
            <thead>
                <tr>
                    <th>指标</th>
                    <th>值</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>最小响应时间</td>
                    <td>{response_times.get('min', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>最大响应时间</td>
                    <td>{response_times.get('max', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>平均响应时间</td>
                    <td>{response_times.get('avg', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>中位数响应时间</td>
                    <td>{response_times.get('median', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>P95 响应时间</td>
                    <td>{response_times.get('p95', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>P99 响应时间</td>
                    <td>{response_times.get('p99', 0):.2f}ms</td>
                </tr>
                <tr>
                    <td>平均吞吐量</td>
                    <td>{throughput.get('avg', 0):.2f} RPS</td>
                </tr>
                <tr>
                    <td>峰值吞吐量</td>
                    <td>{throughput.get('peak', 0):.2f} RPS</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <script>
        // 响应时间分布图表（示例数据，实际应从metrics中获取）
        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        new Chart(responseTimeCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(metrics.get('time_points', []))},
                datasets: [{{
                    label: '平均响应时间 (ms)',
                    data: {json.dumps(metrics.get('response_time_data', []))},
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // 吞吐量图表
        const throughputCtx = document.getElementById('throughputChart').getContext('2d');
        new Chart(throughputCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(metrics.get('time_points', []))},
                datasets: [{{
                    label: '吞吐量 (RPS)',
                    data: {json.dumps(metrics.get('throughput_data', []))},
                    backgroundColor: 'rgba(54, 162, 235, 0.5)'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html
    
    def save_json_report(self, test_name: str, metrics: Dict[str, Any]) -> str:
        """保存JSON格式的测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_report_{test_name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        report_data = {
            "test_name": test_name,
            "timestamp": timestamp,
            "metrics": metrics,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)


# 使用示例
if __name__ == "__main__":
    generator = PerformanceReportGenerator()
    
    # 示例指标数据
    sample_metrics = {
        "total_requests": 10000,
        "total_failures": 50,
        "error_rate": 0.5,
        "response_times": {
            "min": 50,
            "max": 2000,
            "avg": 250,
            "median": 200,
            "p95": 500,
            "p99": 1000,
        },
        "throughput": {
            "avg": 100,
            "peak": 150,
        },
        "time_points": list(range(0, 60, 5)),
        "response_time_data": [200 + i * 5 for i in range(12)],
        "throughput_data": [90 + i * 2 for i in range(12)],
    }
    
    # 生成HTML报告
    html_file = generator.generate_html_report("sample_test", sample_metrics)
    print(f"HTML报告已生成: {html_file}")
    
    # 保存JSON报告
    json_file = generator.save_json_report("sample_test", sample_metrics)
    print(f"JSON报告已保存: {json_file}")

