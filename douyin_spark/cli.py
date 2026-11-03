import argparse
import json
from pathlib import Path

from . import messages, snapshot
from . import state as st

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "config" / "state.json"
DEFAULT_TEMPLATES = ROOT / "config" / "messages.json"
DEFAULT_REPORT_DIR = ROOT / "reports"


def build_parser():
    parser = argparse.ArgumentParser(prog="douyin-spark", description="抖音火花联系人与每日续火花状态管理")
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--templates", default=str(DEFAULT_TEMPLATES))
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出联系人清单")
    sub.add_parser("plan", help="列出今日待发联系人")
    p_next = sub.add_parser("next", help="输出本次建议发送的消息")
    p_next.add_argument("--text", default="", help="固定发送这一条内容，例如 [比心]")
    sub.add_parser("status", help="显示今日运行状态")
    sub.add_parser("report", help="输出可汇报的发送结果表格")
    sub.add_parser("dump", help="输出完整状态 JSON")

    p_add = sub.add_parser("add", help="添加联系人")
    p_add.add_argument("name")
    p_add.add_argument("--days", type=int, default=0)
    p_add.add_argument("--status", default="未标注", choices=list(st.STATUS_VALUES))
    p_add.add_argument("--progress", default="")

    p_remove = sub.add_parser("remove", help="移除联系人")
    p_remove.add_argument("name")

    p_set = sub.add_parser("set", help="按页面实际读数更新联系人")
    p_set.add_argument("name")
    p_set.add_argument("--days", type=int, default=None)
    p_set.add_argument("--status", default=None, choices=list(st.STATUS_VALUES))
    p_set.add_argument("--progress", default=None)

    p_mark = sub.add_parser("mark", help="记录今日已发送")
    p_mark.add_argument("name")
    p_mark.add_argument("--text", default="")

    p_fail = sub.add_parser("fail", help="记录一次发送失败")
    p_fail.add_argument("name")
    p_fail.add_argument("--reason", default="")

    p_snapshot = sub.add_parser("snapshot", help="校验或导入会话快照")
    p_snapshot.add_argument("--file", required=True)
    p_snapshot.add_argument("--apply", action="store_true")

    p_digest = sub.add_parser("digest", help="生成每日 Markdown 日报")
    p_digest.add_argument("--out", default=None)

    return parser


def load_templates(path):
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        pool = data.get("templates", [])
        if pool:
            return [str(x) for x in pool]
    return messages.DEFAULT_TEMPLATES


def render_table(rows, headers):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    head = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    lines = [head, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |")
    return "\n".join(lines)


def main(argv=None):
    args = build_parser().parse_args(argv)
    state = st.load_state(args.state)
    changed = False
    cmd = args.command

    if cmd == "add":
        ok = st.add_contact(state, args.name, args.days, args.status, args.progress)
        print("已添加联系人：" + args.name if ok else "联系人已存在：" + args.name)
        changed = ok
    elif cmd == "remove":
        ok = st.remove_contact(state, args.name)
        print("已移除联系人：" + args.name if ok else "未找到联系人：" + args.name)
        changed = ok
    elif cmd == "set":
        ok = st.update_contact(state, args.name, args.days, args.status, args.progress)
        print("已更新读数：" + args.name if ok else "未找到联系人或状态取值不合法：" + args.name)
        changed = ok
    elif cmd == "mark":
        st.roll_day(state)
        ok = st.mark_sent(state, args.name, args.text)
        print("已记录今日发送：" + args.name if ok else "今日已发送或未找到联系人：" + args.name)
        changed = ok
    elif cmd == "fail":
        st.roll_day(state)
        ok = st.mark_failed(state, args.name, args.reason)
        print("已记录失败：" + args.name if ok else "今日已记录或未找到联系人：" + args.name)
        changed = ok
    elif cmd == "snapshot":
        data = snapshot.load(args.file)
        ok, message = snapshot.validate(data)
        if not ok:
            print("快照校验失败：" + message)
            return 2
        print("快照校验通过：" + str(len(snapshot.conversations(data))) + " 个会话")
        if args.apply:
            st.roll_day(state)
            added, updated = st.apply_snapshot(state, data)
            print("已导入：新增 " + str(added) + "，更新 " + str(updated))
            changed = True
        else:
            print("未写入状态，追加 --apply 才会生效")
    elif cmd == "digest":
        st.roll_day(state)
        text = st.build_digest(state)
        out = Path(args.out) if args.out else DEFAULT_REPORT_DIR / (state["last_date"] + ".md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text)
        print("日报已写入：" + str(out))
        changed = True
    elif cmd == "next":
        st.roll_day(state)
        fixed = (getattr(args, "text", "") or "").strip()
        if fixed:
            print(fixed)
        else:
            print(messages.pick_message(state, load_templates(args.templates)))
        changed = True
    elif cmd == "plan":
        st.roll_day(state)
        if st.is_tripped(state):
            print("已熔断：今日失败 " + str(len(state["failures_today"])) + " 次，达到阈值 " + str(state["failure_threshold"]) + "，停止发送。")
            print(render_table([], ["联系人", "火花天数", "状态", "重燃进度"]))
        else:
            rows = [[c["name"], c["spark_days"], c["status"], c["reignite_progress"]] for c in st.pending(state)]
            print(render_table(rows, ["联系人", "火花天数", "状态", "重燃进度"]))
        changed = True
    elif cmd == "list":
        rows = [[c["name"], c["spark_days"], c["status"], c["reignite_progress"]] for c in state["contacts"]]
        print(render_table(rows, ["联系人", "火花天数", "状态", "重燃进度"]))
    elif cmd == "status":
        st.roll_day(state)
        print("日期：" + state["last_date"])
        print("已发送：" + str(len(state["sent_today"])) + " / " + str(len(state["contacts"])))
        print("待发送：" + str(len(st.pending(state))))
        print("今日失败：" + str(len(state["failures_today"])))
        print("熔断状态：" + ("已触发" if st.is_tripped(state) else "未触发"))
        print("上一条消息：" + (state["last_text"] or "无"))
        changed = True
    elif cmd == "report":
        rows = []
        for c in state["contacts"]:
            flag = "已发" if c["name"] in state["sent_today"] else "待发"
            rows.append([c["name"], c["spark_days"], c["status"], c["reignite_progress"], flag])
        print(render_table(rows, ["联系人", "火花天数", "状态", "重燃进度", "今日"]))
    elif cmd == "dump":
        print(json.dumps(state, ensure_ascii=False, indent=2))

    if changed:
        st.save_state(args.state, state)
    return 0
