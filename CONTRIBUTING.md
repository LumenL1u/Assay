# Contributing

Thanks for considering a contribution. This project evaluates agents against
task definitions, so contributions usually fall into one of three categories:

1. Improving the `evalkit` toolkit or CLI.
2. Improving the generic prompt templates.
3. Adding or improving an example task.

## Development setup

Requirements: Python 3.11+ and `make` (optional).

```bash
git clone <repository-url>
cd agent-eval
python3 -m pip install -e ".[dev]"
```

Run the checks before opening a pull request:

```bash
make check
# equivalent to:
python3 -m ruff check .
python3 -m unittest discover -s tests -v
python3 -m evalkit validate --all
python3 -m evalkit render --all --check-only
```

## Adding a task

```bash
python3 -m evalkit new \
  --id my-task-01 \
  --title "My evaluation task" \
  --category backend-api \
  --task-type build
```

Then:

1. Fill in every `TODO` in `tasks/my-task-01/task.toml`.
2. Put starter code, if any, in `tasks/my-task-01/workspace/`.
3. Put fixtures and reference materials in `assets/` and `reference/`.
4. Make sure every requirement is observable and every acceptance criterion has
   a verification method.
5. Run `make validate` and `make render`.
6. Commit the task definition and any starter files. Do **not** commit generated
   `CONTRACT.md` files or the `out/` directory.

See [`docs/task-schema.md`](docs/task-schema.md) for every supported field.

## Task quality checklist

- [ ] The task has a single, testable objective.
- [ ] Requirements use `must` / `should` / `nice` consistently.
- [ ] Acceptance criteria describe observable outcomes, not implementation steps.
- [ ] The rubric covers correctness, quality, and honesty.
- [ ] Commands work from a clean checkout.
- [ ] Any starter workspace fails in the intended way before the task is solved.
- [ ] The task does not require network services unless explicitly documented.

## Code style

- Python 3.11+, standard library only for runtime code.
- Formatting and linting are handled by Ruff; configuration lives in
  `pyproject.toml`.
- Keep user-facing text in the existing language of the file you are editing.
- Add tests for behavior changes in `tests/`.

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <subject>

<body>
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.
Examples:

```text
feat(tasks): add a database migration example
fix(render): keep workspace contracts read-only on re-render
docs: clarify scoring configuration
```

## Pull requests

- Keep each pull request focused on one change.
- Describe the problem, the approach, and how you verified it.
- Link related issues when possible.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
- Make sure CI is green.

## Reporting bugs

Use the GitHub issue templates. For security issues, follow
[`SECURITY.md`](SECURITY.md) instead of opening a public issue.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
