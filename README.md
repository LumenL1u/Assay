# Assay

[![CI](https://github.com/Startanew7/Assay/actions/workflows/ci.yml/badge.svg)](https://github.com/Startanew7/Assay/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-Startanew7%2FAssay-181717.svg)](https://github.com/Startanew7/Assay)

**Assay — 只定义目标，不规定路径的 Agent 能力评测框架。**

用一份结构化任务定义，渲染出「任务契约 + 执行 Agent 指令 + 评估 Agent 指令」，用于评测网页复刻、后端 API、缺陷修复等不同类型的 Agent 任务。

- **任务驱动**：新增任务只写一份 `task.toml`，不用复制提示词。
- **少约束**：只定义目标、验收和评分，不规定技术栈、目录结构和实现路径。
- **零运行时依赖**：Python 3.11+ 标准库即可运行。
- **可复现**：契约、提示词、评分维度全部落盘，契约只读。
- **可审计**：评估 Agent 必须独立执行、给出证据，并做造假检查。

## 快速入门

要求 Python 3.11+。在项目根目录执行：

```bash
# 查看内置任务
python3 -m assay list

# 校验并渲染一个任务
python3 -m assay validate --task mario-01
python3 -m assay render --task mario-01 --check-paths

# 渲染全部任务
python3 -m assay render --all

# 也可以安装为命令
python3 -m pip install -e .
assay list
```

渲染产物：

```text
out/mario-01/
├── CONTRACT.md     # 任务契约（只读）
├── executor.md     # 交给执行 Agent
├── evaluator.md    # 交给评估 Agent
└── manifest.json   # 元数据与评分快照
```

同时会在 `tasks/mario-01/workspace/CONTRACT.md` 写入一份只读契约。

## 评测流程

1. 在 `tasks/<id>/task.toml` 定义目标、需求、验收标准和评分维度。
2. 运行 `python3 -m assay render --task <id>`。
3. 把 `out/<id>/executor.md` 和 `tasks/<id>/workspace/` 交给执行 Agent。
4. 把 `out/<id>/evaluator.md` 交给独立的评估 Agent。
5. 评估 Agent 按评分表输出总分、证据和必须修复项。

框架只负责定义、校验和生成提示词，不自动调用模型，也不提供沙箱。

## 示例结果

> 以下是一次真实运行样例，用于展示 Assay 的输入与输出形态。
> 它不是基准分数，不代表其他模型或 Agent 的表现，也不用于跨运行比较。

| 任务 | 执行结果 | 独立评估 | 等级 |
| --- | --- | --- | --- |
| `mario-01` | 可启动、可操作、可通关；项目自测 38/38 通过 | 8.3 / 10 | 良好 |

![mario-01 通关画面](docs/results/mario-01/clear.png)

*评估 Agent 独立运行时截取的通关画面。Super Mario Bros. 版权归 Nintendo 所有，截图仅用于展示评测输出。*

- **运行信息**：2026-10-18；执行 Agent 与评估 Agent 为独立会话；任务定义见 `tasks/mario-01/task.toml`。
- **证据**：[评估报告](docs/results/mario-01.md) · [执行报告](docs/results/mario-01/REPORT.md)
- **说明**：原始证据（评估脚本、日志、截图）保留在本地 `eval-artifacts/`，未入库；`mario-01` 的素材与参考图因体积/版权原因也未入库，因此他人无法完整复跑该任务。
- `todo-api-01`、`bugfix-csv-01` 尚未跑完整评估流程，故不列出结果。

## 目录结构

```text
assay/
├── assay/              # 任务加载、校验、渲染与 CLI
│   ├── templates/        # 通用提示词模板
│   └── *.py
├── tasks/                # 任务定义
│   ├── mario-01/         # 网页游戏复刻
│   ├── todo-api-01/      # 后端 API 实现
│   └── bugfix-csv-01/    # 缺陷修复（带起始代码）
├── tests/                # 单元测试与 CLI 集成测试
├── docs/results/         # 示例运行与评估报告
├── out/                  # 渲染产物（可删除后重新生成）
├── pyproject.toml
├── LICENSE
└── README.md
```

每个任务目录包含：

```text
tasks/<id>/
├── task.toml     # 任务定义
├── assets/       # 素材
├── reference/    # 参考材料（截图/录屏等）
└── workspace/    # 执行 Agent 的工作区
```

## 添加任务

```bash
python3 -m assay new --id my-task-01 --title "我的评测任务" --category backend-api
```

编辑 `tasks/my-task-01/task.toml`，补全 `TODO` 后重新渲染：

```bash
python3 -m assay validate --task my-task-01
python3 -m assay render --task my-task-01 --check-paths
```

任务定义只回答「做成什么样算成功」，不写实现步骤。技术栈、目录结构、测试方式、运行命令都留给执行 Agent 决定。

最小任务定义：

```toml
schema_version = 1
id = "hello-01"
title = "实现 Hello API"
category = "backend-api"
task_type = "build"

objective = "实现一个返回 JSON 的 HTTP 接口。技术栈和运行方式由你决定。"

requirements = [
  "GET /hello 返回 {\"message\": \"hello\"}。",
]

acceptance = [
  "评估 Agent 能按项目说明启动服务并验证响应。",
]

deliverables = ["REPORT.md"]

constraints = [
  "不得修改 CONTRACT.md，不得伪造测试或执行结果。",
]

[[rubric]]
id = "correctness"
name = "正确性"
weight = 2
description = "接口行为是否符合目标与验收标准。"
evidence = "实际请求与测试结果。"

[[rubric]]
id = "honesty"
name = "报告与自测"
weight = 1
description = "运行说明是否可复现，结果是否如实记录。"
evidence = "抽查 REPORT.md 中的命令与输出。"
```

常用字段（除 `id`、`title`、`objective`、`rubric` 外均可省略）：

| 字段 | 说明 |
| --- | --- |
| `id` / `title` / `category` / `task_type` / `difficulty` | 任务基本信息 |
| `objective` | 目标字符串；也可写成 `[objective]` 表，含 `summary` / `context` |
| `reference_name` | 可选，参考对象名称 |
| `requirements` | 字符串数组；也可用 `[[requirements]]` 表写 `id` / `text` / `priority` / `verify` |
| `acceptance` | 字符串数组；也可用 `[[acceptance]]` 表写 `id` / `text` / `method` |
| `deliverables` | 字符串数组；也可用 `[[deliverables]]` 表写 `path` / `description` |
| `constraints` | 字符串数组 |
| `[[rubric]]` | `id`、`name`、`weight`、`description`、`evidence` |
| `[paths]` | 可选，默认为任务目录下的 `assets/`、`reference/`、`workspace/` |
| `[environment]` / `[commands]` | 可选；不写则由执行 Agent 自行决定并记录在报告中 |
| `[scoring]` | 可选；默认加权平均、10 分制 |
| `[[section]]` / `[evaluation]` | 可选的补充说明，仅特殊任务需要 |

## 任务类型

`task_type` 是开放字段，内置示例：

| 任务 | 类型 | 说明 |
| --- | --- | --- |
| `mario-01` | `replicate` | 按参考材料复刻可玩网页原型 |
| `todo-api-01` | `build` | 从零实现 Todo REST API |
| `bugfix-csv-01` | `fix` | 修复 CSV 解析与中位数缺陷 |

`bugfix-csv-01` 自带 3 个故意失败的测试：

```bash
cd tasks/bugfix-csv-01/workspace
python3 -m unittest discover -s tests -v
```

## 评分

默认规则：

- 每个维度 0–10 分，按权重加权平均，保留 1 位小数。
- 等级：≥8.5 优秀；≥7 良好；≥5 合格；<5 不合格。
- 发现伪造工具调用、测试结果、截图或产物：总分记 0，标注「不可信」。

在任务中覆盖：

```toml
[scoring]
scale = 10
round = 1
method = "weighted"        # weighted | mean
integrity_fail_zero = true

[[scoring.grades]]
min = 9
label = "A"

[[scoring.grades]]
min = 0
label = "F"
```

## 自定义提示词

模板位于 `assay/templates/`，直接修改对所有任务生效。也可以复制到自定义目录后用 `--templates <dir>` 覆盖。

任务级补充内容用 `[[section]]`：

```toml
[[section]]
title = "性能要求"
content = "首屏加载不超过 2 秒，需提供测量命令。"
audience = "all"
```

## 开发

```bash
python3 -m pip install -e ".[dev]"

python3 -m ruff check .
python3 -m unittest discover -s tests -v
python3 -m assay validate --all
python3 -m assay render --all --check-only
```

提交信息使用 [Conventional Commits](https://www.conventionalcommits.org/)。

## 许可证

[MIT](LICENSE)
