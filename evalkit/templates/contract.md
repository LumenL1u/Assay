# 任务契约

> 本文件由 `evalkit` 根据任务定义自动生成，执行期间只读。
> 如需调整任务，请修改任务目录中的 `task.toml` 后重新渲染。

## 任务信息

| 字段 | 值 |
| --- | --- |
| ID | `{{TASK_ID}}` |
| 名称 | {{TASK_TITLE}} |
| 版本 | {{TASK_VERSION}} |
| 类别 | {{CATEGORY}} |
| 类型 | {{TASK_TYPE}} |
| 难度 | {{DIFFICULTY}} |

## 目标

{{OBJECTIVE}}

{{CONTEXT_BLOCK}}

{{REFERENCE_BLOCK}}

## 路径

| 用途 | 路径 |
| --- | --- |
| 工作区 | `{{WORKSPACE}}` |
| 素材 | `{{ASSETS_DIR}}` |
| 参考 | `{{REFERENCE_DIR}}` |
| 提示词输出 | `{{OUTPUT_DIR}}` |

## 环境与命令

{{ENVIRONMENT_BLOCK}}

{{COMMANDS_BLOCK}}

{{URL_LINE}}
{{PORT_LINE}}

## 功能需求

{{REQUIREMENTS_BLOCK}}

## 验收标准

{{ACCEPTANCE_BLOCK}}

## 交付物

{{DELIVERABLES_BLOCK}}

## 约束

{{CONSTRAINTS_BLOCK}}

{{CUSTOM_SECTIONS_BLOCK}}

## 通过判定

满足全部「必须」需求与验收标准，且评分达到合格线（{{PASS_LINE}}）以上。

如发现执行 Agent 伪造工具调用、测试结果、截图或交付物，判定为「不可信」。
