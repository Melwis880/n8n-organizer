import unittest

from n8n_organizer.utils import clean_text


class CleanTextTests(unittest.TestCase):
    def test_whitespace_and_control_characters_collapse_to_single_spaces(self):
        self.assertEqual(clean_text("  a\tb\n\nc   d e\x00f  "), "a b c d e f")

    def test_bidi_and_zero_width_removed(self):
        self.assertEqual(clean_text("abc\u202Edef​ghi"), "abc def ghi")

    def test_long_text_truncated(self):
        out = clean_text("word " * 100, max_len=20)
        self.assertEqual(len(out), 20)
        self.assertTrue(out.endswith("..."))

    def test_non_strings(self):
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(42), "42")
        self.assertEqual(clean_text(["a", "b"]), "['a', 'b']")


if __name__ == "__main__":
    unittest.main()
