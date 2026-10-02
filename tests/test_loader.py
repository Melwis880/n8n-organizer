import os
import unittest
from unittest import mock

from n8n_organizer import loader

from helpers import DATA_WF, TempDirTest, write_json

REAL_WALK = os.walk


def reversed_walk(top, **kwargs):
    """Like os.walk, but lists folders and files in reverse order, as some file systems do."""
    for root, dirs, files in REAL_WALK(top, **kwargs):
        dirs.reverse()
        files.reverse()
        yield root, dirs, files


class OrderTests(TempDirTest):
    def test_files_come_in_sorted_path_order_whatever_the_file_system_order(self):
        for folder in ("a", "b", "c"):
            for name in ("1.json", "2.json"):
                write_json(self.input / folder / name, DATA_WF)
        with mock.patch.object(loader.os, "walk", reversed_walk):
            found = [p.relative_to(self.input).as_posix() for p in loader.iter_workflow_files(self.input)]
        self.assertEqual(found, ["a/1.json", "a/2.json", "b/1.json", "b/2.json", "c/1.json", "c/2.json"])


if __name__ == "__main__":
    unittest.main()
