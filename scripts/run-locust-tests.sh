#!/bin/bash
# Locust性能测试运行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCUST_DIR="$PROJECT_ROOT/backend/tests/performance/locust"

cd "$LOCUST_DIR"

# 检查locust是否安装
if ! command -v locust &> /dev/null; then
    echo "错误: locust 未安装"
    echo "请运行: pip install locust>=2.0.0"
    exit 1
fi

# API基础URL（可通过环境变量覆盖）
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

# 测试参数（可通过环境变量覆盖）
USERS="${USERS:-50}"
SPAWN_RATE="${SPAWN_RATE:-5}"
RUN_TIME="${RUN_TIME:-5m}"
MODE="${MODE:-headless}"

echo "=== Locust性能测试 ==="
echo "API地址: $API_BASE_URL"
echo "并发用户数: $USERS"
echo "生成速率: $SPAWN_RATE 用户/秒"
echo "运行时间: $RUN_TIME"
echo ""

if [ "$MODE" = "ui" ]; then
    echo "启动Locust Web UI..."
    echo "访问 http://localhost:8089 开始测试"
    locust -f comprehensive_load_test.py --host "$API_BASE_URL"
else
    echo "运行综合性能测试（headless模式）..."
    locust -f comprehensive_load_test.py \
        --host "$API_BASE_URL" \
        --users "$USERS" \
        --spawn-rate "$SPAWN_RATE" \
        --run-time "$RUN_TIME" \
        --headless \
        --html "$PROJECT_ROOT/backend/tests/performance/reports/locust_report.html" \
        --csv "$PROJECT_ROOT/backend/tests/performance/reports/locust"
    
    echo ""
    echo "测试报告已保存到: backend/tests/performance/reports/"
fi

echo ""
echo "=== 测试完成 ==="

