import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT) if not existing else f"{ROOT}{os.pathsep}{existing}"
    return subprocess.run(
        [sys.executable, "-m", "evalkit", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_list_shows_example_tasks(self):
        result = run_cli("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        for task_id in ("mario-01", "todo-api-01", "bugfix-csv-01"):
            self.assertIn(task_id, result.stdout)

    def test_validate_all(self):
        result = run_cli("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("[OK]"), 3)

    def test_render_check_only(self):
        result = run_cli("render", "--all", "--check-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[ERROR]", result.stderr)

    def test_scaffold_validate_and_render(self):
        with tempfile.TemporaryDirectory() as directory:
            tasks_dir = Path(directory) / "tasks"
            out_dir = Path(directory) / "out"

            result = run_cli(
                "--tasks-dir",
                str(tasks_dir),
                "new",
                "--id",
                "demo-01",
                "--title",
                "Demo task",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((tasks_dir / "demo-01" / "task.toml").is_file())

            result = run_cli("--tasks-dir", str(tasks_dir), "validate", "--task", "demo-01")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("[WARN]", result.stdout)

            result = run_cli(
                "--tasks-dir",
                str(tasks_dir),
                "render",
                "--task",
                "demo-01",
                "--out",
                str(out_dir),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("CONTRACT.md", "executor.md", "evaluator.md", "manifest.json"):
                self.assertTrue((out_dir / "demo-01" / name).is_file(), name)

    def test_unknown_task_fails(self):
        result = run_cli("validate", "--task", "does-not-exist")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[ERROR]", result.stderr)


if __name__ == "__main__":
    unittest.main()
