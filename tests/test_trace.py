import io
import json
import os
import stat
import unittest
from collections import defaultdict

from n8n_organizer.main import run
from n8n_organizer.trace import Tracer

from helpers import AI_WF, DATA_WF, TempDirTest, write_json


class TraceTests(TempDirTest):
    def events(self, tracer):
        return [json.loads(line) for line in tracer.path.read_text().splitlines()]

    def test_event_chain_per_file(self):
        write_json(self.input / "a.json", AI_WF)
        write_json(self.input / "b.json", AI_WF)
        write_json(self.input / "c.json", ["not", "a", "workflow"])
        tracer = Tracer(self.tmp / "logs")
        run(self.input, self.output, tracer=tracer)
        events = self.events(tracer)

        self.assertEqual(events[0]["event"], "run_start")
        self.assertEqual(events[-1]["event"], "run_end")
        self.assertEqual([e["seq"] for e in events], list(range(1, len(events) + 1)))
        self.assertEqual({e["run_id"] for e in events}, {tracer.run_id})

        chain = defaultdict(list)
        for e in events:
            if "path" in e:
                chain[e["path"]].append(e["event"])
        self.assertEqual(chain["a.json"], ["found", "loaded", "classified", "placed"])
        self.assertEqual(chain["b.json"], ["found", "loaded", "classified", "duplicate"])
        self.assertEqual(chain["c.json"], ["found", "skipped"])

    def test_no_workflow_content_in_trace(self):
        write_json(self.input / "a.json", AI_WF)
        tracer = Tracer(self.tmp / "logs")
        run(self.input, self.output, tracer=tracer)
        text = tracer.path.read_text()
        self.assertNotIn("langchain.agent", text)
        self.assertNotIn("parameters", text)

    def test_debug_mirrors_to_stream(self):
        write_json(self.input / "a.json", DATA_WF)
        stream = io.StringIO()
        tracer = Tracer(self.tmp / "logs", debug=True, stream=stream)
        run(self.input, self.output, tracer=tracer)
        self.assertEqual(stream.getvalue().splitlines(), tracer.path.read_text().splitlines())

    def test_each_event_is_on_disk_as_soon_as_it_is_written(self):
        tracer = Tracer(self.tmp / "logs")
        tracer.event("found", path="a.json")
        self.assertEqual(self.events(tracer)[0]["path"], "a.json")
        tracer.close()

    def test_file_is_closed_after_a_run_and_reopened_by_the_next(self):
        write_json(self.input / "a.json", DATA_WF)
        tracer = Tracer(self.tmp / "logs")
        run(self.input, self.output, tracer=tracer)
        self.assertIsNone(tracer._file)
        run(self.input, self.tmp / "output2", tracer=tracer)
        self.assertIsNone(tracer._file)
        events = self.events(tracer)
        self.assertEqual([e["event"] for e in events].count("run_end"), 2)
        self.assertEqual([e["seq"] for e in events], list(range(1, len(events) + 1)))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores permissions")
    def test_unwritable_log_dir_warns_once_and_run_continues(self):
        blocked = self.tmp / "blocked"
        blocked.write_text("a file, not a folder")
        write_json(self.input / "a.json", DATA_WF)
        stream = io.StringIO()
        result = run(self.input, self.output, tracer=Tracer(blocked / "logs", stream=stream))
        self.assertEqual(result.analysed, 1)
        self.assertEqual(stream.getvalue().count("cannot write trace"), 1)


class TraceFileSafetyTests(TempDirTest):
    @unittest.skipUnless(hasattr(os, "symlink") and hasattr(os, "O_NOFOLLOW"), "no symlinks or O_NOFOLLOW")
    def test_symlink_at_the_trace_path_is_not_followed(self):
        target = self.tmp / "victim.txt"
        target.write_text("keep me")
        tracer = Tracer(self.tmp / "logs", stream=io.StringIO())
        tracer.path.parent.mkdir()
        os.symlink(target, tracer.path)
        write_json(self.input / "a.json", DATA_WF)
        result = run(self.input, self.output, tracer=tracer)
        self.assertEqual(result.analysed, 1)
        self.assertEqual(target.read_text(), "keep me")
        self.assertEqual(tracer.stream.getvalue().count("cannot write trace"), 1)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no FIFOs")
    def test_fifo_at_the_trace_path_does_not_block_the_run(self):
        tracer = Tracer(self.tmp / "logs", stream=io.StringIO())
        tracer.path.parent.mkdir()
        os.mkfifo(tracer.path)
        write_json(self.input / "a.json", DATA_WF)
        self.assertEqual(run(self.input, self.output, tracer=tracer).analysed, 1)
        self.assertEqual(tracer.stream.getvalue().count("cannot write trace"), 1)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "no FIFOs")
    def test_fifo_with_a_reader_at_the_trace_path_is_not_written(self):
        tracer = Tracer(self.tmp / "logs", stream=io.StringIO())
        tracer.path.parent.mkdir()
        os.mkfifo(tracer.path)
        reader = os.open(tracer.path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            write_json(self.input / "a.json", DATA_WF)
            self.assertEqual(run(self.input, self.output, tracer=tracer).analysed, 1)
            try:
                data = os.read(reader, 1)  # b"" once no writer is left
            except BlockingIOError:
                data = b""
            self.assertEqual(data, b"")  # nothing was written to the pipe
        finally:
            os.close(reader)
        self.assertEqual(tracer.stream.getvalue().count("cannot write trace"), 1)

    @unittest.skipUnless(os.name == "posix", "POSIX permissions")
    def test_new_trace_file_is_readable_by_its_owner_only(self):
        tracer = Tracer(self.tmp / "logs")
        tracer.event("found", path="a.json")
        tracer.close()
        self.assertEqual(stat.S_IMODE(tracer.path.stat().st_mode) & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
