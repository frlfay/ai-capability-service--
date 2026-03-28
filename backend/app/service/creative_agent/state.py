"""
Creative Agent - 状态管理模块
所有 Agent 共享此状态。
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from enum import Enum


class CreativePhase(str, Enum):
    """创作阶段状态机"""
    INIT = "init"
    DISPATCHING = "dispatching"
    PROMPT_ENGINEERING = "prompt_engineering"
    GENERATING_IMAGE = "generating_image"
    GENERATING_VIDEO = "generating_video"
    QUALITY_CHECKING = "quality_checking"
    COMPLETED = "completed"


class CreativeState(TypedDict):
    """全局创作状态"""
    # 基础信息
    query: str
    session_id: str
    phase: str
    iteration: int
    max_iterations: int

    # Dispatcher 输出
    intent: Dict[str, Any]

    # PromptEngineer 输出
    image_prompt: str
    image_negative_prompt: str
    video_prompt: str
    selected_image_model: str
    selected_video_model: str
    image_params: Dict[str, Any]

    # ImageGenerator 输出
    generated_images: List[Dict[str, Any]]

    # VideoGenerator 输出
    generated_videos: List[Dict[str, Any]]
    video_task_id: str

    # QualityChecker 输出
    quality_scores: List[Dict[str, Any]]
    overall_quality: float

    # 设计技能配置
    design_skill: Dict[str, Any]

    # 最终输出
    final_output: Dict[str, Any]

    # 元数据
    logs: List[Dict[str, Any]]
    errors: List[str]
    messages: List[Dict[str, Any]]


# 设计技能模板库
DESIGN_SKILLS = {
    "social_media_poster": {
        "name": "社交媒体海报",
        "prompt_suffix": "social media style, eye-catching, vibrant colors, professional layout",
        "negative_prompt": "blurry, low quality, watermark, text error, distorted",
        "recommended_model": "Kwai-Kolors/Kolors",
        "aspect_ratio": "1:1",
        "quality_tags": "masterpiece, best quality, 8k, highly detailed",
    },
    "brand_logo": {
        "name": "品牌Logo",
        "prompt_suffix": "minimalist logo design, vector style, clean background, professional",
        "negative_prompt": "complex background, photorealistic, blurry, low quality",
        "recommended_model": "Qwen/Qwen-Image",
        "aspect_ratio": "1:1",
        "quality_tags": "logo, minimal, clean, sharp",
    },
    "product_photo": {
        "name": "产品摄影",
        "prompt_suffix": "professional product photography, studio lighting, clean background, commercial quality",
        "negative_prompt": "amateur, noisy, distorted, low resolution, watermark",
        "recommended_model": "Kwai-Kolors/Kolors",
        "aspect_ratio": "4:3",
        "quality_tags": "commercial photography, sharp focus, studio quality",
    },
    "video_ad": {
        "name": "视频广告",
        "prompt_suffix": "cinematic, professional lighting, smooth camera movement, high production value",
        "negative_prompt": "shaky, low quality, amateur, distorted",
        "recommended_model": "Wan-AI/Wan2.2-T2V-A14B",
        "aspect_ratio": "16:9",
        "quality_tags": "cinematic, 4k, professional",
    },
}


def create_initial_state(query: str, session_id: str) -> CreativeState:
    """创建初始状态"""
    return CreativeState(
        query=query,
        session_id=session_id,
        phase=CreativePhase.INIT.value,
        iteration=0,
        max_iterations=2,
        intent={},
        image_prompt="",
        image_negative_prompt="",
        video_prompt="",
        selected_image_model="",
        selected_video_model="",
        image_params={},
        generated_images=[],
        generated_videos=[],
        video_task_id="",
        quality_scores=[],
        overall_quality=0.0,
        design_skill={},
        final_output={},
        logs=[],
        errors=[],
        messages=[],
    )
