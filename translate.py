#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
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


def parse_sentence_pairs(text):
    """Parse model response as JSON sentence pairs. Returns list or None."""
    # Try direct parse
    try:
        pairs = json.loads(text)
        if isinstance(pairs, list) and pairs and "src" in pairs[0] and "tgt" in pairs[0]:
            return pairs
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    # Try extracting JSON array from surrounding text
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            pairs = json.loads(m.group())
            if isinstance(pairs, list) and pairs and "src" in pairs[0] and "tgt" in pairs[0]:
                return pairs
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
    return None


def generate_preview_html(pairs, direction, original=None, translation=None):
    if direction == "en":
        left_label, right_label = "中文原文", "English Translation"
    else:
        left_label, right_label = "English Original", "中文译文"

    if pairs:
        left_parts = []
        right_parts = []
        for i, p in enumerate(pairs):
            left_parts.append(f'<span class="s" data-i="{i}">{html.escape(p["src"])}</span>')
            right_parts.append(f'<span class="s" data-i="{i}">{html.escape(p["tgt"])}</span>')
        left_html = " ".join(left_parts)
        right_html = " ".join(right_parts)
    else:
        left_html = html.escape(original or "")
        right_html = html.escape(translation or "")

    highlight_css = ""
    highlight_js = ""
    if pairs:
        highlight_css = (
            "  .s { cursor: pointer; border-radius: 3px; padding: 1px 0; transition: background 0.15s; }\n"
            "  .s.active { background: rgba(255, 196, 0, 0.3); }\n"
        )
        highlight_js = """
<script>
(function() {
  function clearAll() {
    document.querySelectorAll('.s.active').forEach(function(el) { el.classList.remove('active'); });
  }
  document.querySelectorAll('.s').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.stopPropagation();
      clearAll();
      var idx = this.dataset.i;
      document.querySelectorAll('.s[data-i="' + idx + '"]').forEach(function(s) { s.classList.add('active'); });
    });
  });
  document.addEventListener('click', clearAll);
})();
</script>"""

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
    .s.active {{ background: rgba(255, 196, 0, 0.2); }}
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
{highlight_css}</style>
</head>
<body>
<div class="container">
  <div class="panel" id="left">
    <div class="label">{left_label}</div>
    <div class="text">{left_html}</div>
  </div>
  <div class="panel" id="right">
    <div class="label">{right_label}</div>
    <div class="text">{right_html}</div>
  </div>
</div>
{highlight_js}
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
        prompt = (
            "Translate the following Chinese text into English.\n"
            "Split the text into individual sentences. Return a JSON array where each element is one sentence pair: {\"src\": \"original sentence\", \"tgt\": \"translated sentence\"}.\n"
            "Each sentence must be a SEPARATE element. Output ONLY valid JSON, no markdown fences, no explanations.\n"
            'Example input: "你好世界。今天天气不错。"\n'
            'Example output: [{"src": "你好世界。", "tgt": "Hello world."}, {"src": "今天天气不错。", "tgt": "The weather is nice today."}]'
        )
    else:
        prompt = (
            "Translate the following English text into Chinese.\n"
            "Split the text into individual sentences. Return a JSON array where each element is one sentence pair: {\"src\": \"original sentence\", \"tgt\": \"translated sentence\"}.\n"
            "Each sentence must be a SEPARATE element. Output ONLY valid JSON, no markdown fences, no explanations.\n"
            'Example input: "Hello world. Nice weather today."\n'
            'Example output: [{"src": "Hello world.", "tgt": "你好世界。"}, {"src": "Nice weather today.", "tgt": "今天天气不错。"}]'
        )

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

    content = result["message"]["content"].strip()
    logging.debug("model response: %s", content)
    return content


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
        pairs = parse_sentence_pairs(result)
        if pairs:
            translation = " ".join(p["tgt"] for p in pairs)
            preview = generate_preview_html(pairs, direction)
        else:
            translation = result
            preview = generate_preview_html(None, direction, query, translation)
        subtitle = "中→英" if direction == "en" else "英→中"
        alfred_output(translation, subtitle=f"{subtitle} | Shift 查看对照",
                      arg=translation, quicklookurl=preview)
    except urllib.error.URLError:
        alfred_output("无法连接 Ollama", subtitle="请确保 Ollama 正在运行", valid=False)
    except TimeoutError:
        alfred_output("翻译超时", subtitle="请稍后重试", valid=False)
    except Exception as e:
        alfred_output(f"错误: {e}", subtitle="翻译失败", valid=False)


if __name__ == "__main__":
    main()
