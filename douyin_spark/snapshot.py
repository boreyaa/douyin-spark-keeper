import json
from pathlib import Path

from .state import STATUS_VALUES

SNAPSHOT_VERSION = 1


def example():
    return {
        "version": SNAPSHOT_VERSION,
        "captured_at": "2026-11-03T21:00:00",
        "conversations": [
            {"name": "好友甲", "spark_days": 93, "status": "彩色", "reignite_progress": ""},
            {"name": "好友乙", "spark_days": 2, "status": "重燃中", "reignite_progress": "2/3"},
        ],
    }


def load(path):
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate(data):
    if not isinstance(data, dict):
        return False, "快照顶层必须是对象"
    items = data.get("conversations")
    if not isinstance(items, list):
        return False, "快照缺少 conversations 数组"
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            return False, "会话条目缺少 name"
        status = item.get("status")
        if status and status not in STATUS_VALUES:
            return False, "会话 status 取值不合法：" + str(status)
        if "spark_days" in item:
            try:
                int(item["spark_days"])
            except (TypeError, ValueError):
                return False, "会话 spark_days 不是整数"
    return True, ""


def conversations(data):
    return data.get("conversations", [])
