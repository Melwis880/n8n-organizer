import unittest

import hashlib
import os
import stat
import tempfile
import time
from pathlib import Path

from n8n_organizer.utils import LINK_PLACEHOLDER, _LINKISH, clean_name, clean_text, md_text, sha256_text, write_new_file


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
        self.assertEqual(clean_name("see WWW.example.org"), "see (link removed)")  # no "/" or "@"
        self.assertEqual(clean_name("ftp://h/x and s3://bucket/key"), "(link removed) and (link removed)")
        self.assertEqual(clean_name("mail ops+alerts@corp.example."), "mail (link removed).")
        self.assertEqual(clean_name("a_www.x.example b_https://y.example"), "a_(link removed) b_(link removed)")
        self.assertEqual(clean_name("1https://x.example 2-ftp://y.example"), "1(link removed) 2-(link removed)")
        self.assertEqual(clean_name("x" * 40 + "https://z.example"), "x" * 13 + "(link removed)")  # scheme: 32 at most

    def test_host_names_with_a_path_are_removed(self):
        self.assertEqual(clean_name("Open bit.ly/abc and evil.example/login now"), "Open (link removed) and (link removed) now")
        self.assertEqual(clean_name("Go to sub.evil.example/a?key=K1."), "Go to (link removed).")
        self.assertEqual(clean_name("@horka.tv/n8n-nodes-kv.store"), "@(link removed)")
        # A host or file name alone is kept, and so is a path whose dotted part ends in a digit.
        for name in ("Open evil.example now", "Read data.csv", "Split 1.0/2.0", "Input/Output", "n8n-nodes-base.set"):
            self.assertEqual(clean_name(name), name)

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

    def test_long_names_take_linear_time(self):
        # A raw name can be millions of characters long. Tried from every position of a long run,
        # the pattern took quadratic time: 40,000 letters took 31 s, 200,000 would take minutes.
        start = time.perf_counter()
        for name in ("a" * 200_000, "a." * 100_000, "ab+." * 50_000, ("b" * 50 + "@") * 4_000, "www." + "." * 200_000,
                     "a.bc" * 100_000, "ab." * 100_000 + "ab", ("ab.cd" * 1_000 + " ") * 100, "a-" * 200_000):
            clean_name(name)
        self.assertLess(time.perf_counter() - start, 5)

    def test_link_pattern_is_linear_without_the_scan_limit(self):
        # clean_name scans 4,096 characters, which hides a quadratic pattern; the pattern itself
        # must stay linear. A host name starts only where its run starts: tried after every dot,
        # 20,000 characters took 4 s.
        start = time.perf_counter()
        for text in ("a.bc" * 5_000, "ab." * 7_000 + "ab", "a" * 20_000, ("b" * 50 + "@") * 400):
            _LINKISH.sub(LINK_PLACEHOLDER, text)
        self.assertLess(time.perf_counter() - start, 1)

    def test_only_the_start_of_a_huge_name_is_scanned(self):
        start = time.perf_counter()
        self.assertEqual(clean_name("a" * 10_000_000), "a" * 197 + "...")
        self.assertLess(time.perf_counter() - start, 1)
        self.assertEqual(clean_name("https://x.example/" + "a" * 10_000), "(link removed)")

    def test_truncated_after_removal(self):
        self.assertEqual(len(clean_name("https://x.example/" + "a" * 50 + " " + "b" * 300)), 200)


class MdTextTests(unittest.TestCase):
    def test_link_image_html_and_code_characters_are_escaped(self):
        self.assertEqual(md_text("![i](u) <b> `c` \\"), "!\\[i\\](u) \\<b> \\`c\\` \\\\")

    def test_ordinary_text_is_unchanged(self):
        self.assertEqual(md_text("If Amount > 1000 & get_orders -> Sheet*"), "If Amount > 1000 & get_orders -> Sheet*")


class Sha256TextTests(unittest.TestCase):
    def test_lone_surrogate_is_hashed_and_other_text_is_unchanged(self):
        self.assertRegex(sha256_text("a\ud83d"), r"^[0-9a-f]{64}$")
        self.assertNotEqual(sha256_text("a\ud83d"), sha256_text("a\ud83e"))
        self.assertEqual(sha256_text("Café 📄"), hashlib.sha256("Café 📄".encode("utf-8")).hexdigest())


class WriteNewFileTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX permissions")
    def test_new_file_is_readable_by_its_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            write_new_file(path, "x\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "x\n")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0)

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
