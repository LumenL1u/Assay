"""任务定义的加载、规范化与校验。

支持 `task.toml`、`task.json`；安装了 PyYAML 时也支持 `task.yaml`。

任务定义只描述「要评什么」，不包含任何具体模板文本。所有面向
执行/评估 Agent 的措辞都放在 assay/templates/ 中，因此同一套模板可以
评测网页复刻、后端 API、缺陷修复等不同类型的任务。
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

DEFAULT_PATHS = {
    "assets": "assets",
    "reference": "reference",
    "workspace": "workspace",
}

DEFAULT_GRADES = [
    {"min": 8.5, "label": "优秀"},
    {"min": 7.0, "label": "良好"},
    {"min": 5.0, "label": "合格"},
    {"min": 0.0, "label": "不合格"},
]

PRIORITY_LABELS = {
    "must": "必须",
    "should": "应当",
    "nice": "可选",
}

TASK_FILENAMES = ("task.toml", "task.json", "task.yaml", "task.yml")


class TaskError(Exception):
    """任务定义或渲染过程中的可预期错误。"""


@dataclass
class Task:
    id: str
    title: str
    schema_version: int
    version: str
    category: str
    task_type: str
    difficulty: str
    language: str
    objective: str
    context: str
    reference_name: str
    paths: dict[str, str]
    environment: dict[str, Any]
    commands: dict[str, str]
    extra_commands: list[dict[str, str]]
    requirements: list[dict[str, Any]]
    acceptance: list[dict[str, Any]]
    deliverables: list[dict[str, str]]
    constraints: list[str]
    rubric: list[dict[str, Any]]
    scoring: dict[str, Any]
    evaluation: dict[str, Any]
    sections: list[dict[str, str]]
    task_dir: Path
    source: Path
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 原始文件读取
# ---------------------------------------------------------------------------


def find_task_file(task_dir: Path) -> Path | None:
    for name in TASK_FILENAMES:
        candidate = task_dir / name
        if candidate.is_file():
            return candidate
    return None


def _load_raw(task_dir: Path) -> tuple[dict[str, Any], Path]:
    source = find_task_file(task_dir)
    if source is None:
        raise TaskError(f"任务目录中没有 task.toml / task.json / task.yaml: {task_dir}")

    suffix = source.suffix.lower()
    if suffix == ".toml":
        with source.open("rb") as fh:
            data = tomllib.load(fh)
    elif suffix == ".json":
        data = json.loads(source.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise TaskError(
                f"读取 {source.name} 需要 PyYAML；请安装 pyyaml，或改用 task.toml / task.json"
            ) from exc
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
    else:  # pragma: no cover - find_task_file 已限制后缀
        raise TaskError(f"不支持的任务文件格式: {source}")

    if not isinstance(data, dict):
        raise TaskError(f"{source.name} 顶层必须是对象/表")
    return data, source


# ---------------------------------------------------------------------------
# 规范化辅助
# ---------------------------------------------------------------------------


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _pick(raw: dict[str, Any], singular: str, plural: str) -> Any:
    """同时接受 TOML 中单数/复数的数组表写法。"""
    if plural in raw:
        return raw[plural]
    return raw.get(singular)


def _normalize_objective(raw: dict[str, Any]) -> tuple[str, str, str]:
    value = raw.get("objective")
    if value is None:
        return "", "", _text(raw.get("reference_name"))
    if isinstance(value, str):
        return value.strip(), "", _text(raw.get("reference_name"))
    if not isinstance(value, dict):
        raise TaskError("objective 必须是字符串或表")

    objective = _text(value.get("summary") or value.get("text"))
    context = _text(value.get("context") or value.get("background"))
    reference = _text(value.get("reference_name") or raw.get("reference_name"))
    return objective, context, reference


def _normalize_requirements(raw: dict[str, Any]) -> list[dict[str, Any]]:
    items = _as_list(_pick(raw, "requirement", "requirements"))
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            data: dict[str, Any] = {"text": item}
        elif isinstance(item, dict):
            data = dict(item)
        else:
            raise TaskError(f"requirements[{index}] 必须是字符串或表")

        text = _text(data.get("text") or data.get("description"))
        if not text:
            raise TaskError(f"requirements[{index}] 缺少 text")

        result.append(
            {
                "id": _text(data.get("id"), f"R{index}"),
                "text": text,
                "priority": _text(data.get("priority"), "must").lower(),
                "verify": _text(data.get("verify") or data.get("verification")),
                "tags": [_text(tag) for tag in _as_list(data.get("tags")) if _text(tag)],
            }
        )
    return result


def _normalize_acceptance(raw: dict[str, Any]) -> list[dict[str, Any]]:
    items = _as_list(_pick(raw, "acceptance", "acceptance_criteria"))
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            data = {"text": item}
        elif isinstance(item, dict):
            data = dict(item)
        else:
            raise TaskError(f"acceptance[{index}] 必须是字符串或表")

        text = _text(data.get("text") or data.get("description"))
        if not text:
            raise TaskError(f"acceptance[{index}] 缺少 text")

        result.append(
            {
                "id": _text(data.get("id"), f"A{index}"),
                "text": text,
                "method": _text(data.get("method") or data.get("verify")),
            }
        )
    return result


def _normalize_deliverables(raw: dict[str, Any]) -> list[dict[str, str]]:
    items = _as_list(_pick(raw, "deliverable", "deliverables"))
    result: list[dict[str, str]] = []
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            data = {"path": item}
        elif isinstance(item, dict):
            data = dict(item)
        else:
            raise TaskError(f"deliverables[{index}] 必须是字符串或表")

        path = _text(data.get("path") or data.get("pattern") or data.get("name"))
        if not path:
            raise TaskError(f"deliverables[{index}] 缺少 path")
        result.append(
            {
                "path": path,
                "description": _text(data.get("description") or data.get("desc")),
            }
        )
    return result


def _normalize_constraints(raw: dict[str, Any]) -> list[str]:
    items = _as_list(raw.get("constraints"))
    result: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = _text(item.get("text") or item.get("description"))
        else:
            text = _text(item)
        if text:
            result.append(text)
    return result


def _normalize_rubric(raw: dict[str, Any]) -> list[dict[str, Any]]:
    items = _as_list(_pick(raw, "rubric", "rubrics"))
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            data: dict[str, Any] = {"name": item}
        elif isinstance(item, dict):
            data = dict(item)
        else:
            raise TaskError(f"rubric[{index}] 必须是字符串或表")

        key = _text(data.get("id") or data.get("key"), f"dim-{index}")
        name = _text(data.get("name") or data.get("title"), key)
        try:
            weight = float(data.get("weight", 1))
        except (TypeError, ValueError) as exc:
            raise TaskError(f"rubric[{index}].weight 必须是数字") from exc
        if weight <= 0:
            raise TaskError(f"rubric[{index}].weight 必须大于 0")

        result.append(
            {
                "id": key,
                "name": name,
                "weight": weight,
                "description": _text(data.get("description") or data.get("desc")),
                "evidence": _text(data.get("evidence") or data.get("verify")),
            }
        )
    return result


def _normalize_commands(raw: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, str]]]:
    raw_commands = raw.get("commands")
    commands: dict[str, str] = {}
    if raw_commands is not None:
        if not isinstance(raw_commands, dict):
            raise TaskError('commands 必须是表，例如 [commands] test = "..."')
        for key, value in raw_commands.items():
            text = _text(value)
            if text:
                commands[str(key)] = text

    extras: list[dict[str, str]] = []
    for index, item in enumerate(_as_list(_pick(raw, "command", "extra_commands")), 1):
        if not isinstance(item, dict):
            raise TaskError(f"extra_commands[{index}] 必须是表")
        run = _text(item.get("run") or item.get("command"))
        if not run:
            raise TaskError(f"extra_commands[{index}] 缺少 run")
        extras.append(
            {
                "label": _text(item.get("label"), f"附加命令 {index}"),
                "run": run,
            }
        )
    return commands, extras


def _normalize_environment(raw: dict[str, Any]) -> dict[str, Any]:
    value = raw.get("environment")
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise TaskError("environment 必须是表")

    env = dict(value)
    if "port" in env and env["port"] is not None:
        env["port"] = str(env["port"])
    url = _text(env.get("url"))
    if url and "{port}" in url and env.get("port"):
        url = url.replace("{port}", str(env["port"]))
    env["url"] = url
    env["description"] = _text(env.get("description"))
    env["notes"] = _text(env.get("notes"))
    return env


def _normalize_scoring(raw: dict[str, Any]) -> dict[str, Any]:
    value = raw.get("scoring")
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise TaskError("scoring 必须是表")

    try:
        scale = float(value.get("scale", 10))
    except (TypeError, ValueError) as exc:
        raise TaskError("scoring.scale 必须是数字") from exc
    if scale <= 0:
        raise TaskError("scoring.scale 必须大于 0")

    try:
        round_digits = int(value.get("round", 1))
    except (TypeError, ValueError) as exc:
        raise TaskError("scoring.round 必须是整数") from exc
    if round_digits < 0:
        raise TaskError("scoring.round 不能为负数")

    method = _text(value.get("method"), "weighted").lower()
    if method not in {"weighted", "mean"}:
        raise TaskError("scoring.method 只能是 weighted 或 mean")

    raw_grades = _as_list(value.get("grades", value.get("grade")))
    grades: list[dict[str, Any]] = []
    for index, item in enumerate(raw_grades, 1):
        if not isinstance(item, dict):
            raise TaskError(f"scoring.grades[{index}] 必须是表")
        try:
            minimum = float(item.get("min"))
        except (TypeError, ValueError) as exc:
            raise TaskError(f"scoring.grades[{index}].min 必须是数字") from exc
        label = _text(item.get("label"))
        if not label:
            raise TaskError(f"scoring.grades[{index}] 缺少 label")
        grades.append({"min": minimum, "label": label})

    if not grades:
        grades = [dict(item) for item in DEFAULT_GRADES]

    grades.sort(key=lambda item: item["min"], reverse=True)
    return {
        "scale": scale,
        "round": round_digits,
        "method": method,
        "integrity_fail_zero": bool(value.get("integrity_fail_zero", True)),
        "grades": grades,
    }


def _normalize_sections(raw: dict[str, Any]) -> list[dict[str, str]]:
    items = _as_list(_pick(raw, "section", "sections"))
    result: list[dict[str, str]] = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise TaskError(f"sections[{index}] 必须是表")
        title = _text(item.get("title"))
        content = _text(item.get("content"))
        if not title or not content:
            raise TaskError(f"sections[{index}] 需要 title 和 content")
        audience = _text(item.get("audience"), "all").lower()
        if audience not in {"all", "contract", "executor", "evaluator"}:
            raise TaskError(f"sections[{index}].audience 只能是 all/contract/executor/evaluator")
        result.append({"title": title, "content": content, "audience": audience})
    return result


def _normalize_paths(raw: dict[str, Any], task_dir: Path) -> dict[str, str]:
    value = raw.get("paths")
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise TaskError("paths 必须是表")

    resolved: dict[str, str] = {}
    for key, default in DEFAULT_PATHS.items():
        candidate = _text(value.get(key), default)
        path = Path(candidate).expanduser()
        if not path.is_absolute():
            path = task_dir / path
        resolved[key] = str(path.resolve())
    return resolved


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def load_task(task_dir: str | Path) -> Task:
    """加载并校验一个任务目录。"""
    directory = Path(task_dir).expanduser().resolve()
    if not directory.is_dir():
        raise TaskError(f"任务目录不存在: {directory}")

    raw, source = _load_raw(directory)

    try:
        objective, context, reference_name = _normalize_objective(raw)
        requirements = _normalize_requirements(raw)
        acceptance = _normalize_acceptance(raw)
        deliverables = _normalize_deliverables(raw)
        constraints = _normalize_constraints(raw)
        rubric = _normalize_rubric(raw)
        commands, extra_commands = _normalize_commands(raw)
        environment = _normalize_environment(raw)
        scoring = _normalize_scoring(raw)
        sections = _normalize_sections(raw)
        paths = _normalize_paths(raw, directory)
    except TaskError as exc:
        raise TaskError(f"{source}: {exc}") from exc

    evaluation = raw.get("evaluation") or {}
    if not isinstance(evaluation, dict):
        raise TaskError(f"{source}: evaluation 必须是表")

    try:
        schema_version = int(raw.get("schema_version", SCHEMA_VERSION))
    except (TypeError, ValueError) as exc:
        raise TaskError(f"{source}: schema_version 必须是整数") from exc

    errors: list[str] = []
    task_id = _text(raw.get("id"))
    title = _text(raw.get("title"))

    if schema_version != SCHEMA_VERSION:
        errors.append(f"不支持的 schema_version={schema_version}（当前为 {SCHEMA_VERSION}）")
    if not task_id:
        errors.append("缺少 id")
    elif not ID_PATTERN.match(task_id):
        errors.append("id 只能包含字母、数字、点、下划线和短横线")
    if not title:
        errors.append("缺少 title")
    if not objective:
        errors.append("缺少 objective.summary")
    if not rubric:
        errors.append("至少需要一个评分维度 [[rubric]]")

    if errors:
        raise TaskError(f"{source}: " + "；".join(errors))

    return Task(
        id=task_id,
        title=title,
        schema_version=schema_version,
        version=_text(raw.get("version"), "1"),
        category=_text(raw.get("category"), "general"),
        task_type=_text(raw.get("task_type"), "build"),
        difficulty=_text(raw.get("difficulty"), "medium"),
        language=_text(raw.get("language"), "zh"),
        objective=objective,
        context=context,
        reference_name=reference_name,
        paths=paths,
        environment=environment,
        commands=commands,
        extra_commands=extra_commands,
        requirements=requirements,
        acceptance=acceptance,
        deliverables=deliverables,
        constraints=constraints,
        rubric=rubric,
        scoring=scoring,
        evaluation=evaluation,
        sections=sections,
        task_dir=directory,
        source=source,
    )


def find_task_dirs(tasks_dir: str | Path) -> list[Path]:
    """列出目录下所有包含任务定义文件的子目录。"""
    root = Path(tasks_dir).expanduser().resolve()
    if not root.is_dir():
        raise TaskError(f"任务根目录不存在: {root}")
    return [
        child
        for child in sorted(root.iterdir())
        if child.is_dir() and find_task_file(child) is not None
    ]


def validate_task(task: Task) -> list[str]:
    """返回非致命警告（加载阶段已经保证结构合法）。"""
    warnings: list[str] = []

    if task.id != task.task_dir.name:
        warnings.append(f"任务 id（{task.id}）与目录名（{task.task_dir.name}）不一致")

    for key in ("assets", "reference", "workspace"):
        path = Path(task.paths[key])
        if not path.exists():
            warnings.append(f"paths.{key} 不存在: {path}")

    if not task.requirements:
        warnings.append("未定义功能需求（requirements）")
    if not task.acceptance:
        warnings.append("未定义验收标准（acceptance）")
    if not task.deliverables:
        warnings.append("未定义交付物（deliverables）")

    requirement_ids = [item["id"] for item in task.requirements]
    if len(requirement_ids) != len(set(requirement_ids)):
        warnings.append("需求 id 存在重复")
    rubric_ids = [item["id"] for item in task.rubric]
    if len(rubric_ids) != len(set(rubric_ids)):
        warnings.append("评分维度 id 存在重复")

    for item in task.requirements:
        if item["priority"] not in PRIORITY_LABELS:
            warnings.append(
                f"需求 {item['id']} 的 priority={item['priority']} 不在 must/should/nice 中"
            )

    placeholders = [task.title, task.objective, task.context]
    placeholders += [item["text"] for item in task.requirements]
    placeholders += [item["text"] for item in task.acceptance]
    placeholders += [item["description"] for item in task.rubric]
    if any("TODO" in value for value in placeholders if value):
        warnings.append("任务定义中仍有 TODO 占位符，渲染前请补全")

    return warnings
