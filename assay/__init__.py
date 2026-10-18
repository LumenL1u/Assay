"""Assay: 通用 Agent 任务评测工具。

核心思路：任务定义（task.toml）与提示词模板分离，渲染出每个任务的
契约（CONTRACT.md）、执行 Agent 指令与评估 Agent 指令。
"""

__version__ = "0.1.0"

from .render import RenderResult, render_task
from .task import Task, TaskError, find_task_dirs, load_task, validate_task

__all__ = [
    "Task",
    "TaskError",
    "find_task_dirs",
    "load_task",
    "validate_task",
    "RenderResult",
    "render_task",
]
