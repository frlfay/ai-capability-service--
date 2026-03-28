"""
ImageGeneratorAgent - 图片生成
调用硅基流动 API 生成图片。
"""

import logging
import asyncio
from typing import Dict, Any
from openai import OpenAI

from ...deep_research_v2.agents.base import BaseAgent
from ..state import CreativeState, CreativePhase

logger = logging.getLogger("Agent.ImageGenerator")


class ImageGeneratorAgent(BaseAgent):
    """图片生成 Agent"""

    def __init__(self, siliconflow_api_key: str, llm_api_key: str, llm_base_url: str, model: str = "Kwai-Kolors/Kolors"):
        super().__init__(
            name="ImageGenerator",
            role="Image Generation Specialist",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model,
        )
        self.sf_client = OpenAI(
            api_key=siliconflow_api_key,
            base_url="https://api.siliconflow.cn/v1",
        )

    async def process(self, state: CreativeState) -> CreativeState:
        """生成图片"""
        self.add_message(state, "phase", {
            "phase": "generating_image",
            "content": "正在生成图片..."
        })

        model = state["selected_image_model"] or "Kwai-Kolors/Kolors"
        prompt = state["image_prompt"]
        negative_prompt = state["image_negative_prompt"]
        size = state["image_params"].get("size", "1024x1024")

        if not prompt:
            state["errors"].append("No image prompt available")
            return state

        self.add_message(state, "generation_start", {
            "model": model,
            "prompt": prompt[:100],
        })

        try:
            # SiliconFlow 的 OpenAI 兼容接口不支持 negative_prompt 参数
            # 将 negative prompt 合并到 prompt 中
            full_prompt = prompt
            if negative_prompt:
                full_prompt = f"{prompt} --no {negative_prompt}"

            kwargs = {
                "model": model,
                "prompt": full_prompt,
                "size": size,
                "n": 1,
            }

            response = await asyncio.to_thread(
                self.sf_client.images.generate,
                **kwargs
            )

            image_url = response.data[0].url
            image_data = {
                "url": image_url,
                "model": model,
                "prompt": prompt,
                "size": size,
            }
            state["generated_images"].append(image_data)
            state["phase"] = CreativePhase.GENERATING_IMAGE.value

            self.add_message(state, "image_generated", {
                "url": image_url,
                "model": model,
            })

            logger.info(f"Image generated: {image_url[:80]}...")

        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            self.add_message(state, "error", {"content": error_msg})

        return state
