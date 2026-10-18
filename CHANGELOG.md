# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-18

### Added

- Task-driven evaluation framework built around `tasks/<id>/task.toml`.
- Generic contract, executor, and evaluator prompt templates.
- `evalkit` CLI with `list`, `validate`, `render`, `info`, and `new` commands.
- Configurable scoring: weighted or arithmetic mean, custom grade bands, and
  integrity-failure zeroing.
- Read-only `CONTRACT.md` synchronization into each task workspace.
- Example tasks covering web-game replication (`mario-01`), backend API
  implementation (`todo-api-01`), and bug fixing (`bugfix-csv-01`).
- Unit and CLI integration tests.
- Task schema reference, architecture notes, and community documentation.
- GitHub Actions CI, Dependabot, and issue/PR templates.

### Changed

- Replaced the original Mario-specific prompt renderer with a general task
  definition schema and renderer.
- Moved task assets, references, and workspaces from the repository root into
  per-task directories.
