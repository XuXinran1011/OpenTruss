# k6性能测试运行脚本 (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$K6Dir = Join-Path $ProjectRoot "backend\tests\performance\k6"

Set-Location $K6Dir

# 检查k6是否安装
if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "错误: k6 未安装" -ForegroundColor Red
    Write-Host "请访问 https://k6.io/docs/getting-started/installation/ 安装k6"
    exit 1
}

# API基础URL（可通过环境变量覆盖）
$ApiBaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://localhost:8000" }

Write-Host "=== k6性能测试 ===" -ForegroundColor Cyan
Write-Host "API地址: $ApiBaseUrl"
Write-Host ""

# 运行认证API测试
Write-Host "1. 运行认证API测试..." -ForegroundColor Yellow
$env:API_BASE_URL = $ApiBaseUrl
k6 run auth.js

Write-Host ""
Write-Host "2. 运行构件API测试..." -ForegroundColor Yellow
k6 run elements.js

Write-Host ""
Write-Host "3. 运行场景化测试..." -ForegroundColor Yellow
k6 run scenarios.js

Write-Host ""
Write-Host "=== 测试完成 ===" -ForegroundColor Green

