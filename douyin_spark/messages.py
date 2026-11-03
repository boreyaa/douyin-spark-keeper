DEFAULT_TEMPLATES = [
    "早呀，今天也冒个泡",
    "在忙啥呢",
    "刚刷到一个挺有意思的，等下发你",
    "晚上记得早点休息",
    "今天这天气有点意思",
    "顺手打个卡",
]


def pick_message(state, templates=None):
    pool = list(templates or DEFAULT_TEMPLATES)
    if not pool:
        return ""
    idx = int(state.get("template_index", 0)) % len(pool)
    candidate = pool[idx]
    if len(pool) > 1 and candidate == state.get("last_text", ""):
        idx = (idx + 1) % len(pool)
        candidate = pool[idx]
    state["template_index"] = (idx + 1) % len(pool)
    return candidate
