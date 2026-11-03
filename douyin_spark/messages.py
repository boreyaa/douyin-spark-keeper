HEART = "[比心]"

DEFAULT_TEMPLATES = [HEART]


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
