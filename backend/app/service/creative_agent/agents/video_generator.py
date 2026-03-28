"""
VideoGeneratorAgent - 视频生成
调用硅基流动 Wan2.2 模型，支持文生视频(T2V)和图生视频(I2V)。
视频生成是异步的：提交任务 -> 轮询状态 -> 获取URL。
"""

import logging
import asyncio
import json
import requests
from typing import Dict, Any

from ...deep_research_v2.agents.base import BaseAgent
from ..state import CreativeState, CreativePhase

logger = logging.getLogger("Agent.VideoGenerator")


class VideoGeneratorAgent(BaseAgent):
    """视频生成 Agent"""

    def __init__(self, siliconflow_api_key: str, llm_api_key: str, llm_base_url: str, model: str = "Wan-AI/Wan2.2-T2V-A14B"):
        super().__init__(
            name="VideoGenerator",
            role="Video Generation Specialist",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model,
        )
        self.sf_api_key = siliconflow_api_key
        self.sf_base_url = "https://api.siliconflow.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {siliconflow_api_key}",
            "Content-Type": "application/json",
        }

    async def process(self, state: CreativeState) -> CreativeState:
        """生成视频"""
        task_type = state["intent"].get("task_type", "image")
        if task_type not in ("video", "image_and_video"):
            logger.info("No video generation needed, skipping")
            return state

        self.add_message(state, "phase", {
            "phase": "generating_video",
            "content": "正在生成视频（这可能需要1-2分钟）..."
        })

        # 决定用 T2V 还是 I2V
        has_image = len(state["generated_images"]) > 0
        use_i2v = has_image and task_type == "image_and_video"

        if use_i2v:
            model = "Wan-AI/Wan2.2-I2V-A14B"
            image_url = state["generated_images"][-1]["url"]
            payload = {
                "model": model,
                "prompt": state["video_prompt"] or state["image_prompt"],
                "image": image_url,
            }
            self.add_message(state, "video_mode", {
                "mode": "I2V (图生视频)",
                "source_image": image_url[:80],
            })
        else:
            model = state["selected_video_model"] or "Wan-AI/Wan2.2-T2V-A14B"
            payload = {
                "model": model,
                "prompt": state["video_prompt"] or state["image_prompt"],
            }
            self.add_message(state, "video_mode", {
                "mode": "T2V (文生视频)",
            })

        try:
            # 步骤1: 提交视频生成任务
            submit_resp = await asyncio.to_thread(
                requests.post,
                f"{self.sf_base_url}/video/submit",
                headers=self.headers,
                json=payload,
            )
            submit_data = submit_resp.json()
            request_id = submit_data.get("requestId", "")

            if not request_id:
                raise Exception(f"Video submit failed: {submit_resp.text}")

            state["video_task_id"] = request_id
            self.add_message(state, "video_submitted", {
                "request_id": request_id,
                "model": model,
            })
            logger.info(f"Video task submitted: {request_id}")

            # 步骤2: 轮询等待结果
            max_polls = 60
            for i in range(max_polls):
                await asyncio.sleep(5)

                status_resp = await asyncio.to_thread(
                    requests.post,
                    f"{self.sf_base_url}/video/status",
                    headers=self.headers,
                    json={"requestId": request_id},
                )

                raw = status_resp.text
                if "RPM limit" in raw:
                    continue

                status_data = json.loads(raw)
                status = status_data.get("status", "")

                if i % 6 == 0:
                    self.add_message(state, "video_progress", {
                        "status": status,
                        "elapsed_seconds": (i + 1) * 5,
                    })

                if status == "Succeed":
                    videos = status_data.get("results", {}).get("videos", [])
                    if videos:
                        video_url = videos[0].get("url", "")
                        video_data = {
                            "url": video_url,
                            "model": model,
                            "prompt": payload.get("prompt", ""),
                            "request_id": request_id,
                        }
                        state["generated_videos"].append(video_data)
                        self.add_message(state, "video_generated", {
                            "url": video_url,
                            "model": model,
                        })
                        logger.info(f"Video generated: {video_url[:80]}...")
                    break

                elif "Fail" in status or "Error" in status:
                    reason = status_data.get("reason", "Unknown error")
                    raise Exception(f"Video generation failed: {reason}")

            else:
                raise Exception("Video generation timed out after 5 minutes")

        except Exception as e:
            error_msg = f"Video generation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            self.add_message(state, "error", {"content": error_msg})

        state["phase"] = CreativePhase.GENERATING_VIDEO.value
        return state
