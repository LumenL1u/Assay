"""把结构化任务定义转换为模板变量。

模板只做 `{{VAR}}` 替换；所有列表、表格、条件性段落都在这里预先生成
Markdown 文本，这样模板本身保持通用、易读。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .task import PRIORITY_LABELS, Task

COMMAND_LABELS = {
    "install": "安装",
    "build": "构建",
    "test": "测试",
    "run": "运行",
    "dev": "开发服务",
    "start": "启动",
    "lint": "检查",
    "format": "格式化",
    "typecheck": "类型检查",
}

COMMAND_ORDER = (
    "install",
    "build",
    "test",
    "run",
    "start",
    "dev",
    "lint",
    "format",
    "typecheck",
)


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _cell(value: Any) -> str:
    return _clean(value).replace("|", "\\|").replace("\n", "<br>")


def _bullets(lines: list[str], empty: str = "- （未定义）") -> str:
    return "\n".join(lines) if lines else empty


def _reference_dir_has_content(task: Task) -> bool:
    directory = Path(task.paths["reference"])
    if not directory.is_dir():
        return False
    ignored = {".gitkeep", ".DS_Store"}
    return any(child.name not in ignored for child in directory.iterdir())


def _has_reference(task: Task) -> bool:
    return bool(task.reference_name) or _reference_dir_has_content(task)


def _requirements_block(task: Task) -> str:
    lines: list[str] = []
    for item in task.requirements:
        priority = PRIORITY_LABELS.get(item["priority"], item["priority"])
        lines.append(f"- **{item['id']}**（{priority}）{item['text']}")
        if item["verify"]:
            lines.append(f"  - 验证：{item['verify']}")
    return _bullets(lines, "- （未定义功能需求）")


def _acceptance_block(task: Task) -> str:
    lines: list[str] = []
    for item in task.acceptance:
        lines.append(f"- **{item['id']}** {item['text']}")
        if item["method"]:
            lines.append(f"  - 核验方式：{item['method']}")
    return _bullets(lines, "- （未定义验收标准）")


def _deliverables_block(task: Task) -> str:
    lines: list[str] = []
    for item in task.deliverables:
        line = f"- `{item['path']}`"
        if item["description"]:
            line += f" — {item['description']}"
        lines.append(line)
    return _bullets(lines, "- （未定义交付物）")


def _constraints_block(task: Task) -> str:
    return _bullets([f"- {item}" for item in task.constraints], "- （无额外约束）")


def _commands_block(task: Task) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for key in COMMAND_ORDER:
        if key in task.commands:
            label = COMMAND_LABELS.get(key, key)
            lines.append(f"- {label}：`{task.commands[key]}`")
            seen.add(key)
    for key, command in task.commands.items():
        if key in seen:
            continue
        lines.append(f"- {key}：`{command}`")
    for item in task.extra_commands:
        lines.append(f"- {item['label']}：`{item['run']}`")
    return "\n".join(lines)


def _environment_block(task: Task) -> str:
    lines: list[str] = []
    description = _clean(task.environment.get("description"))
    notes = _clean(task.environment.get("notes"))
    if description:
        lines.append(description)
    if notes:
        lines.append(notes)
    if lines:
        return "\n".join(lines)

    has_runtime_hints = bool(
        task.commands
        or task.extra_commands
        or task.environment.get("url")
        or task.environment.get("port")
    )
    if has_runtime_hints:
        return ""
    return (
        "未指定固定技术栈、命令或运行地址；由执行 Agent 自行决定，"
        "并在 REPORT.md 中说明如何运行和验证。"
    )


def _reference_block(task: Task) -> str:
    lines: list[str] = []
    if task.reference_name:
        lines.append(f"- 参考对象：{task.reference_name}")
    if _reference_dir_has_content(task):
        lines.append(f"- 参考材料：`{task.paths['reference']}`")
    if not lines:
        return ""
    return "### 参考\n\n" + "\n".join(lines)


def _reference_clause(task: Task) -> str:
    if not _has_reference(task):
        return ""
    return "   - 对比参考材料与你的独立观察结果，记录可复核的视觉/行为偏差。"


def _rubric_table(task: Task) -> str:
    header = "| 维度 | 权重 | 评分要点 | 证据要求 |\n| --- | ---: | --- | --- |"
    rows: list[str] = []
    for item in task.rubric:
        rows.append(
            "| "
            f"{_cell(item['name'])}（`{_cell(item['id'])}`） | "
            f"{item['weight']:g} | "
            f"{_cell(item['description']) or '—'} | "
            f"{_cell(item['evidence']) or '命令、输出、文件或截图'} |"
        )
    return header + ("\n" + "\n".join(rows) if rows else "")


def _grade_text(grades: list[dict[str, Any]]) -> str:
    ordered = sorted(grades, key=lambda item: item["min"], reverse=True)
    parts: list[str] = []
    for index, grade in enumerate(ordered):
        is_last = index == len(ordered) - 1
        if is_last and grade["min"] <= 0 and index > 0:
            parts.append(f"<{ordered[index - 1]['min']:g} {grade['label']}")
        else:
            parts.append(f"≥{grade['min']:g} {grade['label']}")
    return "；".join(parts) + "。"


def _pass_line(task: Task) -> str:
    positive = sorted(
        (item for item in task.scoring["grades"] if item["min"] > 0),
        key=lambda item: item["min"],
    )
    target = (
        positive[0] if positive else sorted(task.scoring["grades"], key=lambda item: item["min"])[0]
    )
    return f"{target['min']:g} 分（{target['label']}）"


def _scoring_rule(task: Task) -> str:
    scoring = task.scoring
    scale = f"{scoring['scale']:g}"
    digits = scoring["round"]
    if scoring["method"] == "mean":
        formula = f"总分 = 各维度平均分（0–{scale} 分）"
    else:
        formula = f"总分 = Σ(维度得分 × 权重) / Σ权重（0–{scale} 分）"
    formula += f"，保留 {digits} 位小数。"

    rule = f"{formula}等级：{_grade_text(scoring['grades'])}"
    if scoring["integrity_fail_zero"]:
        rule += "若确认执行 Agent 伪造工具调用、测试结果、截图或产物，总分记 0 并标注「不可信」。"
    return rule


def _test_step(task: Task) -> str:
    command = task.commands.get("test")
    if command:
        return f"运行契约中的测试命令 `{command}`，记录通过/失败；测试缺失或造假直接在该项记 0 分。"
    return "运行项目自带的测试；若没有现成测试，则按验收标准自行设计验证。记录实际命令与输出。"


def _runtime_step(task: Task) -> str:
    url = _clean(task.environment.get("url"))
    if url:
        return (
            f"访问 {url}，检查服务能否启动、页面/接口是否符合验收标准，记录真实响应、截图或日志。"
        )
    command = task.commands.get("run") or task.commands.get("start") or task.commands.get("dev")
    if command:
        return f"按 `{command}` 启动或调用交付物，独立操作并验证验收标准，记录实际输入与输出。"
    return (
        "查看工作区 README/REPORT 中记录的启动方式，独立启动或调用交付物；"
        "若未记录，自行判断运行方式并说明。记录实际输入与输出。"
    )


def _sections_block(task: Task, audience: str) -> str:
    parts: list[str] = []
    if audience == "evaluator":
        notes = _clean(task.evaluation.get("notes"))
        if notes:
            parts.append(f"## 补充评估说明\n\n{notes}")

    for section in task.sections:
        if section["audience"] not in {"all", audience}:
            continue
        parts.append(f"## {section['title']}\n\n{section['content']}")
    return "\n\n".join(parts)


def _context_block(task: Task) -> str:
    if not task.context:
        return ""
    return f"### 背景\n\n{task.context}"


def _port_line(task: Task) -> str:
    port = _clean(task.environment.get("port"))
    url = _clean(task.environment.get("url"))
    if port and not url:
        return f"- 端口：{port}"
    return ""


def _url_line(task: Task) -> str:
    url = _clean(task.environment.get("url"))
    return f"- 访问地址：{url}" if url else ""


def build_variables(task: Task, out_dir: Path) -> dict[str, str]:
    """生成渲染模板所需的全部变量（值为已格式化的字符串）。"""
    contract_path = Path(task.paths["workspace"]) / "CONTRACT.md"
    integrity_clause = (
        "一旦确认，按计分规则将总分记 0。"
        if task.scoring["integrity_fail_zero"]
        else "在结论中明确标注。"
    )

    return {
        # 基本信息
        "TASK_ID": task.id,
        "TASK_TITLE": task.title,
        "TASK_VERSION": task.version,
        "CATEGORY": task.category,
        "TASK_TYPE": task.task_type,
        "DIFFICULTY": task.difficulty,
        "LANGUAGE": task.language,
        # 路径
        "TASK_DIR": str(task.task_dir),
        "WORKSPACE": task.paths["workspace"],
        "ASSETS_DIR": task.paths["assets"],
        "REFERENCE_DIR": task.paths["reference"],
        "OUTPUT_DIR": str(Path(out_dir).resolve()),
        "CONTRACT_PATH": str(contract_path.resolve()),
        # 目标与参考
        "OBJECTIVE": task.objective,
        "CONTEXT_BLOCK": _context_block(task),
        "REFERENCE_NAME": task.reference_name,
        "REFERENCE_BLOCK": _reference_block(task),
        "REFERENCE_CLAUSE": _reference_clause(task),
        # 环境与命令
        "ENVIRONMENT_BLOCK": _environment_block(task),
        "COMMANDS_BLOCK": _commands_block(task),
        "URL_LINE": _url_line(task),
        "PORT_LINE": _port_line(task),
        # 需求与交付
        "REQUIREMENTS_BLOCK": _requirements_block(task),
        "ACCEPTANCE_BLOCK": _acceptance_block(task),
        "DELIVERABLES_BLOCK": _deliverables_block(task),
        "CONSTRAINTS_BLOCK": _constraints_block(task),
        # 评分
        "RUBRIC_TABLE": _rubric_table(task),
        "SCORING_RULE": _scoring_rule(task),
        "SCALE": f"{task.scoring['scale']:g}",
        "PASS_LINE": _pass_line(task),
        "TEST_STEP": _test_step(task),
        "RUNTIME_STEP": _runtime_step(task),
        "INTEGRITY_CLAUSE": integrity_clause,
        # 自定义段落
        "CUSTOM_SECTIONS_BLOCK": _sections_block(task, "contract"),
        "EXECUTOR_EXTRA_BLOCK": _sections_block(task, "executor"),
        "EVALUATOR_EXTRA_BLOCK": _sections_block(task, "evaluator"),
    }
