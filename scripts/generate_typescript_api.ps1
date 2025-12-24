# PowerShell 脚本：生成 TypeScript API 客户端

$ErrorActionPreference = "Stop"

Write-Host "开始生成 TypeScript API 客户端..." -ForegroundColor Green

# 检查 OpenAPI schema 文件是否存在
$schemaFile = "temp\openapi.json"
if (-not (Test-Path $schemaFile)) {
    Write-Host "警告: OpenAPI schema 文件不存在，尝试从 FastAPI 服务获取..." -ForegroundColor Yellow
    
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -OutFile $schemaFile
        Write-Host "✓ 已下载 OpenAPI schema" -ForegroundColor Green
    } catch {
        Write-Host "错误: 无法下载 OpenAPI schema，请确保 FastAPI 服务正在运行" -ForegroundColor Red
        Write-Host "或者手动运行: python scripts\verify_openapi_schema.py" -ForegroundColor Yellow
        exit 1
    }
}

# 进入前端目录
Push-Location frontend

try {
    # 检查是否安装了依赖
    if (-not (Test-Path "node_modules")) {
        Write-Host "安装 npm 依赖..." -ForegroundColor Yellow
        npm install
    }
    
    # 生成 TypeScript 代码
    Write-Host "生成 TypeScript API 客户端..." -ForegroundColor Green
    npm run generate-api
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ TypeScript API 客户端生成成功！" -ForegroundColor Green
        Write-Host "输出目录: frontend\src\lib\api" -ForegroundColor Green
    } else {
        Write-Host "✗ TypeScript API 客户端生成失败" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

