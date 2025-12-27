"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import ingest, hierarchy, elements, lots, approval, export, auth, metrics, background, routing, validation, rules, spatial, hangers
from app.core.config import settings
from app.services.schema import initialize_schema
from app.utils.memgraph import MemgraphClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理
    
    在启动时初始化 Schema，在关闭时清理资源
    """
    # 启动时执行
    logger.info("Initializing OpenTruss API...")
    try:
        # 初始化 Memgraph Schema（包括默认用户）
        client = MemgraphClient()
        initialize_schema(client, create_default_users=True)
        logger.info("Schema initialization completed")
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}")
        # 继续启动，但记录错误
        # 在实际生产环境中，可能需要阻止启动
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down OpenTruss API...")


app = FastAPI(
    title="OpenTruss API",
    description="面向建筑施工行业的生成式 BIM 中间件 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(hierarchy.router, prefix="/api/v1")
app.include_router(elements.router, prefix="/api/v1")
app.include_router(lots.router, prefix="/api/v1")
app.include_router(approval.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(background.router, prefix="/api/v1")
app.include_router(routing.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(rules.router, prefix="/api/v1")
app.include_router(metrics.router)  # Metrics endpoint at /metrics (no prefix)
app.include_router(spatial.router, prefix="/api/v1")
app.include_router(hangers.router, prefix="/api/v1")


@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "OpenTruss API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}

