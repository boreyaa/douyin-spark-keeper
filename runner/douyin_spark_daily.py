"""独立续火花运行器：不依赖宿主应用，自己枚举会话、发比心、记当日账。

用法：
    python runner/douyin_spark_daily.py --config config/runner.json
    python runner/douyin_spark_daily.py --config config/runner.json --headed
    python runner/douyin_spark_daily.py --config config/runner.json --dry-run

退出码：0 正常（含今日已完成）、2 页面加载失败、3 登录态失效。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("缺少 playwright：pip install playwright")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
ITEM = '[class*="conversationConversationItemwrapper"]'
TITLE = '[class*="conversationConversationItemtitle"]'
EDITOR = "div[contenteditable='true']"
SEND_BTN = "svg.messageMsgInputpublishBtn"
CONTENT_BOX = ".messageMessageBoxcontentBox"
CHAT_URL = "https://www.douyin.com/chat?isPopup=1"
TODAY = date.today().isoformat()

SCROLLER_JS = """() => {
    const first = document.querySelector('%s');
    if (!first) return false;
    let p = first.parentElement;
    while (p && p !== document.body) {
        const s = getComputedStyle(p);
        if ((s.overflowY === 'auto' || s.overflowY === 'scroll') && p.scrollHeight > p.clientHeight + 20) {
            p.setAttribute('data-spark-scroller', '1');
            return true;
        }
        p = p.parentElement;
    }
    return false;
}""" % ITEM

COLLECT_JS = """() => {
    const nodes = Array.from(document.querySelectorAll('%s'));
    return nodes.map((el) => {
        const t = el.querySelector('%s');
        const s = el.querySelector('[class*="commonStreaknormalText"]');
        return {
            name: t ? (t.innerText || '').trim().split('\\n')[0].trim() : '',
            streak: s ? (s.innerText || '').trim() : '',
            hasStreak: !!el.querySelector('[class*="commonStreakstreakContainer"]')
        };
    });
}""" % (ITEM, TITLE)

INDEX_JS = """(name) => {
    const nodes = Array.from(document.querySelectorAll('%s'));
    for (let i = 0; i < nodes.length; i++) {
        const t = nodes[i].querySelector('%s');
        const first = t ? (t.innerText || '').trim().split('\\n')[0].trim() : '';
        if (first === name) {
            const r = nodes[i].getBoundingClientRect();
            return {i: i, vis: r.top > 80 && r.bottom < innerHeight - 20};
        }
    }
    return {i: -1, vis: false};
}""" % (ITEM, TITLE)

SIG_JS = """() => {
    const boxes = Array.from(document.querySelectorAll('%s'));
    const last = boxes[boxes.length - 1];
    return {n: boxes.length, tail: last ? last.outerHTML.slice(-200) : ''};
}""" % CONTENT_BOX

PREVIEW_JS = """(a) => {
    const n = document.querySelectorAll(a.sel);
    return n[a.i] ? (n[a.i].innerText || '') : '';
}"""


def expand(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def detect_chrome(config_value: str) -> str:
    if config_value:
        return config_value
    for name in ("chrome", "chrome.exe"):
        from shutil import which

        found = which(name)
        if found:
            return found
    for candidate in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
    ):
        if Path(candidate).exists():
            return candidate
    print("找不到 Chrome，请在 config/runner.json 里填 chrome_path")
    sys.exit(2)


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str) -> None:
        line = datetime.now().strftime("%H:%M:%S") + " " + msg
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def scroll_top(page) -> None:
    page.evaluate("() => { const s = document.querySelector('[data-spark-scroller]'); if (s) s.scrollTop = 0; }")


def enumerate_all(page, log, max_steps: int = 120):
    scroll_top(page)
    page.wait_for_timeout(800)
    seen: dict[str, dict] = {}
    for step in range(max_steps):
        for item in page.evaluate(COLLECT_JS):
            if item["name"] and item["name"] not in seen:
                seen[item["name"]] = item
        page.evaluate("() => { const s = document.querySelector('[data-spark-scroller]'); if (s) s.scrollTop += 340; }")
        page.wait_for_timeout(450)
        if step > 5 and step % 3 == 0:
            at_bottom = page.evaluate(
                """() => {
                    const s = document.querySelector('[data-spark-scroller]');
                    if (!s) return true;
                    const nodes = Array.from(document.querySelectorAll('%s'));
                    if (!nodes.length) return true;
                    return s.scrollTop + s.clientHeight >= s.scrollHeight - 40;
                }""" % ITEM
            )
            if at_bottom:
                again = page.evaluate(COLLECT_JS)
                if all((not b["name"]) or b["name"] in seen for b in again):
                    log("列表到底，共 " + str(len(seen)) + " 个会话")
                    break
    return list(seen.values())


def find_item(page, name: str, max_steps: int = 90) -> int:
    scroll_top(page)
    page.wait_for_timeout(650)
    for _ in range(max_steps):
        res = page.evaluate(INDEX_JS, name)
        if res["i"] >= 0 and res["vis"]:
            return res["i"]
        page.evaluate("() => { const s = document.querySelector('[data-spark-scroller]'); if (s) s.scrollTop += 340; }")
        page.wait_for_timeout(420)
    return -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "runner.json"))
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cfg = load_json(Path(args.config), {})
    data_dir = expand(cfg.get("data_dir") or str(ROOT / "data"))
    profile = expand(cfg.get("profile_dir") or str(data_dir / "profile"))
    heart = str(cfg.get("heart") or "[比心]")
    ledger_path = data_dir / "heart_ledger.json"
    exclude_path = data_dir / "exclude.json"

    log = Logger(data_dir / "logs" / "run.log")
    if not profile.exists():
        log("配置错误：profile_dir 不存在 " + str(profile))
        sys.exit(3)

    ledger = load_json(ledger_path, {})
    done_today = set(ledger.get(TODAY, []))
    blocked = set(load_json(exclude_path, {}).get("exclude", []))
    log("START " + TODAY + " 已发 " + str(len(done_today)) + " 排除 " + str(len(blocked)))

    chrome = detect_chrome(str(cfg.get("chrome_path") or ""))
    headless = bool(cfg.get("headless", True)) and not args.headed

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            executable_path=chrome,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)

        if not ({"sessionid", "sid_tt", "sessionid_ss"} & {c["name"] for c in ctx.cookies()}):
            log("LOGIN_LOST 登录态失效，需要扫码")
            ctx.close()
            sys.exit(3)

        if not page.evaluate(SCROLLER_JS):
            log("PAGE_ERROR 找不到会话列表容器")
            ctx.close()
            sys.exit(2)

        chats = enumerate_all(page, log)
        fire = [c for c in chats if c["hasStreak"] and c["name"]]
        log("会话 " + str(len(chats)) + " 带火花 " + str(len(fire)))
        if not chats:
            ctx.close()
            sys.exit(2)

        only = {x.strip() for x in args.only.split(",") if x.strip()}
        targets = [c for c in fire if c["name"] not in blocked and c["name"] not in done_today]
        if only:
            targets = [c for c in targets if c["name"] in only]
        if args.limit:
            targets = targets[: args.limit]

        if not targets:
            log("NOTHING_TO_DO 今日没有待发会话")
            ctx.close()
            sys.exit(0)

        log("待发 " + str(len(targets)) + " " + json.dumps([t["name"] for t in targets], ensure_ascii=False))
        if args.dry_run:
            ctx.close()
            sys.exit(0)

        results = []
        for target in targets:
            name = target["name"]
            rec = {"name": name, "streak": target["streak"], "ok": False, "error": ""}
            try:
                idx = find_item(page, name)
                if idx < 0:
                    raise RuntimeError("滚动未找到会话")
                page.locator(ITEM).nth(idx).click(timeout=8000)
                page.wait_for_timeout(2500)

                before = page.evaluate(SIG_JS)
                page.locator(EDITOR).last.click(timeout=6000)
                page.wait_for_timeout(250)
                page.keyboard.type(heart, delay=90)
                page.wait_for_timeout(700)
                if heart not in page.locator(EDITOR).last.inner_text():
                    raise RuntimeError("输入框未写入内容")
                page.locator(SEND_BTN).last.click(force=True, timeout=6000)
                page.wait_for_timeout(2800)

                after = page.evaluate(SIG_JS)
                left = page.locator(EDITOR).last.inner_text().replace("\u200b", "").strip()
                changed = after["n"] > before["n"] or after["tail"] != before["tail"]

                scroll_top(page)
                page.wait_for_timeout(700)
                preview = ""
                res = page.evaluate(INDEX_JS, name)
                if res["i"] >= 0:
                    preview = page.evaluate(PREVIEW_JS, {"sel": ITEM, "i": res["i"]})
                preview_hit = heart in preview

                rec["ok"] = bool((changed or preview_hit) and not left)
                if not rec["ok"]:
                    rec["error"] = "未检测到新消息" if not (changed or preview_hit) else "输入框残留"
                else:
                    ledger.setdefault(TODAY, [])
                    if name not in ledger[TODAY]:
                        ledger[TODAY].append(name)
                    save_json(ledger_path, ledger)
                    done_today.add(name)
                log(("SENT " if rec["ok"] else "FAIL ") + name + " " + str(target["streak"]))
            except Exception as exc:  # noqa: BLE001
                rec["error"] = str(exc)[:150]
                log("FAIL " + name + " | " + rec["error"])
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
            results.append(rec)
            save_json(data_dir / "last_run.json", results)
            page.wait_for_timeout(1300)

        log("DONE " + str(sum(1 for r in results if r["ok"])) + " / " + str(len(targets)))
        ctx.close()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print("FATAL " + str(exc)[:300], flush=True)
        sys.exit(2)
