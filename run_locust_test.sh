#!/bin/bash
# 临时脚本用于运行 locust 测试

WIN_IP=$(cat /etc/resolv.conf | awk '/nameserver/ {print $2}')
export API_BASE_URL="http://${WIN_IP}:8000"

cd /mnt/d/MyPrograms/OpenTruss\(beta\)/backend/tests/performance/locust

mkdir -p ../reports

echo "Running locust test: $1"
echo "API_BASE_URL: $API_BASE_URL"

if command -v locust &> /dev/null; then
    LOCUST_CMD=locust
else
    LOCUST_CMD=~/.local/bin/locust
fi

$LOCUST_CMD -f "$1" --host "$API_BASE_URL" --headless --users 10 --spawn-rate 2 --run-time 30s --html ../reports/locust_report.html --csv ../reports/locust
