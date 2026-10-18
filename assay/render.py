"""提示词渲染：把任务变量代入通用模板并写出契约/提示词/清单。"""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .task import Task, TaskError
from .variables import build_variables

VAR_PATTERN = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# 模板文件 -> 输出文件
TEMPLATE_MAP = (
    ("contract.md", "CONTRACT.md"),
    ("executor.md", "executor.md"),
    ("evaluator.md", "evaluator.md"),
)

READONLY_FILES = {"CONTRACT.md"}


@dataclass
class RenderResult:
    task: Task
    out_dir: Path
    rendered: dict[str, str] = field(default_factory=dict)
    files: dict[str, Path] = field(default_factory=dict)
    contract_in_workspace: Path | None = None
    manifest: Path | None = None
    check_only: bool = False


def render_text(text: str, variables: dict[str, str], source: Path) -> str:
    """替换 {{VAR}}，缺少变量时报错。"""
    missing = sorted(set(VAR_PATTERN.findall(text)) - variables.keys())
    if missing:
        raise TaskError(f"{source.name} 缺少变量: {', '.join(missing)}")
    rendered = VAR_PATTERN.sub(lambda match: variables[match.group(1)], text)
    # 空的可选段落会在模板中留下多余空行，统一压缩为单空行。
    return re.sub(r"\n{3,}", "\n\n", rendered)


def check_task_paths(task: Task) -> list[str]:
    problems: list[str] = []
    for key in ("assets", "reference", "workspace"):
        path = Path(task.paths[key])
        if not path.exists():
            problems.append(f"{key}: 不存在 -> {path}")
    return problems


def _prepare_write(path: Path) -> None:
    """如果文件已存在且只读，先恢复可写，避免重复渲染失败。"""
    if path.exists():
        try:
            path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        except OSError:
            pass


def _write(path: Path, content: str, *, readonly: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _prepare_write(path)
    path.write_text(content, encoding="utf-8")
    if readonly:
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def _manifest(task: Task, out_dir: Path, files: dict[str, Path]) -> dict[str, Any]:
    return {
        "schema_version": task.schema_version,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "task": {
            "id": task.id,
            "title": task.title,
            "version": task.version,
            "category": task.category,
            "task_type": task.task_type,
            "difficulty": task.difficulty,
            "language": task.language,
        },
        "source": str(task.source),
        "paths": {
            **task.paths,
            "output": str(out_dir),
            "contract": str(Path(task.paths["workspace"]) / "CONTRACT.md"),
        },
        "prompts": {name: str(path) for name, path in files.items()},
        "rubric": task.rubric,
        "scoring": task.scoring,
    }


def render_task(
    task: Task,
    templates_dir: str | Path,
    out_dir: str | Path,
    *,
    write_contract_in_workspace: bool = True,
    check_only: bool = False,
    check_paths: bool = False,
) -> RenderResult:
    """渲染单个任务。

    Args:
        task: 已加载的任务。
        templates_dir: 通用模板目录。
        out_dir: 该任务的输出目录（通常为 out/<task-id>）。
        write_contract_in_workspace: 是否把只读契约写入工作区根目录。
        check_only: 只校验变量并返回渲染结果，不写文件。
        check_paths: 写文件前校验 assets/reference/workspace 是否存在。
    """
    templates = Path(templates_dir).expanduser().resolve()
    output = Path(out_dir).expanduser().resolve()

    if check_paths:
        problems = check_task_paths(task)
        if problems:
            raise TaskError("路径校验失败：\n" + "\n".join(f"  - {p}" for p in problems))

    variables = build_variables(task, output)
    rendered: dict[str, str] = {}
    for template_name, output_name in TEMPLATE_MAP:
        template_path = templates / template_name
        if not template_path.is_file():
            raise TaskError(f"模板不存在: {template_path}")
        text = template_path.read_text(encoding="utf-8")
        rendered[output_name] = render_text(text, variables, template_path)

    result = RenderResult(
        task=task,
        out_dir=output,
        rendered=rendered,
        check_only=check_only,
    )

    if check_only:
        return result

    result.files = {}
    for output_name, content in rendered.items():
        target = output / output_name
        _write(target, content, readonly=output_name in READONLY_FILES)
        result.files[output_name] = target

    if write_contract_in_workspace:
        workspace = Path(task.paths["workspace"])
        workspace.mkdir(parents=True, exist_ok=True)
        contract = workspace / "CONTRACT.md"
        _write(contract, rendered["CONTRACT.md"], readonly=True)
        result.contract_in_workspace = contract

    manifest_path = output / "manifest.json"
    manifest = _manifest(task, output, result.files)
    _write(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    result.manifest = manifest_path
    result.files["manifest.json"] = manifest_path
    return result
