#!/usr/bin/env python3
"""
批量把 content/<zone>/*.md 的 title + summary + deepDive + resources 翻译成中文，
原地写入 <!-- ZH_* --> 块与 front matter 的 title_zh。

- 断点续翻：已含 title_zh 或 <!-- ZH_SUMMARY --> 的跳过（除非 --force）。
- 走本机代理（127.0.0.1:10809）访问 DeepSeek API。
- 用法：
    python translate_content.py                 # 全量（已翻的跳过）
    python translate_content.py --zone foundations   # 只翻某个分区
    python translate_content.py --zone foundations --limit 3  # 试翻前 3 篇
    python translate_content.py --force            # 强制重翻全部
"""
import os
import re
import sys
import time
import argparse
import json
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
API_URL = "https://api.deepseek.com/v1/chat/completions"
PROXY = "http://127.0.0.1:10809"

SYSTEM = (
    "你是专业 SRE/DevOps 技术文档翻译，精通基础设施、可观测性、Kubernetes、网络、数据库、"
    "分布式系统等领域的术语。把英文技术内容准确翻译为简体中文。严格遵守：\n"
    "1) 只翻译自然语言，原样保留所有代码块、命令行、文件路径、技术专有名词"
    "(Kubernetes、ebpf、Cilium、BGP、DNS、TCP、Redis 等可保留英文)、URL 链接、"
    "以及全部 Markdown 语法与标记(#, *, -, >, `, ** 等)。\n"
    "2) 译文通顺专业，符合中文技术文档习惯，不要过度意译导致信息偏差。\n"
    "3) 只输出译文本身，不要任何解释、前言(如'以下是翻译')或后缀。\n"
    "4) 若原文本身是代码/链接/术语，直接保留，不要强行翻译。"
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
    if not text.strip():
        return ""
    payload = json.dumps(
        {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
            "max_tokens": 8192,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    last_err = None
    for attempt in range(3):
        try:
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
            )
            with opener.open(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                out = data["choices"][0]["message"]["content"].strip()
                # 去除可能的 ``` 包裹
                if out.startswith("```") and out.endswith("```"):
                    out = out[out.find("\n") + 1 : -3].strip()
                return out
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"    [retry {attempt + 1}] {e}")
            time.sleep(3)
    print(f"    !! 翻译失败: {last_err}")
    return None


def parse_frontmatter(txt: str):
    if txt.startswith("---"):
        end = txt.find("---", 3)
        if end != -1:
            return txt[3:end].strip(), txt[end + 3 :]
    return "", txt


def get_title(fm: str) -> str:
    m = re.search(r"^title:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else ""


def split_en(body: str):
    d = "<!-- DEEP_DIVE -->"
    r = "<!-- RESOURCES -->"
    di = body.find(d)
    ri = body.find(r)
    if di == -1 and ri == -1:
        return body.strip(), "", ""
    summary = body[: di if di != -1 else ri].strip()
    deepDive = ""
    resources = ""
    if di != -1:
        deepDive = body[di + len(d) : ri if ri != -1 else len(body)].strip()
    if ri != -1:
        resources = body[ri + len(r) :].strip()
    return summary, deepDive, resources


def has_zh(fm: str, body: str) -> bool:
    return ("title_zh" in fm) or ("<!-- ZH_SUMMARY -->" in body)


def yaml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default=None, help="只处理某个分区")
    ap.add_argument("--limit", type=int, default=0, help="最多处理 N 篇(调试用)")
    ap.add_argument("--force", action="store_true", help="忽略已有译文，重翻全部")
    args = ap.parse_args()

    api_key = get_key()
    if not api_key:
        print("未发现 DeepSeek key（环境变量 DEEPSEEK_API_KEY 或 start-backend.bat）")
        sys.exit(1)

    if args.zone:
        zones = [os.path.join(CONTENT_DIR, args.zone)]
    else:
        zones = sorted(
            d for d in (os.path.join(CONTENT_DIR, x) for x in os.listdir(CONTENT_DIR))
            if os.path.isdir(d)
        )

    done = skipped = failed = total = 0
    for zone in zones:
        if not os.path.isdir(zone):
            continue
        if os.path.basename(zone) == "aiops":  # 自研中文分区，跳过不翻译
            continue
        mds = sorted(f for f in os.listdir(zone) if f.endswith(".md"))
        for md in mds:
            total += 1
            if args.limit and done >= args.limit:
                break
            path = os.path.join(zone, md)
            txt = open(path, encoding="utf-8").read()
            fm, body = parse_frontmatter(txt)
            if has_zh(fm, body) and not args.force:
                skipped += 1
                continue
            title = get_title(fm)
            summary, deepDive, resources = split_en(body)
            print(f"▶ {os.path.basename(zone)}/{md}  (title={title[:40]})")
            title_zh = ""
            if title:
                t = call_api(f"翻译以下技术节点标题为简体中文：\n{title}", api_key)
                title_zh = t or ""
            summary_zh = call_api(summary, api_key) if summary else ""
            deepDive_zh = call_api(deepDive, api_key) if deepDive else ""
            resources_zh = call_api(resources, api_key) if resources else ""
            if summary_zh is None or deepDive_zh is None:
                failed += 1
                print("  ! 翻译失败，跳过写入")
                continue
            new_fm = fm
            if title_zh:
                new_fm = fm.rstrip() + f"\ntitle_zh: {yaml_quote(title_zh)}\n"
            zh_block = "\n\n"
            if summary_zh:
                zh_block += f"<!-- ZH_SUMMARY -->\n{summary_zh}\n\n"
            if deepDive_zh:
                zh_block += f"<!-- ZH_DEEP_DIVE -->\n{deepDive_zh}\n\n"
            if resources_zh:
                zh_block += f"<!-- ZH_RESOURCES -->\n{resources_zh}\n"
            new_body = body.rstrip() + zh_block
            new_txt = f"---\n{new_fm}\n---\n{new_body}" if fm else new_body
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_txt)
            done += 1
            time.sleep(0.3)

    print(
        f"\n完成：翻译 {done} 篇，跳过(已有译文) {skipped} 篇，失败 {failed} 篇，总扫描 {total} 篇"
    )


if __name__ == "__main__":
    main()
