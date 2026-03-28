"""
Creative Agent - LangGraph 工作流
Dispatch -> PromptEngineer -> ImageGenerator -> QualityChecker -> (VideoGenerator) -> Complete
"""

import logging
import asyncio
from typing import Dict, Any, AsyncGenerator, Literal
from datetime import datetime

from .state import CreativeState, CreativePhase, create_initial_state
from .agents import (
    DispatcherAgent,
    PromptEngineerAgent,
    ImageGeneratorAgent,
    VideoGeneratorAgent,
    QualityCheckerAgent,
)

try:
    from config.llm_config import get_config
except ImportError:
    from app.config.llm_config import get_config

logger = logging.getLogger("CreativeGraph")


class CreativeGraph:
    """
    Creative Agent 工作流图

    DAG: Dispatch -> PromptEngineer -> ImageGen -> QualityCheck
                                                      |
                                             pass? -> VideoGen -> END
                                             fail? -> PromptEngineer (重试)
    """

    def __init__(self):
        config = get_config()

        self.dispatcher = DispatcherAgent(
            config.api_key, config.base_url,
            config.agents.dispatcher.model,
        )
        self.prompt_engineer = PromptEngineerAgent(
            config.api_key, config.base_url,
            config.agents.prompt_engineer.model,
        )
        self.image_generator = ImageGeneratorAgent(
            siliconflow_api_key=config.siliconflow_api_key,
            llm_api_key=config.api_key,
            llm_base_url=config.base_url,
        )
        self.video_generator = VideoGeneratorAgent(
            siliconflow_api_key=config.siliconflow_api_key,
            llm_api_key=config.api_key,
            llm_base_url=config.base_url,
        )
        self.quality_checker = QualityCheckerAgent(
            config.api_key, config.base_url,
            config.agents.quality_checker.model,
        )

        logger.info("CreativeGraph initialized")

    async def run(self, query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """执行创作流程（流式输出）"""
        state = create_initial_state(query, session_id)
        message_queue = asyncio.Queue()
        state["_message_queue"] = message_queue

        async def run_agent_with_streaming(agent):
            """执行 agent 并实时 yield 消息，失败时抛出异常"""
            task = asyncio.create_task(agent.process(state))
            while not task.done():
                try:
                    msg = await asyncio.wait_for(message_queue.get(), timeout=0.5)
                    yield msg
                except asyncio.TimeoutError:
                    continue
            # 清空剩余消息
            while not message_queue.empty():
                try:
                    yield message_queue.get_nowait()
                except:
                    break
            # 获取结果，如果 agent 抛出异常则向上传播
            await task

        try:
            # 发送开始事件
            yield {
                "type": "creative_start",
                "query": query,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Phase 1: Dispatch (意图解析)
            async for msg in run_agent_with_streaming(self.dispatcher):
                yield msg
            state["messages"] = []

            # Phase 2+3+4: 生成与质检循环
            while state["iteration"] <= state["max_iterations"]:
                # Phase 2: PromptEngineer (提示词优化)
                async for msg in run_agent_with_streaming(self.prompt_engineer):
                    yield msg
                state["messages"] = []

                # Phase 3: ImageGenerator (图片生成)
                async for msg in run_agent_with_streaming(self.image_generator):
                    yield msg
                state["messages"] = []

                # Phase 4: QualityChecker (质量检查)
                async for msg in run_agent_with_streaming(self.quality_checker):
                    yield msg
                state["messages"] = []

                # 质检通过则退出循环
                if state["phase"] == CreativePhase.COMPLETED.value:
                    break

                # 质检不通过，清空之前的图片重新生成
                state["iteration"] += 1
                logger.info(f"Regenerating... iteration={state['iteration']}")
                state["generated_images"] = []

            # Phase 5: VideoGenerator (视频生成，如果需要)
            task_type = state["intent"].get("task_type", "image")
            if task_type in ("video", "image_and_video"):
                async for msg in run_agent_with_streaming(self.video_generator):
                    yield msg
                state["messages"] = []

                # 更新最终输出
                if state["generated_videos"]:
                    state["final_output"]["videos"] = state["generated_videos"]
                    state["final_output"]["summary"] += f"和 {len(state['generated_videos'])} 个视频"

            # 完成
            state["phase"] = CreativePhase.COMPLETED.value
            yield {
                "type": "creative_complete",
                "final_output": state["final_output"],
                "quality_score": state["overall_quality"],
                "images": state["generated_images"],
                "videos": state["generated_videos"],
                "iterations": state["iteration"],
            }

        except Exception as e:
            logger.error(f"Creative workflow error: {e}")
            yield {"type": "error", "content": str(e)}
        finally:
            state["_message_queue"] = None
