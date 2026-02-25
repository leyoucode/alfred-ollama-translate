#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import os
import logging
import html
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2:7b"

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")


def generate_preview_html(original, translation, direction):
    if direction == "en":
        left_label, right_label = "中文原文", "English Translation"
    else:
        left_label, right_label = "English Original", "中文译文"

    safe_original = html.escape(original)
    safe_translation = html.escape(translation)

    content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    margin: 0; padding: 20px;
    background: #fff; color: #222;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1e1e1e; color: #ddd; }}
    .panel {{ background: #2a2a2a; border-color: #444; }}
  }}
  .container {{ display: flex; gap: 20px; }}
  .panel {{
    flex: 1; padding: 16px; border: 1px solid #ddd;
    border-radius: 8px; background: #f9f9f9;
  }}
  .label {{
    font-size: 12px; font-weight: 600; color: #888;
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .text {{ font-size: 16px; line-height: 1.6; white-space: pre-wrap; }}
</style>
</head>
<body>
<div class="container">
  <div class="panel">
    <div class="label">{left_label}</div>
    <div class="text">{safe_original}</div>
  </div>
  <div class="panel">
    <div class="label">{right_label}</div>
    <div class="text">{safe_translation}</div>
  </div>
</div>
</body>
</html>"""

    path = "/tmp/alfred_ollama_translate.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def alfred_output(title, subtitle="", arg="", valid=True, quicklookurl=None):
    item = {"title": title, "subtitle": subtitle, "arg": arg, "valid": valid}
    if quicklookurl:
        item["quicklookurl"] = quicklookurl
    if arg:
        item["text"] = {"largetype": arg}
    print(json.dumps({"items": [item]}))


def translate(text, direction):
    if direction == "en":
        prompt = "You are a translator. Translate the following Chinese text into English. Output ONLY the translation, no explanations or extra text."
    else:
        prompt = "You are a translator. Translate the following English text into Chinese. Output ONLY the translation, no explanations or extra text."

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return result["message"]["content"].strip()


def main():
    logging.debug("argv: %s", sys.argv)

    # First argument: direction (en = translate to English, cn = translate to Chinese)
    direction = sys.argv[1] if len(sys.argv) > 1 else "en"

    # Read query: from remaining args (CLI testing) or stdin (Alfred scriptargtype=1)
    if len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
    elif not sys.stdin.isatty():
        query = sys.stdin.read().strip()
    else:
        query = ""

    logging.debug("direction: %s, query: %s", direction, query)

    if not query:
        alfred_output("输入要翻译的文字", subtitle="中英互译 (Ollama)", valid=False)
        return

    try:
        result = translate(query, direction)
        subtitle = "中→英" if direction == "en" else "英→中"
        preview = generate_preview_html(query, result, direction)
        alfred_output(result, subtitle=f"{subtitle} | Shift 查看对照",
                      arg=result, quicklookurl=preview)
    except urllib.error.URLError:
        alfred_output("无法连接 Ollama", subtitle="请确保 Ollama 正在运行", valid=False)
    except TimeoutError:
        alfred_output("翻译超时", subtitle="请稍后重试", valid=False)
    except Exception as e:
        alfred_output(f"错误: {e}", subtitle="翻译失败", valid=False)


if __name__ == "__main__":
    main()
