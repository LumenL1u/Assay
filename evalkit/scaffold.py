"""创建新任务目录的骨架。"""

from __future__ import annotations

import json
from pathlib import Path

from .task import ID_PATTERN, TaskError

TASK_TEMPLATE = """# 任务定义：{title}
# 字段说明见 docs/task-schema.md
schema_version = 1
id = "{task_id}"
title = {title_toml}
category = "{category}"
task_type = "{task_type}"
difficulty = "medium"
version = "0.1.0"

[objective]
summary = "TODO: 用一两句话描述要完成的目标。"
context = "TODO: 补充背景、输入材料、边界与不做的事。"
# reference_name = "可选：参考对象名称"

[environment]
description = "TODO: 描述运行环境、依赖与验收方式。"
# port = 3000
# url = "http://localhost:{{port}}"

[commands]
# install = "npm install"
# build = "npm run build"
# test = "npm test"
# run = "npm start"

[[requirements]]
id = "R1"
text = "TODO: 写一条可验证的功能需求。"
priority = "must"
verify = "TODO: 如何验证这一条"

[[acceptance]]
id = "A1"
text = "TODO: 写一条可观测的验收标准。"
method = "TODO: 检查方式"

[[deliverables]]
path = "REPORT.md"
description = "实际执行记录、测试结果与已知差异"

[[rubric]]
id = "correctness"
name = "正确性"
weight = 1.5
description = "交付是否满足功能需求与验收标准"
evidence = "命令输出、测试结果或人工核验"

[[rubric]]
id = "quality"
name = "工程质量"
weight = 1
description = "结构、可维护性、文档是否达标"
evidence = "代码走查与 README"

# [[section]]
# title = "补充说明"
# content = "仅对特定受众展示的额外约束。"
# audience = "all"  # all | contract | executor | evaluator

# [evaluation]
# notes = "给评估 Agent 的补充说明。"

# [scoring]
# scale = 10
# round = 1
# method = "weighted"  # weighted | mean
# integrity_fail_zero = true
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
