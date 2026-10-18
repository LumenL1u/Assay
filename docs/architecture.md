# Architecture

## Overview

`agent-eval` separates three concerns that are usually tangled together in
agent evaluation projects:

1. **What is being evaluated** — a declarative task definition.
2. **How agents are instructed** — generic prompt templates.
3. **How results are scored** — a rubric and scoring policy attached to the task.

The renderer is the only component that joins them. It turns a task definition
and the generic templates into a per-task evaluation kit.

## Data flow

```text
tasks/<id>/task.toml
        │
        ├── validate ──► warnings / errors
        │
        └── render ──► variables.py (Markdown blocks)
                         │
                         ├── evalkit/templates/contract.md   ──► out/<id>/CONTRACT.md
                         ├── evalkit/templates/executor.md   ──► out/<id>/executor.md
                         └── evalkit/templates/evaluator.md  ──► out/<id>/evaluator.md
                                                       out/<id>/manifest.json
                                                       workspace/CONTRACT.md
```

The executor and evaluator are external agents. The framework does not invoke
them, schedule them, or sandbox them.

## Modules

| Module | Responsibility |
| --- | --- |
| `evalkit/task.py` | Load TOML/JSON/YAML, normalize fields, validate structure, expose `Task` |
| `evalkit/variables.py` | Convert lists, tables, and conditional sections into Markdown variables |
| `evalkit/render.py` | Substitute variables, write outputs, file permissions, manifest |
| `evalkit/scaffold.py` | Create a new task directory with a commented starter definition |
| `evalkit/cli.py` | `list`, `validate`, `render`, `info`, `new` commands |

## Key design decisions

### Structured task data instead of a task-specific prompt

The original project encoded Super Mario requirements directly in three prompt
templates. Adding a second task meant copying and rewriting all three templates.
The task schema makes the differences declarative, so one set of templates
covers replication, implementation, and bug-fix tasks.

### Precomputed Markdown blocks instead of a template language

Templates only support `{{VAR}}` substitution. Lists, rubric tables, conditional
steps, and grading text are generated in `variables.py`. This keeps the
templates readable and avoids adding a Jinja2 dependency or a custom template
dialect.

### Per-task workspaces

Each task owns `assets/`, `reference/`, and `workspace/`. This prevents tasks
from polluting each other and makes a task directory self-contained and
portable.

### Read-only contract

`CONTRACT.md` is written into the workspace with mode `444`. The executor is
instructed not to modify it, and the filesystem enforces the same rule. The
evaluator reads the same contract the executor received.

### Evidence-oriented evaluation

The evaluator prompt requires independent execution, at least three
independently verified acceptance paths, and evidence for every score. The
default scoring policy zeroes the total when fabrication is confirmed.

### Standard library first

Runtime code uses only the Python standard library. TOML support comes from
`tomllib` (Python 3.11+). YAML is an optional extra; JSON is supported natively.

## Extension points

- **New task types** — `task_type` is an open string. No code change is needed
  unless the task needs new conditional prompt behavior.
- **New prompt variables** — add a builder function in `variables.py` and use the
  variable in a template.
- **New scoring rules** — extend `_normalize_scoring` and `_scoring_rule`.
- **New task file formats** — extend `_load_raw` in `task.py`.
- **Task-specific instructions** — use `[[section]]` with `audience`, or
  `[evaluation].notes`, instead of forking templates.

## Non-goals

- Running models or agents.
- Providing an execution sandbox.
- Automatically judging visual output.
- Storing evaluation results in a database.

These belong to the orchestration layer that consumes the rendered prompts.
