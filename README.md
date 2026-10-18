# Agent Eval

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](CHANGELOG.md)

通用 Agent 任务评测框架。用一份结构化任务定义，渲染出「任务契约 + 执行 Agent 指令 + 评估 Agent 指令」，从而评测网页复刻、后端 API、缺陷修复等不同类型的任务。

原先是针对 Super Mario 还原的单任务项目；现在 `mario-01` 只是内置示例之一，任务本身与提示词、评分逻辑完全解耦。

- **任务驱动**：新增任务只需写一份 `task.toml`，无需复制提示词。
- **零运行时依赖**：Python 3.11+ 标准库即可运行。
- **可复现**：契约、提示词、评分维度与路径全部落盘，并带只读保护。
- **可审计**：评估 Agent 必须独立执行、给出证据，并做造假检查。

## 目录

- [核心设计](#核心设计)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [评测流程](#评测流程)
- [新增任务](#新增任务)
- [任务类型](#任务类型)
- [评分规则](#评分规则)
- [自定义提示词](#自定义提示词)
- [内置示例](#内置示例)
- [从旧版迁移](#从旧版迁移)
- [开发与贡献](#开发与贡献)
- [安全](#安全)
- [许可证](#许可证)

## 核心设计

1. **任务定义与提示词分离**
   - `tasks/<id>/task.toml` 只描述「评什么」：目标、路径、命令、需求、验收标准、交付物、评分维度。
   - `evalkit/templates/` 只描述「怎么要求 Agent」：契约、执行流程、评估流程。
2. **每个任务独立工作区**
   - 每个任务有自己的 `assets/`、`reference/`、`workspace/`，任务之间互不污染。
3. **契约只读**
   - 渲染时会把 `CONTRACT.md` 同步写入工作区根目录，权限设为 `444`，防止执行过程中被改动。
4. **评分可配置**
   - 支持加权平均或算术平均、自定义分档、造假清零。
5. **零第三方依赖**
   - 只需 Python 3.11+；原生支持 TOML/JSON，安装 PyYAML 后也支持 YAML 任务文件。

## 目录结构

```text
agent-eval/
├── evalkit/                  # 任务加载、校验、渲染与 CLI
│   ├── templates/            # 通用提示词模板（随包发布）
│   │   ├── contract.md
│   │   ├── executor.md
│   │   └── evaluator.md
│   ├── cli.py
│   ├── task.py
│   ├── variables.py
│   ├── render.py
│   └── scaffold.py
├── tasks/                    # 任务定义（每个任务一个目录）
│   ├── mario-01/
│   │   ├── task.toml
│   │   ├── assets/
│   │   ├── reference/
│   │   └── workspace/
│   ├── todo-api-01/
│   └── bugfix-csv-01/
│       └── workspace/        # 带缺陷的起始代码
├── tests/                    # 单元测试与 CLI 集成测试
├── docs/                     # 任务 schema 与架构说明
├── .github/                  # CI、Dependabot、Issue/PR 模板
├── out/                      # 渲染产物（可删除后重新生成）
├── Makefile
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
└── README.md
```

## 快速开始

要求 Python 3.11+。在项目根目录执行：

```bash
# 查看任务
python3 -m evalkit list

# 校验任务定义与路径
python3 -m evalkit validate --all
python3 -m evalkit render --all --check-paths

# 渲染全部任务
python3 -m evalkit render --all

# 只渲染一个任务
python3 -m evalkit render --task mario-01

# 查看任务详情
python3 -m evalkit info --task bugfix-csv-01
```

也可以安装为命令：

```bash
python3 -m pip install -e .
agent-eval list
```

渲染结果：

```text
out/mario-01/
├── CONTRACT.md     # 任务契约（444 只读）
├── executor.md     # 给执行 Agent
├── evaluator.md    # 给评估 Agent
└── manifest.json   # 元数据与评分维度快照
tasks/mario-01/workspace/CONTRACT.md   # 同步到工作区的只读契约
```

## 评测流程

1. **定义任务**：在 `tasks/<id>/task.toml` 写目标、需求、验收标准、评分维度。
2. **校验与渲染**：`validate` → `render`。
3. **执行**：把 `out/<id>/executor.md` 和工作区 `tasks/<id>/workspace/` 交给执行 Agent。
4. **评估**：把 `out/<id>/evaluator.md` 交给独立的评估 Agent。
5. **汇总**：评估 Agent 按评分表输出总分、证据与结论；必要时把结果归档到 `eval-artifacts/`。

框架只负责「定义、校验、生成提示词」，不自动调用模型，也不内置沙箱。执行与评估环境由外部编排负责。

## 新增任务

```bash
python3 -m evalkit new \
  --id my-task-01 \
  --title "我的评测任务" \
  --category backend-api \
  --task-type build
```

然后编辑 `tasks/my-task-01/task.toml`，补全 `TODO`，再执行：

```bash
python3 -m evalkit validate --task my-task-01
python3 -m evalkit render --task my-task-01 --check-paths
```

最小任务定义：

```toml
schema_version = 1
id = "hello-01"
title = "实现 Hello API"
category = "backend-api"
task_type = "build"
difficulty = "easy"

[objective]
summary = "实现一个返回 JSON 的 HTTP 接口。"
context = "考察最小可运行服务与测试。"

[environment]
port = 8000
url = "http://localhost:{port}"

[commands]
install = "npm install"
test = "npm test"
run = "npm start"

[[requirements]]
id = "R1"
text = "GET /hello 返回 {\"message\": \"hello\"}。"
priority = "must"
verify = "用 curl 访问并核对响应。"

[[acceptance]]
id = "A1"
text = "服务可启动，接口返回 200 与正确 JSON。"
method = "启动服务后 curl。"

[[deliverables]]
path = "REPORT.md"
description = "实际命令与测试结果"

[[rubric]]
id = "correctness"
name = "正确性"
weight = 2
description = "接口行为是否符合契约。"
evidence = "curl 输出与测试结果"

[[rubric]]
id = "honesty"
name = "报告诚实度"
weight = 1
description = "报告是否与实际执行一致。"
evidence = "抽查命令与输出"
```

完整字段说明见 [`docs/task-schema.md`](docs/task-schema.md)。

## 任务类型

`task_type` 是开放字段，内置示例覆盖三类：

| 类型 | 含义 | 示例 |
| --- | --- | --- |
| `replicate` | 按参考材料还原可运行产物 | `mario-01` |
| `build` | 从零实现功能 | `todo-api-01` |
| `fix` | 修复已有代码中的缺陷 | `bugfix-csv-01` |

也可以使用 `refactor`、`research` 或自定义值。模板不依赖具体类型，差异全部来自任务定义。

## 评分规则

默认配置：

- 每个维度 0–10 分，按权重加权平均，保留 1 位小数。
- 分档：≥8.5 优秀；≥7 良好；≥5 合格；<5 不合格。
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

- 直接修改 `evalkit/templates/*.md`，对所有任务生效。
- 也可以复制模板到自定义目录，并用 `render --templates <dir>` 覆盖。
- 模板只支持 `{{VAR}}` 替换；列表、表格、条件段落由 `evalkit/variables.py` 预先生成。
- 任务级补充内容用 `[[section]]`，可指定受众：

```toml
[[section]]
title = "性能要求"
content = "首屏加载不超过 2 秒，需提供测量命令。"
audience = "all"   # all | contract | executor | evaluator
```

- 给评估 Agent 的额外说明放在 `[evaluation] notes`。

## 内置示例

| 任务 | 说明 |
| --- | --- |
| `mario-01` | 按参考截图/录屏复刻 Super Mario 可玩网页原型 |
| `todo-api-01` | 从零实现带持久化、校验与测试的 Todo REST API |
| `bugfix-csv-01` | 修复 CSV 引号解析与偶数中位数缺陷；工作区自带 3 个失败测试 |

`bugfix-csv-01` 的起始测试可以这样复现失败：

```bash
cd tasks/bugfix-csv-01/workspace
python3 -m unittest discover -s tests -v
```

## 从旧版迁移

旧结构 `prompts/vars/mario-01.json` + `prompts/templates/*.template.md` 已替换为：

| 旧 | 新 |
| --- | --- |
| `prompts/vars/<task>.json` | `tasks/<id>/task.toml` |
| `prompts/templates/CONTRACT.template.md` | `evalkit/templates/contract.md` |
| `prompts/templates/executor.template.md` | `evalkit/templates/executor.md` |
| `prompts/templates/evaluator.template.md` | `evalkit/templates/evaluator.md` |
| 根目录 `assets/ reference/ workspace/` | 每个任务目录下的同名目录 |
| `prompts/render.py` | `python3 -m evalkit render` |

## 开发与贡献

```bash
# 安装开发依赖（ruff / build）
python3 -m pip install -e ".[dev]"

# 提交前检查：lint + 测试 + 任务校验 + 渲染检查
make check

# 或分别运行
python3 -m ruff check .
python3 -m unittest discover -s tests -v
python3 -m evalkit validate --all
python3 -m evalkit render --all --check-only
```

- 贡献指南：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 架构说明：[`docs/architecture.md`](docs/architecture.md)
- 变更记录：[`CHANGELOG.md`](CHANGELOG.md)
- 行为准则：[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- 提交信息使用 [Conventional Commits](https://www.conventionalcommits.org/)。

注意：渲染产物包含绝对路径；移动仓库后需要重新运行 `render`。

## 安全

本框架不执行 Agent 代码、不提供沙箱。第三方任务定义和起始工作区应视为不可信输入。安全问题请按 [`SECURITY.md`](SECURITY.md) 私下报告。

## 许可证

[MIT](LICENSE) © 2026 agent-eval contributors
