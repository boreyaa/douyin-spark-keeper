import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from douyin_spark import messages, snapshot
from douyin_spark import state as st


class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_add_remove(self):
        s = st.empty_state()
        self.assertEqual(s["contacts"], [])
        self.assertTrue(st.add_contact(s, "测试甲", 93, "彩色"))
        self.assertFalse(st.add_contact(s, "测试甲", 1, "彩色"))
        self.assertTrue(st.remove_contact(s, "测试甲"))
        self.assertFalse(st.remove_contact(s, "测试甲"))

    def test_roll_day_resets_sent(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲")
        st.roll_day(s, "2026-11-01")
        self.assertTrue(st.mark_sent(s, "测试甲", "早"))
        self.assertEqual(s["sent_today"], ["测试甲"])
        st.roll_day(s, "2026-11-02")
        self.assertEqual(s["sent_today"], [])

    def test_mark_does_not_change_days(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲", 93, "彩色")
        st.roll_day(s, "2026-11-03")
        self.assertTrue(st.mark_sent(s, "测试甲", "早"))
        self.assertFalse(st.mark_sent(s, "测试甲", "早"))
        self.assertEqual(st.find_contact(s, "测试甲")["spark_days"], 93)

    def test_pending_excludes_sent(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲")
        st.add_contact(s, "测试乙")
        st.roll_day(s, "2026-11-03")
        st.mark_sent(s, "测试甲", "早")
        self.assertEqual([c["name"] for c in st.pending(s)], ["测试乙"])

    def test_pick_message_avoids_last_text(self):
        s = st.empty_state()
        s["last_text"] = messages.DEFAULT_TEMPLATES[0]
        s["template_index"] = 0
        self.assertNotEqual(messages.pick_message(s, messages.DEFAULT_TEMPLATES), s["last_text"])

    def test_update_contact(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲", 10, "重燃中", "1/3")
        self.assertTrue(st.update_contact(s, "测试甲", days=11, status="彩色", progress="3/3"))
        c = st.find_contact(s, "测试甲")
        self.assertEqual((c["spark_days"], c["status"], c["reignite_progress"]), (11, "彩色", "3/3"))

    def test_snapshot_validate(self):
        self.assertTrue(snapshot.validate(snapshot.example())[0])
        self.assertFalse(snapshot.validate({"conversations": [{"name": ""}]})[0])
        self.assertFalse(snapshot.validate({"conversations": [{"name": "甲", "status": "未知"}]})[0])
        self.assertFalse(snapshot.validate({"items": []})[0])

    def test_apply_snapshot_adds_and_updates(self):
        s = st.empty_state()
        st.add_contact(s, "好友甲", 90, "彩色")
        st.roll_day(s, "2026-11-03")
        added, updated = st.apply_snapshot(s, snapshot.example())
        self.assertEqual((added, updated), (1, 1))
        self.assertEqual(st.find_contact(s, "好友甲")["spark_days"], 93)
        self.assertEqual(len(s["snapshots"]), 1)

    def test_circuit_breaker_trips(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲")
        st.add_contact(s, "测试乙")
        st.roll_day(s, "2026-11-03")
        self.assertFalse(st.is_tripped(s))
        self.assertTrue(st.mark_failed(s, "测试甲", "页面未找到"))
        self.assertFalse(st.mark_failed(s, "测试甲", "页面未找到"))
        self.assertFalse(st.is_tripped(s))
        self.assertTrue(st.mark_failed(s, "测试乙", "发送超时"))
        self.assertTrue(st.is_tripped(s))
        st.roll_day(s, "2026-11-04")
        self.assertFalse(st.is_tripped(s))

    def test_digest_contains_metrics(self):
        s = st.empty_state()
        st.add_contact(s, "测试甲", 93, "彩色")
        st.roll_day(s, "2026-11-03")
        text = st.build_digest(s)
        self.assertIn("续火花日报 2026-11-03", text)
        self.assertIn("今日待发", text)
        self.assertIn("测试甲", text)

    def test_cli_end_to_end(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT)

        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "douyin_spark", "--state", str(self.path), *args],
                cwd=str(ROOT), env=env, capture_output=True, text=True,
            )

        r = run("add", "测试甲", "--days", "93", "--status", "彩色")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("add", "测试乙", "--days", "2", "--status", "重燃中", "--progress", "2/3")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("plan")
        self.assertIn("测试甲", r.stdout)
        self.assertIn("测试乙", r.stdout)
        r = run("next")
        self.assertTrue(r.stdout.strip())
        r = run("mark", "测试甲", "--text", "早呀")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("status")
        self.assertIn("已发送：1 / 2", r.stdout)
        r = run("report")
        self.assertIn("已发", r.stdout)
        r = run("list")
        self.assertIn("测试乙", r.stdout)

        snap = Path(self.tmp.name) / "snapshot.json"
        snap.write_text(json.dumps({
            "version": 1,
            "captured_at": "2026-11-03T21:00:00",
            "conversations": [
                {"name": "测试甲", "spark_days": 94, "status": "彩色", "reignite_progress": ""},
                {"name": "测试丙", "spark_days": 5, "status": "灰色", "reignite_progress": ""},
            ],
        }), encoding="utf-8")
        r = run("snapshot", "--file", str(snap))
        self.assertIn("快照校验通过", r.stdout)
        r = run("snapshot", "--file", str(snap), "--apply")
        self.assertIn("已导入", r.stdout)
        r = run("fail", "测试乙", "--reason", "页面未找到")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("digest", "--out", str(Path(self.tmp.name) / "digest.md"))
        self.assertIn("续火花日报", r.stdout)
        self.assertTrue((Path(self.tmp.name) / "digest.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
