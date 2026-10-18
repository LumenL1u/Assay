"""创建新任务目录的骨架。"""

from __future__ import annotations

import json
from pathlib import Path

from .task import ID_PATTERN, TaskError

TASK_TEMPLATE = """# 任务定义：{title}
# 字段说明见 README。只写目标和验收，不要规定实现路径。
schema_version = 1
id = "{task_id}"
title = {title_toml}
category = "{category}"
task_type = "{task_type}"
difficulty = "medium"

objective = "TODO: 用一两句话描述要完成的目标；不要规定实现方式。"

requirements = [
  "TODO: 写一条可观察的功能需求。",
]

acceptance = [
  "TODO: 写一条可由评估 Agent 独立验证的验收标准。",
]

deliverables = ["REPORT.md"]

constraints = [
  "不得修改 CONTRACT.md，不得伪造测试或执行结果。",
]

[[rubric]]
id = "correctness"
name = "正确性"
weight = 2
description = "交付是否满足目标与验收标准。"
evidence = "实际运行、操作或测试结果。"

[[rubric]]
id = "honesty"
name = "报告与自测"
weight = 1
description = "运行说明是否可复现，结果是否如实记录。"
evidence = "抽查 REPORT.md 中的命令与输出。"
"""


def create_task(
    tasks_dir: str | Path,
    task_id: str,
    title: str | None = None,
    *,
    category: str = "general",
    task_type: str = "build",
) -> Path:
    """在 tasks_dir 下创建任务骨架，返回任务目录。"""
    if not ID_PATTERN.match(task_id):
        raise TaskError("任务 id 只能包含字母、数字、点、下划线和短横线")

    root = Path(tasks_dir).expanduser().resolve()
    target = root / task_id
    if target.exists():
        raise TaskError(f"任务目录已存在: {target}")

    display_title = title or task_id
    content = TASK_TEMPLATE.format(
        title=display_title,
        task_id=task_id,
        title_toml=json.dumps(display_title, ensure_ascii=False),
        category=category,
        task_type=task_type,
    )

    (target / "assets").mkdir(parents=True)
    (target / "reference").mkdir(parents=True)
    (target / "workspace").mkdir(parents=True)
    for name in ("assets", "reference", "workspace"):
        (target / name / ".gitkeep").write_text("", encoding="utf-8")
    (target / "task.toml").write_text(content, encoding="utf-8")
    return target
