import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from n8n_organizer.cli import main


class CliTests(unittest.TestCase):
    def test_help_lists_both_commands(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("build", out.getvalue())
        self.assertIn("search", out.getvalue())

    def test_search_is_a_clear_stub(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["search", "telegram"])
        self.assertEqual(code, 2)
        self.assertIn("not built yet", err.getvalue())


if __name__ == "__main__":
    unittest.main()


from helpers import DATA_WF, TempDirTest, write_json


class LocationTests(TempDirTest):
    def run_cli(self, *args):
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            code = main(["build", *args, "--log-dir", str(self.tmp / "logs")])
        return code, err.getvalue()

    def setUp(self):
        super().setUp()
        write_json(self.input / "a.json", DATA_WF)

    def test_output_equal_to_input_is_refused(self):
        code, err = self.run_cli("--input", str(self.input), "--output", str(self.input))
        self.assertEqual(code, 2)
        self.assertIn("must not be the input folder", err)

    def test_output_inside_input_is_refused(self):
        code, err = self.run_cli("--input", str(self.input), "--output", str(self.input / "out"))
        self.assertEqual(code, 2)
        self.assertFalse((self.input / "out").exists())

    def test_non_empty_output_is_refused(self):
        self.output.mkdir()
        (self.output / "keep.md").write_text("mine")
        code, err = self.run_cli("--input", str(self.input), "--output", str(self.output))
        self.assertEqual(code, 2)
        self.assertIn("empty", err)
        self.assertEqual([p.name for p in self.output.iterdir()], ["keep.md"])

    def test_missing_input_is_refused(self):
        code, err = self.run_cli("--input", str(self.tmp / "nope"), "--output", str(self.output))
        self.assertEqual(code, 2)
        self.assertIn("input folder not found", err)

    def test_build_succeeds(self):
        code, _ = self.run_cli("--input", str(self.input), "--output", str(self.output))
        self.assertEqual(code, 0)
        self.assertTrue((self.output / "1-Data_Integration.md").exists())
