# Locust性能测试运行脚本 (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$LocustDir = Join-Path $ProjectRoot "backend\tests\performance\locust"

Set-Location $LocustDir

# 检查locust是否安装
try {
    $null = Get-Command locust -ErrorAction Stop
} catch {
    Write-Host "错误: locust 未安装" -ForegroundColor Red
    Write-Host "请运行: pip install locust>=2.0.0"
    exit 1
}

# API基础URL（可通过环境变量覆盖）
$ApiBaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://localhost:8000" }

# 测试参数（可通过环境变量覆盖）
$Users = if ($env:USERS) { $env:USERS } else { "50" }
$SpawnRate = if ($env:SPAWN_RATE) { $env:SPAWN_RATE } else { "5" }
$RunTime = if ($env:RUN_TIME) { $env:RUN_TIME } else { "5m" }
$Mode = if ($env:MODE) { $env:MODE } else { "headless" }

Write-Host "=== Locust性能测试 ===" -ForegroundColor Cyan
Write-Host "API地址: $ApiBaseUrl"
Write-Host "并发用户数: $Users"
Write-Host "生成速率: $SpawnRate 用户/秒"
Write-Host "运行时间: $RunTime"
Write-Host ""

$ReportsDir = Join-Path $ProjectRoot "backend\tests\performance\reports"
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
}

if ($Mode -eq "ui") {
    Write-Host "启动Locust Web UI..." -ForegroundColor Yellow
    Write-Host "访问 http://localhost:8089 开始测试" -ForegroundColor Green
    locust -f comprehensive_load_test.py --host "$ApiBaseUrl"
} else {
    Write-Host "运行综合性能测试（headless模式）..." -ForegroundColor Yellow
    $ReportPath = Join-Path $ReportsDir "locust_report.html"
    $CsvPath = Join-Path $ReportsDir "locust"
    
    locust -f comprehensive_load_test.py `
        --host "$ApiBaseUrl" `
        --users $Users `
        --spawn-rate $SpawnRate `
        --run-time $RunTime `
        --headless `
        --html $ReportPath `
        --csv $CsvPath
    
    Write-Host ""
    Write-Host "测试报告已保存到: backend\tests\performance\reports\" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 测试完成 ===" -ForegroundColor Green

