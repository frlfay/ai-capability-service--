"""
LLM 和 Agent 配置文件

集中管理所有 LLM 相关配置，包括：
- API 配置（密钥、基础 URL）
- Creative Agent 各节点的模型配置

使用方式:
    from app.config.llm_config import LLMConfig, get_config

    config = get_config()
    print(config.default_model)
    print(config.agents.dispatcher.model)
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class AgentModelConfig:
    """单个 Agent 的模型配置"""
    model: str
    temperature: float = 0.7
    max_tokens: int = 8000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


@dataclass
class AgentsConfig:
    """Creative Agent 各节点配置"""
    dispatcher: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.3,
        max_tokens=2000
    ))

    prompt_engineer: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.7,
        max_tokens=4000
    ))

    quality_checker: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.3,
        max_tokens=4000
    ))


@dataclass
class LLMConfig:
    """LLM 配置主类"""
    # API 配置
    api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ))

    # SiliconFlow API（图片/视频生成）
    siliconflow_api_key: str = field(default_factory=lambda: os.getenv("SILICONFLOW_API_KEY", ""))
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"

    # 默认模型
    default_model: str = "deepseek-v3.2"

    # Agent 配置
    agents: AgentsConfig = field(default_factory=AgentsConfig)

    def get_agent_config(self, agent_name: str) -> AgentModelConfig:
        """获取指定 Agent 的配置"""
        agent_configs = {
            "dispatcher": self.agents.dispatcher,
            "prompt_engineer": self.agents.prompt_engineer,
            "quality_checker": self.agents.quality_checker,
        }
        return agent_configs.get(agent_name, AgentModelConfig(model=self.default_model))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "api_key": self.api_key[:8] + "..." if self.api_key else "",
            "base_url": self.base_url,
            "siliconflow_api_key": self.siliconflow_api_key[:8] + "..." if self.siliconflow_api_key else "",
            "default_model": self.default_model,
            "agents": {
                "dispatcher": self.agents.dispatcher.to_dict(),
                "prompt_engineer": self.agents.prompt_engineer.to_dict(),
                "quality_checker": self.agents.quality_checker.to_dict(),
            },
        }


# 全局配置实例（单例模式）
_config_instance: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = LLMConfig()
    return _config_instance


def reload_config() -> LLMConfig:
    """重新加载配置"""
    global _config_instance
    _config_instance = LLMConfig()
    return _config_instance


def get_agent_model(agent_name: str) -> str:
    """快速获取指定 Agent 的模型名称"""
    return get_config().get_agent_config(agent_name).model


def get_default_model() -> str:
    """快速获取默认模型"""
    return get_config().default_model
