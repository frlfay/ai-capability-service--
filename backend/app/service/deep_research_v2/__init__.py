"""
DeepResearch V2.0 - 基础组件
Creative Agent 复用 BaseAgent 基类和 State 定义。
"""

from .state import ResearchState, ResearchPhase
from .agents.base import BaseAgent

__all__ = [
    'ResearchState',
    'ResearchPhase',
    'BaseAgent',
]
