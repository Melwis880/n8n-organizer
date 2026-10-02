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
