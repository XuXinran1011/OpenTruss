#!/bin/bash
# 临时脚本用于运行压力测试

WIN_IP=$(cat /etc/resolv.conf | awk '/nameserver/ {print $2}')
export API_BASE_URL="http://${WIN_IP}:8000"

cd /mnt/d/MyPrograms/OpenTruss\(beta\)/backend/tests/performance/stress

echo "Running stress test: $1"
echo "API_BASE_URL: $API_BASE_URL"

if [ "$1" = "k6" ]; then
    k6 run --env API_BASE_URL="$API_BASE_URL" k6_stress_test.js
elif [ "$1" = "locust" ]; then
    if command -v locust &> /dev/null; then
        LOCUST_CMD=locust
    else
        LOCUST_CMD=~/.local/bin/locust
    fi
    $LOCUST_CMD -f locust_stress_test.py --host "$API_BASE_URL" --headless --users 50 --spawn-rate 5 --run-time 2m
fi
