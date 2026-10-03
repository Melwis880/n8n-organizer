import unittest

import tempfile
from pathlib import Path

from n8n_organizer.utils import clean_name, clean_text, md_text, write_new_file


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


class CleanNameTests(unittest.TestCase):
    def test_urls_and_email_addresses_are_removed(self):
        self.assertEqual(clean_name("GET https://api.example/v1?key=K1 now"), "GET (link removed) now")
        self.assertEqual(clean_name("see WWW.example.org/a"), "see (link removed)")
        self.assertEqual(clean_name("ftp://h/x and s3://bucket/key"), "(link removed) and (link removed)")
        self.assertEqual(clean_name("mail ops+alerts@corp.example."), "mail (link removed).")
        self.assertEqual(clean_name("a_www.x.example b_https://y.example"), "a_(link removed) b_(link removed)")

    def test_closing_punctuation_stays(self):
        self.assertEqual(clean_name("Fetch (https://x.example/a)."), "Fetch ((link removed)).")
        self.assertEqual(clean_name("[a](https://x.example)"), "[a]((link removed))")

    def test_a_zero_width_character_cannot_hide_a_link(self):
        self.assertEqual(clean_name("ht\u200btps://hidden.example/T"), "ht (link removed)")
        self.assertEqual(clean_name("GET https://x.example/TO\u200bKEN\x00X end"), "GET (link removed) end")
        # Split by a space, it is no longer a link; a bare host name is kept like any dotted word.
        self.assertEqual(clean_name("www\u200b.hidden.example"), "www .hidden.example")

    def test_ordinary_names_are_kept(self):
        for name in ("Node.js v1.2 (step 3).", "Q&A: a > b", "@n8n/n8n-nodes-langchain.agent", "Café 📄", "x@y", "e-mail me"):
            self.assertEqual(clean_name(name), name)

    def test_truncated_after_removal(self):
        self.assertEqual(len(clean_name("https://x.example/" + "a" * 50 + " " + "b" * 300)), 200)


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
