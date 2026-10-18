import tempfile
import unittest
from pathlib import Path

from evalkit.render import render_task, render_text
from evalkit.scaffold import create_task
from evalkit.task import TaskError, load_task, validate_task
from evalkit.variables import build_variables

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
TEMPLATES = ROOT / "evalkit" / "templates"
EXAMPLES = ("mario-01", "todo-api-01", "bugfix-csv-01")


class RenderTextTests(unittest.TestCase):
    def test_substitutes_variables(self):
        self.assertEqual(
            render_text("hello {{NAME}}", {"NAME": "world"}, Path("t.md")),
            "hello world",
        )

    def test_missing_variable_raises(self):
        with self.assertRaises(TaskError):
            render_text("{{MISSING}}", {}, Path("t.md"))

    def test_collapses_extra_blank_lines(self):
        self.assertEqual(render_text("a\n\n\n\nb", {}, Path("t.md")), "a\n\nb")


class TaskLoadingTests(unittest.TestCase):
    def test_load_all_examples(self):
        for name in EXAMPLES:
            with self.subTest(task=name):
                task = load_task(TASKS / name)
                self.assertEqual(task.id, name)
                self.assertTrue(task.requirements)
                self.assertTrue(task.rubric)

    def test_examples_have_no_structural_warnings(self):
        for name in EXAMPLES:
            with self.subTest(task=name):
                self.assertEqual(validate_task(load_task(TASKS / name)), [])

    def test_mario_variables(self):
        task = load_task(TASKS / "mario-01")
        variables = build_variables(task, Path("/tmp/agent-eval-out"))
        self.assertIn("Super Mario", variables["OBJECTIVE"])
        self.assertIn("R1", variables["REQUIREMENTS_BLOCK"])
        self.assertIn("Σ", variables["SCORING_RULE"])
        self.assertIn("优秀", variables["SCORING_RULE"])
        self.assertEqual(
            variables["CONTRACT_PATH"],
            str((TASKS / "mario-01" / "workspace" / "CONTRACT.md").resolve()),
        )

    def test_task_without_url_gets_generic_steps(self):
        task = load_task(TASKS / "bugfix-csv-01")
        variables = build_variables(task, Path("/tmp/agent-eval-out"))
        self.assertEqual(variables["URL_LINE"], "")
        self.assertIn("python3 -m unittest", variables["TEST_STEP"])
        self.assertIn("python3 -m csvstats.cli", variables["RUNTIME_STEP"])

    def test_missing_objective_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            task_dir = Path(directory) / "bad-01"
            task_dir.mkdir()
            (task_dir / "task.toml").write_text(
                'schema_version = 1\nid = "bad-01"\ntitle = "Bad"\n[[rubric]]\nname = "x"\n',
                encoding="utf-8",
            )
            with self.assertRaises(TaskError):
                load_task(task_dir)


class RenderTaskTests(unittest.TestCase):
    def test_render_to_temp_directory(self):
        task = load_task(TASKS / "mario-01")
        with tempfile.TemporaryDirectory() as directory:
            result = render_task(
                task,
                TEMPLATES,
                Path(directory),
                write_contract_in_workspace=False,
            )
            self.assertEqual(set(result.rendered), {"CONTRACT.md", "executor.md", "evaluator.md"})
            for name in (*result.rendered, "manifest.json"):
                self.assertTrue((Path(directory) / name).is_file(), name)

            contract = (Path(directory) / "CONTRACT.md").read_text(encoding="utf-8")
            self.assertIn("Super Mario", contract)
            self.assertNotIn("{{", contract)
            self.assertEqual(
                (Path(directory) / "CONTRACT.md").stat().st_mode & 0o777,
                0o444,
            )

    def test_check_only_writes_nothing(self):
        task = load_task(TASKS / "todo-api-01")
        with tempfile.TemporaryDirectory() as directory:
            result = render_task(
                task,
                TEMPLATES,
                Path(directory),
                check_only=True,
            )
            self.assertTrue(result.check_only)
            self.assertEqual(list(Path(directory).iterdir()), [])


class ScaffoldTests(unittest.TestCase):
    def test_create_and_load_task(self):
        with tempfile.TemporaryDirectory() as directory:
            target = create_task(Path(directory), "demo-01", "演示任务")
            task = load_task(target)
            self.assertEqual(task.id, "demo-01")
            self.assertEqual(task.title, "演示任务")
            self.assertTrue(any("TODO" in item for item in validate_task(task)))

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            create_task(Path(directory), "demo-01")
            with self.assertRaises(TaskError):
                create_task(Path(directory), "demo-01")


if __name__ == "__main__":
    unittest.main()
