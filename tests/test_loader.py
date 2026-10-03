import os
import unittest
from pathlib import Path
from unittest import mock

from n8n_organizer import loader

from helpers import DATA_WF, TempDirTest, write_json

REAL_SCANDIR = os.scandir


class reversed_scandir:
    """Like os.scandir, but lists entries in reverse order, as some file systems do."""

    def __init__(self, path):
        with REAL_SCANDIR(path) as it:
            self.entries = list(it)[::-1]

    def __enter__(self):
        return iter(self.entries)

    def __exit__(self, *exc):
        return False


class OrderTests(TempDirTest):
    def test_files_come_in_sorted_path_order_whatever_the_file_system_order(self):
        for folder in ("a", "b", "c", "b/x"):
            for name in ("1.json", "2.json"):
                write_json(self.input / folder / name, DATA_WF)
        write_json(self.input / "z.json", DATA_WF)
        with mock.patch.object(loader.os, "scandir", reversed_scandir):
            found = [p.relative_to(self.input).as_posix() for p in loader.iter_workflow_files(self.input)]
        # A folder's files first, then its subfolders in order: the order os.walk gave.
        expected = ["z.json", "a/1.json", "a/2.json", "b/1.json", "b/2.json", "b/x/1.json", "b/x/2.json", "c/1.json", "c/2.json"]
        self.assertEqual(found, expected)
        walked = [
            (Path(root) / name).relative_to(self.input).as_posix()
            for root, dirs, files in os.walk(self.input)
            if not dirs.sort()
            for name in sorted(files)
        ]
        self.assertEqual(walked, expected)


if __name__ == "__main__":
    unittest.main()
