"""
DeepResearch Agents - 基础组件
仅导出 BaseAgent 供 Creative Agent 复用。
"""

from .base import BaseAgent, AgentRegistry

__all__ = [
    'BaseAgent',
    'AgentRegistry',
]
