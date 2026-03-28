"""
DispatcherAgent - 意图解析与任务分发
类似 Lovart 的 Coco Agent，负责理解用户意图并制定创作计划。
"""

import json
import logging
from typing import Dict, Any

from ...deep_research_v2.agents.base import BaseAgent
from ..state import CreativeState, CreativePhase, DESIGN_SKILLS

logger = logging.getLogger("Agent.Dispatcher")

SYSTEM_PROMPT = """你是一个专业的创意设计调度员。你的职责是分析用户的创意需求，提取关键信息，并制定创作计划。

你需要从用户的描述中识别：
1. task_type: 任务类型
   - "image": 只需要生成图片
   - "video": 只需要生成视频
   - "image_and_video": 先生成图片，再基于图片生成视频
2. scene: 应用场景（social_media_poster / brand_logo / product_photo / video_ad）
3. style: 视觉风格（minimalist / vibrant / cinematic / warm / cool / retro / futuristic）
4. subject: 主体描述（核心内容是什么）
5. brand_constraints: 品牌约束（如果有的话）
   - colors: 品牌色列表
   - tone: 品牌调性

请始终返回 JSON 格式。"""

USER_PROMPT_TEMPLATE = """用户需求: {query}

请分析以上需求，返回如下 JSON:
{{
    "task_type": "image" | "video" | "image_and_video",
    "scene": "social_media_poster" | "brand_logo" | "product_photo" | "video_ad",
    "style": "风格关键词",
    "subject": "主体描述",
    "brand_constraints": {{
        "colors": [],
        "tone": ""
    }}
}}"""


class DispatcherAgent(BaseAgent):
    """意图解析 Agent"""

    def __init__(self, llm_api_key: str, llm_base_url: str, model: str = "deepseek-v3.2"):
        super().__init__(
            name="Dispatcher",
            role="Creative Intent Analyzer",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model,
        )

    async def process(self, state: CreativeState) -> CreativeState:
        """解析用户意图"""
        self.add_message(state, "phase", {
            "phase": "dispatching",
            "content": "正在分析您的创意需求..."
        })

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT_TEMPLATE.format(query=state["query"]),
            json_mode=True,
            temperature=0.3,
        )

        intent = self.parse_json_response(response)

        # 根据 scene 匹配设计技能
        scene = intent.get("scene", "social_media_poster")
        skill = DESIGN_SKILLS.get(scene, DESIGN_SKILLS["social_media_poster"])

        state["intent"] = intent
        state["design_skill"] = skill
        state["phase"] = CreativePhase.DISPATCHING.value

        self.add_message(state, "intent_parsed", {
            "task_type": intent.get("task_type", "image"),
            "scene": scene,
            "scene_name": skill["name"],
            "style": intent.get("style", ""),
            "subject": intent.get("subject", ""),
        })

        logger.info(f"Intent parsed: type={intent.get('task_type')}, scene={scene}")
        return state
