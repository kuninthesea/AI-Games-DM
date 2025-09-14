# -*- coding: utf-8 -*-
"""
游戏模型包

包含以下模块：
- event: 事件系统
- skill: 技能系统  
- creature: 生物系统
"""

from .event import event_manager
from .skill import skill_manager
from .creature import creature_manager

__all__ = ['event_manager', 'skill_manager', 'creature_manager']
