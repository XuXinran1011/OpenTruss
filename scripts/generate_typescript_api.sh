#!/bin/bash
# 生成 TypeScript API 客户端脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始生成 TypeScript API 客户端...${NC}"

# 检查 OpenAPI schema 文件是否存在
SCHEMA_FILE="temp/openapi.json"
if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${YELLOW}警告: OpenAPI schema 文件不存在，尝试从 FastAPI 服务获取...${NC}"
    
    # 尝试从 FastAPI 服务获取
    if command -v curl &> /dev/null; then
        curl -o "$SCHEMA_FILE" http://localhost:8000/openapi.json
    elif command -v wget &> /dev/null; then
        wget -O "$SCHEMA_FILE" http://localhost:8000/openapi.json
    else
        echo -e "${RED}错误: 无法下载 OpenAPI schema，请手动运行 verify_openapi_schema.py${NC}"
        exit 1
    fi
fi

# 进入前端目录
cd frontend || exit 1

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装 npm 依赖...${NC}"
    npm install
fi

# 生成 TypeScript 代码
echo -e "${GREEN}生成 TypeScript API 客户端...${NC}"
npm run generate-api

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ TypeScript API 客户端生成成功！${NC}"
    echo -e "${GREEN}输出目录: frontend/src/lib/api${NC}"
else
    echo -e "${RED}✗ TypeScript API 客户端生成失败${NC}"
    exit 1
fi

