"""
QualityCheckerAgent - 质量检查
使用 LLM 评估生成结果的质量。
基于提示词和生成参数进行逻辑质检。
"""

import logging
from typing import Dict, Any

from ...deep_research_v2.agents.base import BaseAgent
from ..state import CreativeState, CreativePhase

logger = logging.getLogger("Agent.QualityChecker")

SYSTEM_PROMPT = """你是一个专业的视觉设计质量审核员。你需要根据生成任务的上下文（用户需求、提示词、模型选择）来评估生成结果的潜在质量。

评估维度（每项 1-10 分）:
1. prompt_quality: 提示词是否清晰、具体、无歧义
2. model_match: 模型选择是否匹配任务需求
3. style_consistency: 风格是否与用户需求一致
4. completeness: 是否覆盖了用户要求的所有元素
5. commercial_viability: 结果是否达到商业使用标准

请返回 JSON 格式。如果平均分 >= 7，判定为通过。"""

USER_PROMPT_TEMPLATE = """## 用户原始需求
{query}

## 解析意图
- 任务类型: {task_type}
- 场景: {scene}
- 风格: {style}
- 主体: {subject}

## 使用的提示词
- 图片提示词: {image_prompt}
- 负面提示词: {negative_prompt}

## 模型选择
- 图片模型: {image_model}
- 视频模型: {video_model}

## 生成结果
- 图片数量: {image_count}
- 视频数量: {video_count}
- 是否有错误: {has_errors}
- 错误信息: {errors}

请评估并返回:
{{
    "scores": {{
        "prompt_quality": 1-10,
        "model_match": 1-10,
        "style_consistency": 1-10,
        "completeness": 1-10,
        "commercial_viability": 1-10
    }},
    "average": float,
    "pass": true/false,
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}}"""


class QualityCheckerAgent(BaseAgent):
    """质量检查 Agent"""

    def __init__(self, llm_api_key: str, llm_base_url: str, model: str = "deepseek-v3.2"):
        super().__init__(
            name="QualityChecker",
            role="Quality Assurance Specialist",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model,
        )

    async def process(self, state: CreativeState) -> CreativeState:
        """质量检查"""
        self.add_message(state, "phase", {
            "phase": "quality_checking",
            "content": "正在进行质量检查..."
        })

        intent = state["intent"]

        response = await self.call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT_TEMPLATE.format(
                query=state["query"],
                task_type=intent.get("task_type", ""),
                scene=intent.get("scene", ""),
                style=intent.get("style", ""),
                subject=intent.get("subject", ""),
                image_prompt=state["image_prompt"],
                negative_prompt=state["image_negative_prompt"],
                image_model=state["selected_image_model"],
                video_model=state["selected_video_model"],
                image_count=len(state["generated_images"]),
                video_count=len(state["generated_videos"]),
                has_errors=len(state["errors"]) > 0,
                errors="; ".join(state["errors"]) if state["errors"] else "无",
            ),
            json_mode=True,
            temperature=0.3,
        )

        result = self.parse_json_response(response)

        quality_score = {
            "scores": result.get("scores", {}),
            "average": result.get("average", 0),
            "pass": result.get("pass", False),
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
        }

        state["quality_scores"].append(quality_score)
        state["overall_quality"] = quality_score["average"]
        state["phase"] = CreativePhase.QUALITY_CHECKING.value

        self.add_message(state, "quality_result", {
            "score": quality_score["average"],
            "pass": quality_score["pass"],
            "issues": quality_score["issues"],
            "suggestions": quality_score["suggestions"],
        })

        if not quality_score["pass"] and state["iteration"] < state["max_iterations"]:
            self.add_message(state, "retry", {
                "iteration": state["iteration"],
                "reason": quality_score["issues"],
            })
            logger.info(f"Quality check failed (score={quality_score['average']}), retry #{state['iteration']}")
        else:
            state["final_output"] = {
                "images": state["generated_images"],
                "videos": state["generated_videos"],
                "quality_score": quality_score["average"],
                "summary": f"生成了 {len(state['generated_images'])} 张图片"
                           + (f"和 {len(state['generated_videos'])} 个视频" if state["generated_videos"] else "")
                           + f"，质量评分: {quality_score['average']:.1f}/10",
            }
            state["phase"] = CreativePhase.COMPLETED.value
            logger.info(f"Quality check passed (score={quality_score['average']})")

        return state
