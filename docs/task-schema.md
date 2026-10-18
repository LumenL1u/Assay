# 任务定义参考

任务定义位于 `tasks/<id>/task.toml`（也支持 `task.json`；安装 PyYAML 后支持 `task.yaml`）。

所有相对路径都相对于任务目录解析。渲染输出写入 `out/<id>/`，契约同时写入工作区根目录。

## 顶层字段

| 字段 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | 否 | `1` | 当前仅支持 `1` |
| `id` | 是 | — | 任务 ID，匹配 `[A-Za-z0-9][A-Za-z0-9._-]*` |
| `title` | 是 | — | 任务名称 |
| `version` | 否 | `1` | 任务定义版本 |
| `category` | 否 | `general` | 任务类别，如 `web-game`、`backend-api` |
| `task_type` | 否 | `build` | `replicate` / `build` / `fix` / `refactor` / `research` 或自定义值 |
| `difficulty` | 否 | `medium` | 难度标签，自由文本 |
| `language` | 否 | `zh` | 预留字段，当前模板为中文 |

## `[objective]`

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `summary` | 是 | 一两句话说明要完成的目标 |
| `context` | 否 | 背景、边界、不做的事 |
| `reference_name` | 否 | 参考对象名称，如 `Super Mario` |

`objective` 也可以直接写成字符串：`objective = "..."`。

## `[paths]`

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `assets` | `assets` | 素材目录 |
| `reference` | `reference` | 参考截图/录屏等材料 |
| `workspace` | `workspace` | 执行 Agent 的工作区 |

相对路径基于任务目录。目录不存在时 `validate` 会给出警告，`render --check-paths` 会报错。

## `[environment]`

| 字段 | 说明 |
| --- | --- |
| `description` | 运行环境说明 |
| `notes` | 额外说明 |
| `port` | 端口 |
| `url` | 访问地址；支持 `{port}` 占位符 |

没有 URL 的任务（如 CLI/库）可以省略 `url`，评估流程会自动改用 `run` 命令验证。

## `[commands]`

常用键：`install`、`build`、`test`、`run`、`start`、`dev`、`lint`、`format`、`typecheck`。其他键也会原样渲染。

```toml
[commands]
install = "npm install"
test = "npm test"

[[extra_commands]]
label = "端到端测试"
run = "npm run test:e2e"
```

渲染顺序为内置键顺序，其后是自定义键与 `extra_commands`。

## `[[requirements]]`

| 字段 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `id` | 否 | `R1`、`R2`… | 需求编号 |
| `text` | 是 | — | 可验证的需求描述 |
| `priority` | 否 | `must` | `must` / `should` / `nice` |
| `verify` | 否 | — | 验证方法 |

也接受字符串数组：`requirements = ["...", "..."]`。TOML 中单数 `[[requirement]]` 与复数 `[[requirements]]` 均可。

## `[[acceptance]]`

| 字段 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `id` | 否 | `A1`、`A2`… | 验收编号 |
| `text` | 是 | — | 可观测的验收标准 |
| `method` | 否 | — | 核验方式 |

也接受字符串数组，或使用键名 `acceptance_criteria`。

## `[[deliverables]]`

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `path` | 是 | 文件、目录或 glob，如 `artifacts/*.png` |
| `description` | 否 | 交付物说明 |

也接受字符串数组。

## `constraints`

字符串数组，或数组表：

```toml
constraints = ["仅使用标准库", "不得伪造测试"]

# 或
[[constraints]]
text = "仅使用标准库"
```

## `[[rubric]]`

评分维度。

| 字段 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `id` | 否 | `dim-1`… | 维度标识 |
| `name` | 否 | 与 `id` 相同 | 展示名称 |
| `weight` | 否 | `1` | 权重，必须大于 0 |
| `description` | 否 | — | 评分要点 |
| `evidence` | 否 | — | 评分所需证据 |

至少需要一个评分维度。

## `[scoring]`

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `scale` | `10` | 单维度满分 |
| `round` | `1` | 总分保留小数位 |
| `method` | `weighted` | `weighted` 加权平均；`mean` 算术平均 |
| `integrity_fail_zero` | `true` | 发现造假时总分记 0 |

分档通过 `[[scoring.grades]]` 配置；未配置时使用：

```text
≥8.5 优秀；≥7 良好；≥5 合格；<5 不合格
```

```toml
[scoring]
scale = 10
round = 1
method = "weighted"

[[scoring.grades]]
min = 9
label = "A"

[[scoring.grades]]
min = 0
label = "F"
```

## `[[section]]`

任务级补充段落，按受众插入。

| 字段 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `title` | 是 | — | Markdown 标题 |
| `content` | 是 | — | Markdown 正文 |
| `audience` | 否 | `all` | `all` / `contract` / `executor` / `evaluator` |

## `[evaluation]`

| 字段 | 说明 |
| --- | --- |
| `notes` | 仅插入评估 Agent 指令的补充说明 |

## 模板变量

模板只支持 `{{VAR}}`，未知变量会导致渲染失败。全部变量由 `evalkit/variables.py` 生成：

| 变量 | 内容 |
| --- | --- |
| `TASK_ID` / `TASK_TITLE` / `TASK_VERSION` | 任务基本信息 |
| `CATEGORY` / `TASK_TYPE` / `DIFFICULTY` / `LANGUAGE` | 分类信息 |
| `OBJECTIVE` / `CONTEXT_BLOCK` | 目标与背景段落 |
| `REFERENCE_NAME` / `REFERENCE_BLOCK` / `REFERENCE_CLAUSE` | 参考对象、参考材料段落、评估时的对比提示 |
| `TASK_DIR` / `WORKSPACE` / `ASSETS_DIR` / `REFERENCE_DIR` | 绝对路径 |
| `OUTPUT_DIR` / `CONTRACT_PATH` | 渲染输出目录、工作区契约路径 |
| `ENVIRONMENT_BLOCK` / `COMMANDS_BLOCK` | 环境说明、命令列表 |
| `URL_LINE` / `PORT_LINE` | 地址与端口行（无则为空） |
| `REQUIREMENTS_BLOCK` / `ACCEPTANCE_BLOCK` | 需求与验收标准列表 |
| `DELIVERABLES_BLOCK` / `CONSTRAINTS_BLOCK` | 交付物与约束列表 |
| `RUBRIC_TABLE` / `SCORING_RULE` / `SCALE` / `PASS_LINE` | 评分表、计分规则、满分、合格线 |
| `TEST_STEP` / `RUNTIME_STEP` / `INTEGRITY_CLAUSE` | 评估流程中的条件性步骤 |
| `CUSTOM_SECTIONS_BLOCK` | `audience=all/contract` 的自定义段落 |
| `EXECUTOR_EXTRA_BLOCK` | `audience=all/executor` 的自定义段落 |
| `EVALUATOR_EXTRA_BLOCK` | `audience=all/evaluator` 的自定义段落 + `evaluation.notes` |

## 渲染行为

- `out/<id>/CONTRACT.md`：权限 `444`。
- `out/<id>/executor.md`、`evaluator.md`：普通可写文件。
- `out/<id>/manifest.json`：任务元数据、路径、评分维度快照。
- `tasks/<id>/workspace/CONTRACT.md`：默认同步一份只读契约；用 `--no-contract-in-workspace` 关闭。
- 渲染会压缩连续 3 个以上空行为 2 个，避免可选段落留下大片空白。
- 重新渲染会覆盖 `out/<id>/` 下的生成文件。

## CLI

在项目根目录执行：

```bash
python3 -m evalkit list
python3 -m evalkit validate --all
python3 -m evalkit validate --task mario-01
python3 -m evalkit render --all
python3 -m evalkit render --task mario-01 --check-paths
python3 -m evalkit render --all --check-only
python3 -m evalkit info --task mario-01
python3 -m evalkit new --id my-task --title "我的任务"
```

`--tasks-dir` 是全局参数，需放在子命令之前：

```bash
python3 -m evalkit --tasks-dir /path/to/tasks list
```
