"""
创意生成 API 路由
"""

from typing import Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from service.creative_agent.service import CreativeService

logger = logging.getLogger("CreativeRouter")

router = APIRouter(prefix="/creative", tags=["creative"])


class CreativeRequest(BaseModel):
    """创意生成请求"""
    query: str
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "帮我设计一个咖啡品牌的社交媒体海报，风格要温暖文艺，然后生成一段产品宣传视频",
            }
        }


_service = None

def get_service():
    global _service
    if _service is None:
        _service = CreativeService()
    return _service


@router.post("/generate")
async def generate_creative(request: CreativeRequest):
    """
    创意生成接口 - SSE 流式输出

    支持图片生成、视频生成、图片+视频组合生成。
    通过多 Agent 协作完成：意图解析 -> 提示词优化 -> 图片生成 -> 质量检查 -> 视频生成。
    """
    service = get_service()

    return StreamingResponse(
        service.generate(
            query=request.query,
            session_id=request.session_id,
        ),
        media_type="text/event-stream",
    )
