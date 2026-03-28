"""
PromptEngineerAgent - 提示词优化
类似 Lovart 的 MCoT 引擎简化版，基于设计技能模板优化生成提示词。
"""

import json
import logging
from typing import Dict, Any

from ...deep_research_v2.agents.base import BaseAgent
from ..state import CreativeState, CreativePhase

logger = logging.getLogger("Agent.PromptEngineer")

SYSTEM_PROMPT = """你是一个专业的 AI 图像/视频生成提示词工程师。你的职责是将用户的创意需求转化为高质量的生成提示词。

## 提示词优化规则

**图片提示词结构**:
[主体描述], [风格], [光照], [构图], [质量标签]

**视频提示词结构**:
[场景描述], [运动方式], [镜头语言], [氛围], [质量标签]

**注意事项**:
- 提示词必须用英文
- 主体描述要具体、明确
- 风格标签要与场景匹配
- 质量标签放在最后
- 负面提示词要排除常见瑕疵

请返回 JSON 格式。"""

USER_PROMPT_TEMPLATE = """## 用户需求
{query}

## 解析后的意图
- 任务类型: {task_type}
- 应用场景: {scene} ({scene_name})
- 视觉风格: {style}
- 主体: {subject}
- 品牌色: {brand_colors}

## 设计技能参考
- 推荐质量标签: {quality_tags}
- 推荐风格后缀: {prompt_suffix}
- 推荐负面提示词: {negative_prompt}

请基于以上信息，生成优化后的提示词:
{{
    "image_prompt": "英文图片提示词",
    "image_negative_prompt": "英文负面提示词",
    "video_prompt": "英文视频提示词（如果需要视频）",
    "selected_image_model": "推荐的图片模型ID",
    "selected_video_model": "推荐的视频模型ID",
    "image_size": "1024x1024"
}}

可选的图片模型:
- Kwai-Kolors/Kolors: 快手可图，擅长多风格图片生成，中文理解好
- Qwen/Qwen-Image: 通义万相，擅长创意图片和文字融合

可选的视频模型:
- Wan-AI/Wan2.2-T2V-A14B: 文生视频，适合从文字描述直接生成视频
- Wan-AI/Wan2.2-I2V-A14B: 图生视频，适合将生成的图片动画化"""


class PromptEngineerAgent(BaseAgent):
    """提示词优化 Agent"""

    def __init__(self, llm_api_key: str, llm_base_url: str, model: str = "deepseek-v3.2"):
        super().__init__(
            name="PromptEngineer",
            role="Prompt Optimization Specialist",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model,
        )

    async def process(self, state: CreativeState) -> CreativeState:
        """优化提示词"""
        self.add_message(state, "phase", {
            "phase": "prompt_engineering",
            "content": "正在优化生成提示词..."
        })

        intent = state["intent"]
        skill = state["design_skill"]

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT_TEMPLATE.format(
                query=state["query"],
                task_type=intent.get("task_type", "image"),
                scene=intent.get("scene", ""),
                scene_name=skill.get("name", ""),
                style=intent.get("style", ""),
                subject=intent.get("subject", ""),
                brand_colors=intent.get("brand_constraints", {}).get("colors", []),
                quality_tags=skill.get("quality_tags", ""),
                prompt_suffix=skill.get("prompt_suffix", ""),
                negative_prompt=skill.get("negative_prompt", ""),
            ),
            json_mode=True,
            temperature=0.7,
        )

        result = self.parse_json_response(response)

        state["image_prompt"] = result.get("image_prompt", "")
        state["image_negative_prompt"] = result.get("image_negative_prompt", "")
        state["video_prompt"] = result.get("video_prompt", "")
        state["selected_image_model"] = result.get("selected_image_model", skill.get("recommended_model", "Kwai-Kolors/Kolors"))
        state["selected_video_model"] = result.get("selected_video_model", "Wan-AI/Wan2.2-T2V-A14B")
        state["image_params"] = {"size": result.get("image_size", "1024x1024")}
        state["phase"] = CreativePhase.PROMPT_ENGINEERING.value

        self.add_message(state, "prompt_optimized", {
            "image_prompt": state["image_prompt"],
            "image_negative_prompt": state["image_negative_prompt"],
            "video_prompt": state["video_prompt"],
            "image_model": state["selected_image_model"],
            "video_model": state["selected_video_model"],
        })

        logger.info(f"Prompts optimized. Image model: {state['selected_image_model']}")
        return state
