"""
FastAPI 主应用 - 商业级标准
支持 CORS、异常处理、日志
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn

from core.config import get_settings
from core.fallback import create_safe_fallback_result
from api.routes import router

# 创建应用
app = FastAPI(
    title="AI症状结构化与风险分层系统",
    description="商业级医疗初筛MVP - 对标ADA Health",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(router, prefix="/api", tags=["analysis"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """参数校验异常处理"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数格式错误",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理 - 确保永不返回500给前端"""
    print(f"全局异常: {exc}")
    
    # 返回安全的降级响应
    fallback = create_safe_fallback_result(
        "",
        reason="服务器内部错误，已启用安全降级"
    )
    
    return JSONResponse(
        status_code=200,  # 注意：仍返回200
        content=fallback.dict()
    )


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI症状结构化与风险分层系统 API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )


# 完成
