#!/usr/bin/env python3
"""
第二轮翻译：把每个文件的 front matter 里用户可见的英文文案翻成中文——
  - milestones（里程碑清单）
  - edges.to[].question / detail（"下一步去哪"问题与详情，图谱上的问句节点也用）
译文以编号列表形式追加到 md 末尾的 <!-- ZH_UI --> 块，content.ts 按顺序取用。

- 断点续翻：已含 <!-- ZH_UI --> 的文件跳过（--force 重翻）。
- 每个文件一次 API 调用（多条合并），走本机代理 127.0.0.1:10809。
- 条数强校验：译文条数 != 原文条数则重试，仍失败则跳过写入。
"""
import os
import re
import sys
import time
import json
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRINGS_JSON = os.path.join(ROOT, "scripts", "ui_strings.json")
API_URL = "https://api.deepseek.com/v1/chat/completions"
PROXY = "http://127.0.0.1:10809"

SYSTEM = (
    "你是专业 SRE/DevOps 技术文档翻译。输入是编号的英文条目（学习里程碑、引导问题、"
    "问题补充说明），请全部翻译为简体中文。严格遵守：\n"
    "1) 输出条数必须与输入完全一致，按相同编号输出，每条一行，格式：`N. 译文`。\n"
    "2) 只翻译自然语言；保留命令、路径、技术专有名词（Linux、Kubernetes、PID 等可留英文）。\n"
    "3) 语气自然、简短（这些是图谱节点上的短句），不要任何解释或前后缀。"
)


def get_key() -> str | None:
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k:
        return k
    bat = os.path.join(ROOT, "start-backend.bat")
    if os.path.exists(bat):
        m = re.search(r"set LLM_API_KEY=(\S+)", open(bat, encoding="utf-8").read())
        if m:
            return m.group(1)
    return None


def call_api(text: str, api_key: str) -> str | None:
    payload = json.dumps(
        {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    last_err = None
    for attempt in range(3):
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
            )
            with opener.open(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"    [retry {attempt + 1}] {e}")
            time.sleep(3)
    print(f"    !! API 失败: {last_err}")
    return None


NUM_RE = re.compile(r"^\s*(\d+)\s*[.、)．:：]\s*(.*)$")


def parse_numbered(reply: str, expected: int) -> list[str] | None:
    items: list[tuple[int, str]] = []
    for line in reply.splitlines():
        m = NUM_RE.match(line)
        if m:
            items.append((int(m.group(1)), m.group(2).strip()))
        elif line.strip() and items:
            # 未编号的续行拼到上一条
            items[-1] = (items[-1][0], (items[-1][1] + " " + line.strip()).strip())
    items.sort(key=lambda x: x[0])
    vals = [t for _, t in items]
    if len(vals) != expected or any(not v for v in vals):
        return None
    return vals


def main() -> None:
    api_key = get_key()
    if not api_key:
        print("未发现 DeepSeek key")
        sys.exit(1)

    entries = json.load(open(STRINGS_JSON, encoding="utf-8"))
    done = skipped_empty = skipped_has = failed = 0
    for ent in entries:
        p = ent["path"]
        items = list(ent.get("milestones", []))
        for e in ent.get("edges", []):
            if e.get("question"):
                items.append(e["question"])
            if e.get("detail"):
                items.append(e["detail"])
        txt = open(p, encoding="utf-8").read()
        if "<!-- ZH_UI -->" in txt:
            skipped_has += 1
            continue
        if not items:
            skipped_empty += 1
            continue

        src = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(items))
        rel = os.path.relpath(p, ROOT)
        print(f"▶ {rel}  ({len(items)} 条)")

        vals = None
        for attempt in range(3):
            reply = call_api(src, api_key)
            if reply is None:
                continue
            vals = parse_numbered(reply, len(items))
            if vals:
                break
            print(f"    [条数不符，重试 {attempt + 1}]")
        if not vals:
            failed += 1
            print("    !! 翻译失败，跳过写入")
            continue

        block = "\n\n<!-- ZH_UI -->\n" + "\n".join(
            f"{i + 1}. {v}" for i, v in enumerate(vals)
        ) + "\n"
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt.rstrip() + block)
        done += 1
        time.sleep(0.3)

    print(f"\n完成：翻译 {done} 个文件，空条目 {skipped_empty}，已有译文 {skipped_has}，失败 {failed}")


if __name__ == "__main__":
    main()
