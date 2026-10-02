import unittest

import tempfile
from pathlib import Path

from n8n_organizer.utils import clean_text, md_text, write_new_file


class CleanTextTests(unittest.TestCase):
    def test_whitespace_and_control_characters_collapse_to_single_spaces(self):
        self.assertEqual(clean_text("  a\tb\n\nc   d e\x00f  "), "a b c d e f")

    def test_bidi_and_zero_width_removed(self):
        self.assertEqual(clean_text("abc\u202Edef​ghi"), "abc def ghi")

    def test_long_text_truncated(self):
        out = clean_text("word " * 100, max_len=20)
        self.assertEqual(len(out), 20)
        self.assertTrue(out.endswith("..."))

    def test_lone_surrogates_removed(self):
        self.assertEqual(clean_text("a\udcffb"), "a b")

    def test_every_unsafe_category_is_replaced_and_printable_text_is_kept(self):
        # Cc, Cf (zero width, bidi), Zl, Zp, Cs: each is non-printable, so the fast path never skips one.
        self.assertEqual(clean_text("a\x07b​c‮d e f\ud800g"), "a b c d e f g")
        self.assertEqual(clean_text("a\x07b\x7fc"), "a b c")  # all ASCII: no shortcut for ASCII text
        self.assertEqual(clean_text("Café 📄 Ünal: Q&A > 1000"), "Café 📄 Ünal: Q&A > 1000")

    def test_non_strings(self):
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(42), "42")
        self.assertEqual(clean_text(["a", "b"]), "['a', 'b']")


class MdTextTests(unittest.TestCase):
    def test_link_image_html_and_code_characters_are_escaped(self):
        self.assertEqual(md_text("![i](u) <b> `c` \\"), "!\\[i\\](u) \\<b> \\`c\\` \\\\")

    def test_ordinary_text_is_unchanged(self):
        self.assertEqual(md_text("If Amount > 1000 & get_orders -> Sheet*"), "If Amount > 1000 & get_orders -> Sheet*")


class WriteNewFileTests(unittest.TestCase):
    def test_existing_file_or_symlink_is_never_written_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target.txt"
            target.write_text("keep")
            with self.assertRaises(FileExistsError):
                write_new_file(target, "new")
            link = Path(tmp) / "link.txt"
            link.symlink_to(Path(tmp) / "missing.txt")
            with self.assertRaises(FileExistsError):
                write_new_file(link, "new")
            self.assertFalse((Path(tmp) / "missing.txt").exists())
            self.assertEqual(target.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
