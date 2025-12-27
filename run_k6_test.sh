#!/bin/bash
# 临时脚本用于运行 k6 测试

WIN_IP=$(cat /etc/resolv.conf | awk '/nameserver/ {print $2}')
export API_BASE_URL="http://${WIN_IP}:8000"

cd /mnt/d/MyPrograms/OpenTruss\(beta\)/backend/tests/performance/k6

echo "Running k6 test: $1"
echo "API_BASE_URL: $API_BASE_URL"

k6 run --vus 5 --duration 30s "$1"
