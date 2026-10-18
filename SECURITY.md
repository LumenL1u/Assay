# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a Vulnerability

Please **do not** open a public issue for security problems.

Report vulnerabilities privately to <lumenliu.codes@gmail.com>. Include:

- A description of the issue and its impact.
- Steps to reproduce, including the task definition or command involved.
- The affected version or commit.
- Any suggested mitigation.

You can expect an acknowledgement within 5 business days and a status update
within 10 business days. Please allow time for a fix before public disclosure.

## Scope

This project renders prompts and task definitions; it does not execute agent
code or run a sandbox. Security-relevant issues include, but are not limited to:

- Path traversal or unintended file writes during `render`.
- Template injection through task definitions.
- Accidental exposure of secrets in rendered prompts or manifests.
- Dependency vulnerabilities in optional tooling.

## Handling untrusted tasks

Task definitions and starter workspaces are treated as untrusted input when they
come from third parties. Review task files before rendering or executing them.
The framework does not sandbox the executor or evaluator agents; isolation is
the responsibility of the surrounding orchestration environment.
