"""
Creative Agent - 服务入口
提供 SSE 流式输出接口。
"""

import json
import uuid
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from .graph import CreativeGraph

logger = logging.getLogger("CreativeService")


class CreativeService:
    """Creative Agent 服务"""

    def __init__(self):
        self.graph = CreativeGraph()
        logger.info("CreativeService initialized")

    async def generate(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """执行创意生成（SSE 流式输出）"""
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"Starting creative generation: {query[:50]}...")

        try:
            async for event in self.graph.run(query, session_id):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Creative generation error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"
