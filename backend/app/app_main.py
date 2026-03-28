"""
AI Creative Agent Platform
基于多 Agent 协作的图片/视频创意生成平台
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from router.creative_router import router as creative_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Creative Agent Platform 启动中...")
    yield
    logger.info("Creative Agent Platform 关闭")


app = FastAPI(
    title="AI Creative Agent Platform",
    description="基于多 Agent 协作的图片/视频创意生成平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(creative_router)


@app.get("/hello")
async def hello_world():
    return {
        "status": "success",
        "message": "Creative Agent Platform is running."
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
