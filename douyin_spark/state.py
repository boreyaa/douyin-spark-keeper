import json
from datetime import date
from pathlib import Path

SCHEMA_VERSION = 2
STATUS_VALUES = ("彩色", "灰色", "重燃中", "未标注")
DEFAULT_FAILURE_THRESHOLD = 2


def empty_state():
    return {
        "version": SCHEMA_VERSION,
        "last_date": "",
        "sent_today": [],
        "failures_today": [],
        "failure_threshold": DEFAULT_FAILURE_THRESHOLD,
        "last_text": "",
        "template_index": 0,
        "contacts": [],
        "history": [],
        "snapshots": [],
    }


def load_state(path):
    p = Path(path)
    if not p.exists():
        return empty_state()
    with p.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    for key, value in empty_state().items():
        data.setdefault(key, value)
    return data


def save_state(path, state):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def roll_day(state, today=None):
    day = today or date.today().isoformat()
    if state["last_date"] != day:
        state["last_date"] = day
        state["sent_today"] = []
        state["failures_today"] = []
    return state


def find_contact(state, name):
    for item in state["contacts"]:
        if item.get("name") == name:
            return item
    return None


def add_contact(state, name, days=0, status="未标注", progress=""):
    if find_contact(state, name) is not None:
        return False
    state["contacts"].append({
        "name": name,
        "spark_days": int(days),
        "status": status if status in STATUS_VALUES else "未标注",
        "reignite_progress": progress,
        "note": "",
    })
    return True


def remove_contact(state, name):
    before = len(state["contacts"])
    state["contacts"] = [c for c in state["contacts"] if c.get("name") != name]
    return len(state["contacts"]) != before


def update_contact(state, name, days=None, status=None, progress=None):
    c = find_contact(state, name)
    if c is None:
        return False
    if status is not None and status not in STATUS_VALUES:
        return False
    if days is not None:
        c["spark_days"] = int(days)
    if status is not None:
        c["status"] = status
    if progress is not None:
        c["reignite_progress"] = progress
    return True


def pending(state):
    return [c for c in state["contacts"] if c.get("name") not in state["sent_today"]]


def mark_sent(state, name, text=""):
    if find_contact(state, name) is None:
        return False
    if name in state["sent_today"]:
        return False
    state["sent_today"].append(name)
    if text:
        state["last_text"] = text
    state["history"].append({
        "date": state["last_date"],
        "name": name,
        "text": text,
        "result": "sent",
    })
    return True


def mark_failed(state, name, reason=""):
    if find_contact(state, name) is None:
        return False
    for item in state["failures_today"]:
        if item.get("name") == name:
            return False
    state["failures_today"].append({"name": name, "reason": reason})
    state["history"].append({
        "date": state["last_date"],
        "name": name,
        "text": "",
        "result": "failed",
        "reason": reason,
    })
    return True


def is_tripped(state):
    threshold = int(state.get("failure_threshold", DEFAULT_FAILURE_THRESHOLD))
    return len(state.get("failures_today", [])) >= threshold


def apply_snapshot(state, data):
    added = 0
    updated = 0
    items = data.get("conversations", [])
    for item in items:
        name = item.get("name")
        if not name:
            continue
        days = item.get("spark_days")
        status = item.get("status")
        progress = item.get("reignite_progress", "")
        if find_contact(state, name) is None:
            add_contact(state, name, days or 0, status or "未标注", progress or "")
            added += 1
        else:
            update_contact(
                state, name,
                days=int(days) if days is not None else None,
                status=status if status in STATUS_VALUES else None,
                progress=progress if progress is not None else None,
            )
            updated += 1
    state["snapshots"].append({
        "date": state["last_date"],
        "captured_at": data.get("captured_at", ""),
        "conversations": len(items),
        "added": added,
        "updated": updated,
    })
    return added, updated


def build_digest(state):
    lines = ["# 续火花日报 " + state["last_date"], ""]
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | --- |")
    metrics = [
        ("联系人", len(state["contacts"])),
        ("今日已发", len(state["sent_today"])),
        ("今日待发", len(pending(state))),
        ("今日失败", len(state["failures_today"])),
        ("熔断阈值", state.get("failure_threshold", DEFAULT_FAILURE_THRESHOLD)),
        ("熔断状态", "已触发" if is_tripped(state) else "未触发"),
    ]
    for key, value in metrics:
        lines.append("| " + key + " | " + str(value) + " |")
    lines.append("")
    lines.append("## 联系人明细")
    lines.append("")
    lines.append("| 联系人 | 火花天数 | 状态 | 重燃进度 | 今日 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for c in state["contacts"]:
        flag = "已发" if c["name"] in state["sent_today"] else "待发"
        lines.append("| {} | {} | {} | {} | {} |".format(
            c["name"], c["spark_days"], c["status"], c["reignite_progress"], flag))
    lines.append("")
    lines.append("## 今日消息")
    lines.append("")
    lines.append(state.get("last_text") or "无")
    lines.append("")
    lines.append("## 快照记录")
    lines.append("")
    if state["snapshots"]:
        last = state["snapshots"][-1]
        lines.append("最近一次快照导入 {} 个会话，新增 {}，更新 {}。".format(
            last["conversations"], last["added"], last["updated"]))
    else:
        lines.append("无")
    return "\n".join(lines) + "\n"
