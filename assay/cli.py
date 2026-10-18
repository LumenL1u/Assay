"""命令行入口：list / validate / render / info / new。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .render import render_task
from .scaffold import create_task
from .task import (
    Task,
    TaskError,
    find_task_dirs,
    load_task,
    validate_task,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _default_dir(name: str) -> Path:
    """优先使用当前目录，其次使用仓库/安装目录；都不存在时返回当前目录。"""
    for candidate in (Path.cwd() / name, PROJECT_ROOT / name):
        if candidate.exists():
            return candidate
    return Path.cwd() / name


def _default_templates_dir() -> Path:
    """模板优先取项目覆盖版本，退回包内置版本（wheel 安装后可用）。"""
    for candidate in (
        Path.cwd() / "templates",
        PROJECT_ROOT / "templates",
    ):
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parent / "templates"


DEFAULT_TASKS_DIR = _default_dir("tasks")
DEFAULT_TEMPLATES_DIR = _default_templates_dir()
DEFAULT_OUT_DIR = _default_dir("out")


def _resolve_tasks(args: argparse.Namespace) -> list[Task]:
    tasks_dir = Path(args.tasks_dir).expanduser().resolve()

    if args.task:
        candidate = Path(args.task).expanduser()
        if not candidate.is_dir():
            candidate = tasks_dir / args.task
        if not candidate.is_dir():
            raise TaskError(f"找不到任务: {candidate}")
        return [load_task(candidate)]

    if getattr(args, "all", False):
        directories = find_task_dirs(tasks_dir)
        if not directories:
            raise TaskError(f"没有找到任何任务: {tasks_dir}")
        return [load_task(directory) for directory in directories]

    raise TaskError("请指定 --task <id|目录> 或 --all")


def _print_warnings(task: Task) -> None:
    for warning in validate_task(task):
        print(f"  [WARN] {task.id}: {warning}")


def cmd_list(args: argparse.Namespace) -> int:
    tasks_dir = Path(args.tasks_dir).expanduser().resolve()
    try:
        directories = find_task_dirs(tasks_dir)
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if not directories:
        print(f"[INFO] 没有任务: {tasks_dir}")
        return 0

    print(f"{'ID':<22} {'类型':<10} {'类别':<18} {'难度':<8} 名称")
    print("-" * 88)
    failed = False
    for directory in directories:
        try:
            task = load_task(directory)
        except TaskError as exc:
            print(f"{directory.name:<22} [ERROR] {exc}", file=sys.stderr)
            failed = True
            continue
        print(
            f"{task.id:<22} {task.task_type:<10} {task.category:<18} "
            f"{task.difficulty:<8} {task.title}"
        )
    return 1 if failed else 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        tasks = _resolve_tasks(args)
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    for task in tasks:
        summary = (
            f"{len(task.requirements)} 条需求, "
            f"{len(task.acceptance)} 条验收, "
            f"{len(task.rubric)} 个评分维度"
        )
        print(f"[OK] {task.id}: {summary}")
        _print_warnings(task)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    try:
        tasks = _resolve_tasks(args)
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    templates_dir = Path(args.templates).expanduser().resolve()
    out_root = Path(args.out).expanduser().resolve()
    failed = False

    for task in tasks:
        _print_warnings(task)
        try:
            result = render_task(
                task,
                templates_dir,
                out_root / task.id,
                write_contract_in_workspace=not args.no_contract_in_workspace,
                check_only=args.check_only,
                check_paths=args.check_paths,
            )
        except TaskError as exc:
            print(f"[ERROR] {task.id}: {exc}", file=sys.stderr)
            failed = True
            continue

        if result.check_only:
            print(f"[OK] {task.id}: 可渲染 {len(result.rendered)} 个文件 -> {result.out_dir}")
            continue

        for name, path in result.files.items():
            suffix = "（只读）" if name == "CONTRACT.md" else ""
            print(f"[OK] {task.id}: {path}{suffix}")
        if result.contract_in_workspace:
            print(f"[OK] {task.id}: {result.contract_in_workspace}（只读）")

    return 1 if failed else 0


def cmd_info(args: argparse.Namespace) -> int:
    try:
        task = _resolve_tasks(args)[0]
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"ID:          {task.id}")
    print(f"名称:        {task.title}")
    print(f"版本:        {task.version}")
    print(f"类别/类型:   {task.category} / {task.task_type}")
    print(f"难度:        {task.difficulty}")
    print(f"来源:        {task.source}")
    print(f"目标:        {task.objective}")
    if task.context:
        print(f"背景:        {task.context}")
    if task.reference_name:
        print(f"参考对象:    {task.reference_name}")

    print("\n路径:")
    for key in ("workspace", "assets", "reference"):
        print(f"  {key:<10} {task.paths[key]}")

    print("\n命令:")
    for key, command in task.commands.items():
        print(f"  {key:<10} {command}")
    for item in task.extra_commands:
        print(f"  {item['label']:<10} {item['run']}")

    print(f"\n需求（{len(task.requirements)}）:")
    for item in task.requirements:
        print(f"  {item['id']} [{item['priority']}] {item['text']}")

    print(f"\n验收标准（{len(task.acceptance)}）:")
    for item in task.acceptance:
        print(f"  {item['id']} {item['text']}")

    print(f"\n评分维度（{len(task.rubric)}）:")
    for item in task.rubric:
        print(f"  - {item['name']} ({item['id']}) 权重 {item['weight']:g}")

    warnings = validate_task(task)
    if warnings:
        print("\n警告:")
        for warning in warnings:
            print(f"  [WARN] {warning}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    tasks_dir = Path(args.tasks_dir).expanduser().resolve()
    try:
        target = create_task(
            tasks_dir,
            args.id,
            args.title,
            category=args.category,
            task_type=args.task_type,
        )
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] 已创建任务: {target}")
    print(f"     编辑 {target / 'task.toml'}，然后运行:")
    print(f"     python3 -m assay validate --task {args.id}")
    print(f"     python3 -m assay render --task {args.id}")
    return 0


def _add_selection(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task", help="任务 ID 或任务目录")
    group.add_argument("--all", action="store_true", help="处理 tasks 下所有任务")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assay",
        description="通用 Agent 任务评测：任务定义、校验与提示词渲染",
    )
    parser.add_argument(
        "--tasks-dir",
        default=str(DEFAULT_TASKS_DIR),
        help=f"任务根目录（默认 {DEFAULT_TASKS_DIR}）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出全部任务")
    list_parser.set_defaults(func=cmd_list)

    validate_parser = sub.add_parser("validate", help="校验任务定义")
    _add_selection(validate_parser)
    validate_parser.set_defaults(func=cmd_validate)

    render_parser = sub.add_parser("render", help="渲染契约与提示词")
    _add_selection(render_parser)
    render_parser.add_argument(
        "--templates",
        default=str(DEFAULT_TEMPLATES_DIR),
        help=f"模板目录（默认 {DEFAULT_TEMPLATES_DIR}）",
    )
    render_parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help=f"输出根目录（默认 {DEFAULT_OUT_DIR}）",
    )
    render_parser.add_argument("--check-only", action="store_true", help="只校验可渲染性，不写文件")
    render_parser.add_argument(
        "--check-paths", action="store_true", help="写文件前校验任务路径是否存在"
    )
    render_parser.add_argument(
        "--no-contract-in-workspace",
        action="store_true",
        help="不把 CONTRACT.md 写入工作区",
    )
    render_parser.set_defaults(func=cmd_render)

    info_parser = sub.add_parser("info", help="查看单个任务详情")
    info_parser.add_argument("--task", required=True, help="任务 ID 或任务目录")
    info_parser.set_defaults(func=cmd_info, all=False)

    new_parser = sub.add_parser("new", help="创建任务骨架")
    new_parser.add_argument("--id", required=True, help="任务 ID")
    new_parser.add_argument("--title", help="任务名称（默认与 ID 相同）")
    new_parser.add_argument("--category", default="general", help="任务类别")
    new_parser.add_argument(
        "--task-type",
        default="build",
        choices=["build", "replicate", "fix", "refactor", "research"],
        help="任务类型",
    )
    new_parser.set_defaults(func=cmd_new)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TaskError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
