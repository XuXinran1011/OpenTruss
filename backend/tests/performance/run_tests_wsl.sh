#!/bin/bash
# WSL2 性能测试运行脚本

# 获取 Windows 主机 IP
WIN_HOST_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
API_BASE_URL="http://${WIN_HOST_IP}:8000"

echo "Windows Host IP: $WIN_HOST_IP"
echo "API Base URL: $API_BASE_URL"

# 切换到脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# k6 测试
echo ""
echo "=== 运行 k6 性能测试 ==="
cd k6
export API_BASE_URL="$API_BASE_URL"
k6 run auth.js
k6 run elements.js
k6 run scenarios.js
cd ..

# locust 测试
echo ""
echo "=== 运行 locust 性能测试 ==="
cd locust
mkdir -p ../reports
locust -f comprehensive_load_test.py \
    --host "$API_BASE_URL" \
    --headless \
    --users 10 \
    --spawn-rate 2 \
    --run-time 30s \
    --html ../reports/locust_report.html \
    --csv ../reports/locust
cd ..

# 压力测试
echo ""
echo "=== 运行 k6 压力测试 ==="
cd stress
export API_BASE_URL="$API_BASE_URL"
k6 run k6_stress_test.js
cd ..

echo ""
echo "=== 运行 locust 压力测试 ==="
cd stress
locust -f locust_stress_test.py \
    --host "$API_BASE_URL" \
    --headless \
    --users 50 \
    --spawn-rate 5 \
    --run-time 2m
cd ..

echo ""
echo "=== 所有测试完成 ==="
