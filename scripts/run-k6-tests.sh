#!/bin/bash
# k6性能测试运行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K6_DIR="$PROJECT_ROOT/backend/tests/performance/k6"

cd "$K6_DIR"

# 检查k6是否安装
if ! command -v k6 &> /dev/null; then
    echo "错误: k6 未安装"
    echo "请访问 https://k6.io/docs/getting-started/installation/ 安装k6"
    exit 1
fi

# API基础URL（可通过环境变量覆盖）
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

echo "=== k6性能测试 ==="
echo "API地址: $API_BASE_URL"
echo ""

# 运行认证API测试
echo "1. 运行认证API测试..."
k6 run --env API_BASE_URL="$API_BASE_URL" auth.js

echo ""
echo "2. 运行构件API测试..."
k6 run --env API_BASE_URL="$API_BASE_URL" elements.js

echo ""
echo "3. 运行场景化测试..."
k6 run --env API_BASE_URL="$API_BASE_URL" scenarios.js

echo ""
echo "=== 测试完成 ==="

